"""File transfers with callers: ZMODEM (zmodem.py) and YMODEM-G (lib/ymodem).

A transfer turns the caller's connection into a binary channel for a while:

* The connection's text encoding is switched to Latin-1 (one byte per
  character, so every byte value passes unchanged) and back afterwards.
* The user's write lock is held throughout, and user.in_transfer is set, so
  nothing else (the ambient stars) writes into the stream.
* Reads bypass the idle monitor's warning popup (the protocols have their own
  timeouts), though they still count as activity.
* What the caller's side still sends after the transfer ends (the rest of an
  interrupted one) is read and dropped, so it does not reach menus as keys.
* The screen is saved before and redrawn after (push_screen/pop_screen), since
  the terminal showed a transfer dialog or protocol bytes meanwhile.

Five Ctrl+X (CAN) from the caller cancel a ZMODEM transfer either way, and a
YMODEM-G download (a YMODEM upload's data is not escaped, so CANs there are
data; the caller's terminal cancels it).

Uploads are received under temporary names and published into the library
only when whole, under a sanitised name that never replaces an existing file
(see UploadPolicy).
"""

import asyncio
import contextlib
import os
import re
import shutil
import sys
import tempfile
import threading
from dataclasses import dataclass, field

import zmodem
from definitions import RetVals, success, fail, null
from logger import log

_lib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
if _lib_dir not in sys.path:
  sys.path.insert(0, _lib_dir)

try:
  from ymodem.Socket import ModemSocket
  from ymodem.Protocol import ProtocolType
  _have_ymodem = True
except ImportError:
  _have_ymodem = False
  log.warning("YMODEM-G is unavailable: lib/ymodem could not be imported (is ordered-set installed?)")

CAN = 0x18
CANS_TO_ABORT = 5
TEMP_PREFIX = ".upload-"  # (uploads in progress; never listed: see safe_upload_name)
ROOM_CHECK = 1024 * 1024  # bytes an upload writes between checks of the free disk space
MAX_UPLOAD_FILES = 20     # files taken in one upload
READ_SIZE = 1 << 20       # what a transfer reads at a time: more than telnetlib3 ever buffers, which
                          # it then hands back whole (for less, it decodes byte by byte)


def get_available_protocols():
  """Protocol name -> whether this BBS can run it."""
  return {'zmodem': True, 'ymodem': _have_ymodem}


# ---------------------------------------------------------------------------
# The connection as a byte link
# ---------------------------------------------------------------------------

class _ConnectionLink:
  """zmodem.Link over the caller's connection, while it is in binary mode
  (see _binary_session): text read and written is Latin-1, one character per
  byte."""

  def __init__(self, user):
    reader = user.reader
    self._read = getattr(reader, "read_raw", reader.read)  # (bypass the idle monitor)
    self._writer = user.writer

  async def read(self):
    data = await self._read(READ_SIZE)
    if isinstance(data, str):
      data = data.encode("latin-1")
    return data

  def write(self, data):
    self._writer.write(bytes(data).decode("latin-1"))

  async def drain(self):
    await self._writer.drain()


def _eight_bit_clean(user):
  """False when the telnet session never agreed to BINARY both ways: then the
  ZMODEM side escapes every control character (and asks the caller's side to)."""
  writer = user.writer
  outbinary = getattr(writer, "outbinary", True)
  inbinary = getattr(writer, "inbinary", True)
  return bool(outbinary) and bool(inbinary)


@contextlib.asynccontextmanager
async def _binary_session(user):
  """The connection as a byte link for the duration of a transfer (see the
  module docstring); the screen is restored afterwards by the caller."""
  from common import _set_connection_encoding
  async with user.write_lock:
    user.in_transfer = True
    _set_connection_encoding(user, "latin-1")
    link = _ConnectionLink(user)
    try:
      yield link
    finally:
      try:
        await _settle(link)
      finally:
        _set_connection_encoding(user)
        user.in_transfer = False
        touch = getattr(user.reader, "touch", None)  # (the idle monitor's clock)
        if touch is not None:
          touch()


async def _settle(link, quiet=1.0, limit=10.0):
  """Read and drop input until *quiet* seconds pass without any (at most
  *limit* seconds): the rest of an interrupted transfer."""
  loop = asyncio.get_running_loop()
  end = loop.time() + limit
  while loop.time() < end:
    try:
      data = await asyncio.wait_for(link.read(), min(quiet, end - loop.time()))
    except asyncio.TimeoutError:
      return
    except Exception:
      return
    if not data:
      return


async def _with_screen(user, text, work):
  """Save the screen, show *text* (what to do, how to cancel), run *work()*
  on the binary link, then reset the terminal's modes and redraw the screen."""
  from input_output import push_screen, pop_screen, ansi_cls, ansi_reset_modes, send
  await push_screen(user)
  try:
    await ansi_cls(user)
    await send(user, text.replace("\n", "\r\n") + "\r\n", drain=True)
    async with _binary_session(user) as link:
      return await work(link)
  finally:
    # A terminal without ZMODEM support showed the protocol as text, which can
    # set any mode: put them all back before the screen is redrawn.
    await ansi_reset_modes(user)
    await pop_screen(user)


def _settings(user):
  settings = zmodem.Settings(escape_ctrl=not _eight_bit_clean(user))
  drain_every = getattr(user.writer, "drain_every", None)  # (a slow link's, a modem's)
  if drain_every:
    settings.drain_every = drain_every
  return settings


# ---------------------------------------------------------------------------
# Upload policy: names, limits, publishing
# ---------------------------------------------------------------------------

_DEVICE_NAMES = ({"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
                 | {f"COM{i}" for i in range(10)} | {f"LPT{i}" for i in range(10)})
_BAD_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
MAX_NAME = 120


def safe_upload_name(name):
  """The name an uploaded file may have in the library, from the name the
  caller's terminal sent: its last path component, without characters
  Windows forbids or control characters, without leading dots (no hidden
  files, and never one of our temporary names) or trailing dots and spaces
  (Windows drops them), not a device name (CON, NUL, COM1 ...), and at most
  MAX_NAME characters (keeping the extension). None when nothing usable is left."""
  base = name.replace("\\", "/").rsplit("/", 1)[-1]
  base = base.rsplit(":", 1)[-1]  # a drive letter, or an NTFS stream
  base = _BAD_CHARS.sub("_", base)
  if len(base) > MAX_NAME:
    stem, dot, ext = base.rpartition(".")
    if dot and 0 < len(ext) <= 16:
      base = stem[:MAX_NAME - len(ext) - 1] + "." + ext
    else:
      base = base[:MAX_NAME]
  # (after cutting: what was cut can have left dots or spaces at either end)
  base = base.lstrip(". ").rstrip(". ")
  if not base:
    return None
  if base.split(".")[0].strip().upper() in _DEVICE_NAMES:
    base = "_" + base
  return base


_SIZE = re.compile(r"\s*(\d+(?:\.\d+)?)\s*([KMGT]?)I?B?\s*", re.IGNORECASE)


def parse_size(value, default):
  """A size from the config: a number of bytes, or text such as "100 MB"
  (B, KB, MB, GB, TB; powers of 1024). *default* when absent or unreadable."""
  if value is None or value is null or (isinstance(value, str) and not value.strip()):
    return default  # (absent; but 0 is 0: keep no reserve, say)
  if isinstance(value, (int, float)):
    return int(value)
  m = _SIZE.fullmatch(str(value))
  if not m:
    log.warning("Unreadable size %r in the config; using %d bytes", value, default)
    return default
  return int(float(m.group(1)) * 1024 ** " KMGT".index(m.group(2).upper() or " "))


def _size_text(n):
  for unit in ("bytes", "KB", "MB", "GB", "TB"):
    if n < 1024 or unit == "TB":
      return f"{n} {unit}" if unit == "bytes" else f"{n:.1f} {unit}"
    n /= 1024


@dataclass
class UploadPolicy:
  """Where uploads go and what is allowed.

  directory: the library folder. reserved: names (any case) that may not be
  taken (the catalogue, meta.yaml). max_bytes: the largest file accepted.
  keep_free: bytes the disk must keep free after a file is stored.
  """
  directory: str
  reserved: frozenset = frozenset()
  max_bytes: int = 100 * 1024 * 1024
  keep_free: int = 500 * 1024 * 1024
  saved: list = field(default_factory=list)      # names published this session
  refused: list = field(default_factory=list)    # (name as sent, why)

  def check(self, sent_name, size):
    """The library name for an offered file, or None (and why, in
    self.refused) when it may not be taken."""
    name = safe_upload_name(sent_name)
    if name is None:
      self.refused.append((sent_name, "its name has nothing usable in it"))
      return None
    if name.lower() in self.reserved:
      self.refused.append((sent_name, "that name is reserved"))
      return None
    if os.path.exists(os.path.join(self.directory, name)) or name in self.saved:
      self.refused.append((sent_name, "a file with that name is already in the library"))
      return None
    if size is not None and size > self.max_bytes:
      self.refused.append((sent_name, f"it is larger than the {_size_text(self.max_bytes)} allowed"))
      return None
    if size is not None:
      free = shutil.disk_usage(self.directory).free
      if free - size < self.keep_free:
        self.refused.append((sent_name, "there is not enough room for it"))
        return None
    return name

  def out_of_room(self):
    """True when the disk has less free than keep_free. Checked while files
    arrive too (every ROOM_CHECK bytes): the size a sender declares may be
    false, and a batch of files adds up."""
    return shutil.disk_usage(self.directory).free < self.keep_free

  def publish(self, temp_path, name):
    """Move a whole upload from *temp_path* into the library as *name*,
    never replacing a file. True on success."""
    final = os.path.join(self.directory, name)
    try:
      os.link(temp_path, final)  # fails if *final* exists, on every system
    except FileExistsError:
      self.refused.append((name, "a file with that name arrived meanwhile"))
      os.remove(temp_path)
      return False
    except OSError:
      if os.path.exists(final):  # (a file system without hard links)
        self.refused.append((name, "a file with that name arrived meanwhile"))
        os.remove(temp_path)
        return False
      os.rename(temp_path, final)
    else:
      os.remove(temp_path)
    self.saved.append(name)
    return True


class _UploadSink:
  """zmodem.Sink: an upload written to a temporary file in the library
  folder, published when whole (see UploadPolicy), else deleted."""

  def __init__(self, policy, name):
    self.policy, self.name = policy, name
    fd, self.temp = tempfile.mkstemp(prefix=TEMP_PREFIX, suffix=".part", dir=policy.directory)
    self.file = os.fdopen(fd, "wb")
    self.size = 0
    self.checked = 0  # size at the last free-space check

  def write(self, data):
    self.size += len(data)
    if self.size > self.policy.max_bytes:
      self.policy.refused.append((self.name, f"it is larger than the {_size_text(self.policy.max_bytes)} allowed"))
      raise zmodem.TransferError(f"{self.name} is larger than the {_size_text(self.policy.max_bytes)} allowed")
    if self.size - self.checked >= ROOM_CHECK:
      self.checked = self.size
      if self.policy.out_of_room():
        self.policy.refused.append((self.name, "there is not enough room for it"))
        raise zmodem.TransferError("there is not enough room for the upload")
    self.file.write(data)

  def finish(self):
    self.file.close()
    self.policy.publish(self.temp, self.name)

  def discard(self):
    self.file.close()
    with contextlib.suppress(OSError):
      os.remove(self.temp)


def remove_stale_uploads(directory):
  """Delete temporary upload files left by a crash (call at startup)."""
  with contextlib.suppress(OSError):
    for entry in os.scandir(directory):
      if entry.name.startswith(TEMP_PREFIX):
        if entry.is_dir():
          shutil.rmtree(entry.path, ignore_errors=True)
        else:
          with contextlib.suppress(OSError):
            os.remove(entry.path)


# ---------------------------------------------------------------------------
# What callers see
# ---------------------------------------------------------------------------

_HOW_TO_CANCEL = "Press Ctrl+X five times to cancel."


def _upload_text(protocol):
  name = protocol.upper().replace("YMODEM", "YMODEM-G")
  return (f"Ready to receive by {name}.\n"
          f"Start the upload in your terminal (in the web terminal: choose the files).\n"
          f"{_HOW_TO_CANCEL}")


def _download_text(protocol, names):
  name = protocol.upper().replace("YMODEM", "YMODEM-G")
  what = names[0] if len(names) == 1 else f"{len(names)} files"
  return (f"Sending {what} by {name}.\n"
          f"Your terminal should start receiving by itself; if it does not, start a {name} download in it.\n"
          f"{_HOW_TO_CANCEL}")


def _failure(exc):
  if isinstance(exc, OSError):
    return f"The transfer failed: {exc.strerror or exc}."
  if isinstance(exc, zmodem.Aborted):
    text = str(exc)
    return text if text.endswith(".") else "The transfer was cancelled."
  if isinstance(exc, zmodem.TimedOut):
    return f"The transfer stopped: {exc}."
  return f"The transfer failed: {exc}."


# ---------------------------------------------------------------------------
# ZMODEM
# ---------------------------------------------------------------------------

async def send_files_zmodem(user, paths):
  """Send *paths* to the caller by ZMODEM. RetVals: status, message, and
  results (zmodem.FileResult per file)."""
  names = [os.path.basename(p) for p in paths]
  log.info("ZMODEM send of %s to %s", names, getattr(user, 'handle', '?'))

  async def work(link):
    return await zmodem.send_files(link, paths, _settings(user))
  try:
    results = await _with_screen(user, _download_text("zmodem", names), work)
  except (zmodem.TransferError, OSError) as exc:  # (OSError: a file gone, a full disk, a reset)
    log.info("ZMODEM send to %s ended: %s", getattr(user, 'handle', '?'), exc)
    return RetVals(status=fail, message=_failure(exc), results=[])
  sent = [r for r in results if r.status == "sent"]
  log.info("ZMODEM send to %s: %s", getattr(user, 'handle', '?'),
           ", ".join(f"{r.name} {r.status} ({r.bytes} bytes)" for r in results))
  if len(sent) == len(results):
    return RetVals(status=success, message="Transfer complete.", results=results)
  return RetVals(status=fail, message="Your terminal declined the file.", results=results)


async def receive_files_zmodem(user, policy, max_files=MAX_UPLOAD_FILES):
  """Receive files from the caller by ZMODEM into the library, as *policy*
  allows. RetVals: status, message; policy.saved and policy.refused say
  what came of each file."""
  log.info("ZMODEM receive from %s into %s", getattr(user, 'handle', '?'), policy.directory)

  def accept(offer):
    name = policy.check(offer.name, offer.size)
    return _UploadSink(policy, name) if name else None

  async def work(link):
    return await zmodem.receive_files(link, accept, _settings(user), max_files=max_files)
  try:
    await _with_screen(user, _upload_text("zmodem"), work)
  except (zmodem.TransferError, OSError) as exc:  # (OSError: a file gone, a full disk, a reset)
    log.info("ZMODEM receive from %s ended: %s", getattr(user, 'handle', '?'), exc)
    return RetVals(status=fail, message=_failure(exc))
  log.info("ZMODEM receive from %s: saved %s, refused %s", getattr(user, 'handle', '?'),
           policy.saved, policy.refused)
  return RetVals(status=success, message="Transfer complete.")


# ---------------------------------------------------------------------------
# YMODEM-G (lib/ymodem: synchronous, so it runs in a thread)
# ---------------------------------------------------------------------------

class _Cancelled(BaseException):
  """Stops lib/ymodem from inside its read/write callbacks. A BaseException
  because the library catches Exception from them and carries on (retrying
  for up to a minute)."""


class _ThreadedLink:
  """The byte link for lib/ymodem, which runs in a worker thread and wants
  read(size, timeout) -> exactly *size* bytes (fewer on timeout, None for
  none) and write(data) -> count.

  A pump task reads the connection all along into a buffer. While we send,
  it counts consecutive CANs: five cancel the transfer (the next read or
  write raises), even while the library is only sending. Not while we
  receive: YMODEM's data is not escaped, so CANs in a file are data (the
  library itself takes a CAN where a packet should start as a cancel)."""

  def __init__(self, link, loop, watch_cancel):
    self.link, self.loop = link, loop
    self.watch_cancel = watch_cancel
    self.buf = bytearray()
    self.cond = threading.Condition()
    self.cans = 0
    self.cancelled = False
    self.reason = "The transfer was cancelled."
    self.closed = False
    self.pump = None

  def cancel(self, reason):
    """Stop the library at its next read or write (from any thread)."""
    self.reason = reason
    self.cancelled = True

  async def start(self):
    self.pump = asyncio.ensure_future(self._pump())

  async def stop(self):
    """Stop the pump, and the library's thread at its next read or write (it
    still runs if the task awaiting it was cancelled)."""
    with self.cond:
      self.cancelled = True
      self.cond.notify_all()
    if self.pump:
      self.pump.cancel()
      with contextlib.suppress(BaseException):
        await self.pump

  async def _pump(self):
    try:
      while True:
        data = await self.link.read()
        with self.cond:
          if not data:
            self.closed = True
          if self.watch_cancel:
            for b in data:
              self.cans = self.cans + 1 if b == CAN else 0
              if self.cans >= CANS_TO_ABORT and not self.cancelled:
                self.cancel("The transfer was cancelled.")
          self.buf += data
          self.cond.notify_all()
        if not data:
          return
    except asyncio.CancelledError:
      raise
    except Exception:
      with self.cond:
        self.closed = True
        self.cond.notify_all()

  # -- called from the worker thread --

  def read(self, size, timeout=1):
    with self.cond:
      self.cond.wait_for(lambda: len(self.buf) >= size or self.cancelled or self.closed, timeout)
      if self.cancelled:
        raise _Cancelled()
      data = bytes(self.buf[:size])
      del self.buf[:size]
      if not data and self.closed:
        # (else the library polls a dead connection, at full speed, until its timeouts end)
        self.cancel("The connection closed.")
        raise _Cancelled()
    return data or None

  def write(self, data, timeout=1):
    if self.cancelled or self.closed:
      raise _Cancelled()
    data = bytes(data)

    async def put():
      self.link.write(data)
      await self.link.drain()
    asyncio.run_coroutine_threadsafe(put(), self.loop).result(max(timeout, 30))
    return len(data)


async def _run_ymodem(user, text, job, sending):
  """Run *job(modem, threaded_link)* (blocking, in a thread) on the binary
  link. Returns its result; raises zmodem.Aborted when the caller cancels."""
  loop = asyncio.get_running_loop()

  async def work(link):
    threaded = _ThreadedLink(link, loop, watch_cancel=sending)
    await threaded.start()
    try:
      modem = ModemSocket(threaded.read, threaded.write, protocol_type=ProtocolType.YMODEM,
                          protocol_type_options=['g'])
      try:
        result = await asyncio.to_thread(job, modem, threaded)
      except _Cancelled:
        result = None
      if threaded.cancelled:
        await zmodem.cancel(link)
        raise zmodem.Aborted(threaded.reason)
      return result
    finally:
      await threaded.stop()
  return await _with_screen(user, text, work)


async def send_files_ymodem(user, paths):
  """Send *paths* to the caller by YMODEM-G. RetVals like send_files_zmodem's."""
  if not _have_ymodem:
    return RetVals(status=fail, message="YMODEM-G is not available on this system.", results=[])
  names = [os.path.basename(p) for p in paths]
  log.info("YMODEM-G send of %s to %s", names, getattr(user, 'handle', '?'))

  def job(modem, threaded):
    return modem.send(list(paths))
  try:
    ok = await _run_ymodem(user, _download_text("ymodem", names), job, sending=True)
  except zmodem.TransferError as exc:
    return RetVals(status=fail, message=_failure(exc), results=[])
  except Exception as exc:
    log.error("YMODEM-G send error: %s", exc, exc_info=True)
    return RetVals(status=fail, message=f"The transfer failed: {exc}.", results=[])
  if ok:
    return RetVals(status=success, message="Transfer complete.", results=[])
  return RetVals(status=fail, message="The transfer failed.", results=[])


async def receive_files_ymodem(user, policy, max_files=MAX_UPLOAD_FILES):
  """Receive files by YMODEM-G into the library, as *policy* allows. The
  library writes into a fresh hidden folder; each whole file is then checked
  and published like a ZMODEM upload."""
  if not _have_ymodem:
    return RetVals(status=fail, message="YMODEM-G is not available on this system.")
  staging = tempfile.mkdtemp(prefix=TEMP_PREFIX, dir=policy.directory)
  log.info("YMODEM-G receive from %s into %s", getattr(user, 'handle', '?'), staging)

  checked = {}  # file -> bytes at its last free-space check
  names = {}    # file number -> the name the caller's terminal gave it

  def job(modem, threaded):
    def progress(task_index, name, total, received):
      if threaded.cancelled:
        return
      if task_index >= max_files:
        threaded.cancel(f"No more than {max_files} files can be uploaded at a time.")
      elif received > policy.max_bytes:
        threaded.cancel(f"{name} is larger than the {_size_text(policy.max_bytes)} allowed.")
      elif received - checked.get(task_index, 0) >= ROOM_CHECK:
        checked[task_index] = received
        if policy.out_of_room():
          threaded.cancel("There is not enough room for the upload.")
    try:
      return modem.recv(staging, callback=progress)
    finally:
      names.update(getattr(modem, "received_names", {}))
  try:
    try:
      ok = await _run_ymodem(user, _upload_text("ymodem"), job, sending=False)
    except zmodem.TransferError as exc:
      return RetVals(status=fail, message=_failure(exc))
    except Exception as exc:
      log.error("YMODEM-G receive error: %s", exc, exc_info=True)
      return RetVals(status=fail, message=f"The transfer failed: {exc}.")
    if not ok:
      return RetVals(status=fail, message="The transfer failed.")
    # The library saves file<number>: the caller's names go only through the policy
    for number in sorted(names)[:max_files]:
      path = os.path.join(staging, f"file{number}")
      if not os.path.isfile(path):
        continue
      name = policy.check(names[number], os.path.getsize(path))
      if name is not None:
        policy.publish(path, name)
    return RetVals(status=success, message="Transfer complete.")
  finally:
    shutil.rmtree(staging, ignore_errors=True)
