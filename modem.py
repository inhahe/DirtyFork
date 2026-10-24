"""
Modem connections: callers dialling in to a Hayes-compatible modem on a
serial port (pyserial-asyncio).

listen() answers the calls on one port, one at a time. wait_for_call() sets
the modem up, waits for RING and answers; once connected, the session gets a
SerialReader and a SerialWriter, which stand in for telnetlib3's reader and
writer. When the session ends, the writer hangs up, and the port is opened
again for the next call.

The caller's hang-up shows in the carrier (DCD): once it drops, the reader
reads as closed, and what the modem says then ("NO CARRIER") is not taken
for the caller's keys. Hanging up drops DTR, falling back to the +++ escape
and ATH.

What the BBS needs of the modem is set after the sysop's init string
(SETUP): no echo (E0), results in words (V1, Q0), no auto-answer (S0=0: the
BBS answers on RING), DCD following the carrier (&C1), and a hang-up when DTR
drops (&D2). Flow control is RTS/CTS, which the port uses; the modem's side
of it is its factory default on most modems, or the init string's job.

Output queued between the BBS and the modem is kept to about a second of
the line's speed (from the CARRIER or CONNECT message): the transport's own
limit, 64 KiB, is minutes at modem speeds, which a file transfer's repair
or a caller's cancel would wait through.
"""

import asyncio
import codecs
import re

import serial_asyncio

from logger import log

# What the BBS needs of the modem, a command each (a modem that does not know
# a setting answers its whole line with ERROR, and many then apply none of
# it); results in words first, so that the answers to the rest are words.
SETUP = ("ATE0V1Q0", "ATS0=0", "AT&C1", "AT&D2")
COMMAND_TIMEOUT = 5.0   # seconds a setup command may take to answer (ATZ resets the modem)
ANSWER_TIMEOUT = 60.0   # seconds from ATA to CONNECT (modems give up after S7, 50 s by default)
ANALOG_TOP = 33600      # bps: the fastest line an answering modem has (V.90's 56k needs a digital line here)
CARRIER_POLL = 0.5      # seconds between looks at DCD during a call
DRAIN_POLL = 0.02       # seconds between looks at the output queue while draining
FLUSH_LIMIT = 10.0      # seconds a hang-up waits for output still to leave
DTR_DROP = 1.0          # seconds DTR is held low to hang up
HANGUP_WAIT = 3.0       # seconds more a modem may take to drop the carrier after that
GUARD_TIME = 1.1        # seconds of silence around the +++ escape (S12: 1 s by default)
RETRY = 10.0            # seconds between attempts on a port that failed
SETTLE = 1.0            # seconds after a hang-up before the modem is set up again

_FINAL = {"OK": "OK", "0": "OK", "ERROR": "ERROR", "4": "ERROR"}  # (in words, or V0's digits)
_ANSWER_FAILED = {"NO CARRIER", "ERROR", "NO ANSWER", "BUSY", "NO DIALTONE", "NO DIAL TONE"}


class ModemGone(Exception):
  """The serial port closed or failed (a USB modem unplugged, say)."""


class _Carrier:
  """Whether the caller is still there, by the modem's carrier detect (DCD).

  Only a drop after it has been seen up counts: a modem whose DCD is not
  wired, or not set to follow the carrier, would otherwise end every call
  at once. (seen stays False then, and hang-ups go unnoticed.)"""

  def __init__(self, serial):
    self._serial = serial
    self.seen = False
    self.lost = False
    self.port_failed = False  # (lost because the port failed, not the carrier)

  def check(self):
    """True while the caller is there (or the line cannot tell)."""
    if not self.lost:
      try:
        up = self._serial.cd
      except Exception:  # (the port is gone)
        self.lost = self.port_failed = True
        return False
      if up:
        self.seen = True
      elif self.seen:
        self.lost = True
    return not self.lost


class SerialReader:
  """The caller's input, as telnetlib3's reader gives it: text in the
  connection's encoding (set_encoding), "" once the caller has gone."""

  def __init__(self, stream_reader, carrier=None, encoding="cp437"):
    self._reader = stream_reader
    self._carrier = carrier
    self.set_encoding(encoding)

  def set_encoding(self, encoding):
    """Text encoding from now on (common._set_connection_encoding)."""
    self._decoder = codecs.getincrementaldecoder(encoding)(errors="replace")

  async def read(self, n=1):
    # A cancellation (a timed-out read) must propagate: returned as "", it
    # would look like the caller hanging up.
    while True:
      try:
        data = await self._reader.read(n)
      except Exception:  # (the port failed: as good as a hang-up)
        return ""
      if not data or (self._carrier is not None and not self._carrier.check()):
        return ""  # (after the carrier has gone, what comes is the modem's, not the caller's)
      text = self._decoder.decode(data)
      if text:  # (else only part of a character so far)
        return text


class SerialWriter:
  """The caller's output, as telnetlib3's writer takes it (text in the
  connection's encoding, or bytes), and the end of the call: close() hangs
  up, and wait_closed() waits until the modem is back on hook.

  transfer_block: the bytes a file transfer should send at a time, and
  between drains (file_transfer asks): what is queued beyond drain()'s
  second holds up a repair or a cancel, so less on a slower line (as lrzsz's
  sz: 256 below 4800 bps, 512 below 9600, else 1024)."""

  def __init__(self, stream_writer, port="serial", carrier=None, carrier_watch=None,
               encoding="cp437", line_speed=115200):
    # (kept, though all goes through its transport: asyncio closes the
    # transport when the StreamWriter is collected)
    self._stream_writer = stream_writer
    self._transport = stream_writer.transport
    self._port = port
    self._carrier = carrier
    self._carrier_watch = carrier_watch  # (a task, stopped at the hang-up)
    self._encoding = encoding
    self._closed = False
    self._hangup = None
    self.set_line_speed(line_speed)

  def set_encoding(self, encoding):
    """Text encoding from now on (common._set_connection_encoding)."""
    self._encoding = encoding

  def set_line_speed(self, bps):
    """For a line of *bps* bits a second: drain() leaves about a second of
    output queued, and transfers send transfer_block bytes at a time."""
    self._queue_limit = max(256, bps // 10)
    self.transfer_block = 256 if bps < 4800 else 512 if bps < 9600 else 1024

  def write(self, data):
    if self._closed:
      return
    if isinstance(data, str):
      data = data.encode(self._encoding, errors="replace")
    self._transport.write(data)

  async def drain(self):
    """Wait until no more than about a second of output is still queued, in
    the transport and in the port (which takes any amount at once). Raises
    ConnectionResetError if the caller hangs up meanwhile, or the port has
    failed (pyserial-asyncio then drops what is written, and a sender that
    only writes would never know)."""
    while not self._closed:
      if self._transport.is_closing():
        raise ConnectionResetError("the serial port failed")
      if self._carrier is not None and not self._carrier.check():
        raise ConnectionResetError("the serial port failed" if self._carrier.port_failed
                                   else "the caller hung up")
      if self._queued() <= self._queue_limit:
        return
      await asyncio.sleep(DRAIN_POLL)

  def _queued(self):
    serial = self._transport.serial
    try:
      return self._transport.get_write_buffer_size() + (serial.out_waiting if serial else 0)
    except Exception:  # (the port gone: nothing will leave)
      return 0

  def close(self):
    """Hang up and close the port, in the background (see wait_closed)."""
    if self._hangup is None:
      self._closed = True  # (what is already queued still goes)
      self._hangup = asyncio.ensure_future(self._hang_up())

  async def wait_closed(self):
    if self._hangup is not None:
      await self._hangup

  def get_extra_info(self, name, default=None):
    if name == "TERM":
      return "ansi-bbs"  # modem terminals are typically CP437/ANSI
    if name == "peername":
      return (self._port, 0)
    return default

  async def _hang_up(self):
    """Wait (a while) for the output still queued to leave, then drop DTR;
    if the carrier stays up, or cannot be told (a modem not set to hang up
    on DTR), the +++ escape and ATH. The port is closed at the end, however
    it went: DTR is low by then whatever stopped this (a shutdown cancels
    it), so the modem is not left off hook."""
    if self._carrier_watch is not None:
      self._carrier_watch.cancel()
    serial = self._transport.serial
    if serial is None:  # (the port has already closed)
      return
    try:
      await self._flushed(FLUSH_LIMIT)
      serial.dtr = False
      await asyncio.sleep(DTR_DROP)
      if await self._still_connected(serial):
        log.info("Modem on %s: perhaps still connected with DTR low; hanging up with ATH",
                 self._port)
        await asyncio.sleep(GUARD_TIME)
        self._transport.write(b"+++")
        await asyncio.sleep(GUARD_TIME)
        self._transport.write(b"ATH\r")
        await self._flushed(2.0)
      log.debug("Modem on %s: hung up", self._port)
    except Exception as exc:  # (the port gone, say)
      log.debug("Modem on %s: hanging up: %s: %s", self._port, type(exc).__name__, exc)
    finally:
      try:
        serial.dtr = False
      except Exception:
        pass
      _close_port(self._transport)

  async def _still_connected(self, serial):
    """After DTR dropped: whether the modem may still be connected. It may
    take a few seconds to drop the carrier (HANGUP_WAIT); with no carrier to
    tell by, it may have ignored DTR, so yes."""
    if self._carrier is None or not self._carrier.seen:
      return True
    loop = asyncio.get_running_loop()
    end = loop.time() + HANGUP_WAIT
    while serial.cd:
      if loop.time() >= end:
        return True
      await asyncio.sleep(0.1)
    return False

  async def _flushed(self, limit):
    """Wait, at most *limit* seconds, until what was written has left both
    the transport's buffer and the port's."""
    loop = asyncio.get_running_loop()
    end = loop.time() + limit
    serial = self._transport.serial
    while loop.time() < end:
      if self._transport.get_write_buffer_size() == 0 and not serial.out_waiting:
        return
      await asyncio.sleep(0.1)


def _close_port(transport):
  """Close the port now, dropping any output still queued. pyserial-asyncio's
  close() would wait for that output, and its port flush runs on the event
  loop's thread without a time limit: a modem that has stopped taking data
  (switched off, or flow control held) would stop the whole BBS, or leave
  the port open for good."""
  serial = transport.serial
  if serial is None:  # (closed already: the port failed, say)
    return
  try:
    serial.reset_output_buffer()  # (so that the flush when it closes is quick)
  except Exception:
    pass
  # A close already under way finishes, unless it is pyserial-asyncio's own
  # graceful one (after a failed read) with output in its buffer: that never
  # ends on Windows, its writer stopped; its end was never scheduled, so the
  # abort schedules it once.
  if not transport.is_closing() or transport.get_write_buffer_size():
    transport.abort()


async def _read_line(reader, timeout):
  """The modem's next line that is not empty, stripped; None if none comes
  within *timeout* seconds (None: no limit). Raises ModemGone if the port
  closed or failed, rather than reading as a quiet one (or a loop waiting for
  RING would spin on a dead port, and stop the whole BBS).

  A line ends at its LF (results come as CR LF text CR LF: ended at the CR,
  CONNECT's LF would be the caller's first key), or at the CR that ends an
  echoed command or a numeric result (V0, which has no LF; until SETUP sets
  E0V1)."""
  loop = asyncio.get_running_loop()
  end = None if timeout is None else loop.time() + timeout
  line = bytearray()
  while True:
    remaining = None if end is None else end - loop.time()
    if remaining is not None and remaining <= 0:
      return None
    try:
      ch = await asyncio.wait_for(reader.read(1), remaining)
    except asyncio.TimeoutError:
      return None
    except Exception as exc:
      raise ModemGone(f"{type(exc).__name__}: {exc}") from exc
    if not ch:
      raise ModemGone("the port closed")
    text = line.strip()
    if ch == b"\n" or (ch == b"\r" and (text.isdigit() or text[:2].upper() == b"AT")):
      if text:
        return text.decode("ascii", "replace")
      line.clear()
    elif ch != b"\r":
      line += ch


def _send(writer, command):
  writer.write(command.encode("ascii", "replace") + b"\r")


async def _command(reader, writer, command, timeout):
  """Send the AT *command*. Returns the modem's final result ("OK" or
  "ERROR"), or None if it gives none within *timeout* seconds."""
  _send(writer, command)
  await writer.drain()
  loop = asyncio.get_running_loop()
  end = loop.time() + timeout
  while True:
    line = await _read_line(reader, end - loop.time())
    if line is None:
      return None
    result = _FINAL.get(line.upper())
    if result:
      return result
    # (the command's echo, an information line, a RING)


async def _answer(reader, writer, timeout):
  """Answer (ATA). Returns (result, carrier): the CONNECT line or another
  final result (NO CARRIER, say), or None if the modem says nothing within
  *timeout* seconds; and the CARRIER line before it, if the modem gave one."""
  _send(writer, "ATA")
  await writer.drain()
  loop = asyncio.get_running_loop()
  end = loop.time() + timeout
  carrier = None
  while True:
    line = await _read_line(reader, end - loop.time())
    if line is None:
      return None, carrier
    upper = line.upper()
    if upper.startswith("CONNECT") or upper in _ANSWER_FAILED:
      return line, carrier
    if upper.startswith("CARRIER"):
      carrier = line
    # (RING again, caller ID, other information lines)


def line_speed(connect, carrier=None):
  """The line's speed in bits a second: from the modem's CARRIER message if
  it gave one ("CARRIER 2400"), else from CONNECT ("CONNECT 33600/ARQ/V34";
  a bare "CONNECT" means 300). At most ANALOG_TOP: many modems report in
  CONNECT the computer's speed to them (115200) rather than the line's."""
  for message, word in ((carrier, "CARRIER"), (connect, "CONNECT")):
    m = re.match(word + r"\s+(\d+)", (message or "").strip().upper())
    if m:
      return min(int(m.group(1)), ANALOG_TOP)
  return 300


async def _watch_carrier(carrier, transport, stream_reader, port):
  """End the call's input when the carrier drops (the caller hung up), so
  that a session waiting for a key ends too. Warns when the modem never shows
  a carrier: hang-ups then go unnoticed (but for the idle timeout)."""
  looks = 0
  while carrier.check():
    await asyncio.sleep(CARRIER_POLL)
    looks += 1
    if looks == 4 and not carrier.seen:
      log.warning("Modem on %s: the modem shows no carrier (DCD), so a caller's hang-up will "
                  "not be noticed (is it set &C1, and the cable wired for DCD?)", port)
  if carrier.port_failed:
    log.warning("Modem on %s: the serial port failed during the call", port)
  else:
    log.info("Modem on %s: the carrier dropped (the caller hung up)", port)
  if not transport.is_closing():
    transport.pause_reading()  # (the modem's NO CARRIER is not for the session)
  stream_reader.feed_eof()


async def wait_for_call(port, baudrate, init_string="ATZ", ready=None):
  """Open *port* at *baudrate* (the computer's speed to the modem), set the
  modem up (the sysop's *init_string*, then SETUP), wait for RING and answer.
  Returns (SerialReader, SerialWriter) once a caller is connected. *ready()*,
  if given, is called once the modem is waiting for calls.

  Raises ModemGone if the port fails meanwhile, and serial.SerialException
  if it cannot be opened."""
  reader, writer = await serial_asyncio.open_serial_connection(
    url=port,
    baudrate=baudrate,
    bytesize=serial_asyncio.serial.EIGHTBITS,
    parity=serial_asyncio.serial.PARITY_NONE,
    stopbits=serial_asyncio.serial.STOPBITS_ONE,
    rtscts=True,
  )
  transport = writer.transport
  try:
    transport.serial.dtr = True  # (a modem set &D2 does nothing without it)
    for command in (init_string, *SETUP):
      if not command:
        continue
      result = await _command(reader, writer, command, COMMAND_TIMEOUT)
      if result is None:
        log.warning("Modem on %s: no answer to %s (is a modem there, switched on, and "
                    "set to %d baud?)", port, command, baudrate)
      elif result == "ERROR":
        log.warning("Modem on %s: %s gave ERROR", port, command)
    log.info("Modem on %s: waiting for a call", port)
    if ready is not None:
      ready()
    while True:
      line = await _read_line(reader, None)
      if not line.upper().startswith("RING"):  # (RING, or RING 1, RING A: distinctive rings)
        log.debug("Modem on %s: %s", port, line)  # (caller ID, stray output)
        continue
      log.info("Modem on %s: %s, answering", port, line)
      result, carrier_line = await _answer(reader, writer, ANSWER_TIMEOUT)
      if result is None or not result.upper().startswith("CONNECT"):
        log.warning("Modem on %s: answered, but no connection (%s)", port,
                    result or "the modem said nothing")
        await _command(reader, writer, "ATH", COMMAND_TIMEOUT)  # (in case it is still trying)
        continue
      log.info("Modem on %s: %s", port, f"{carrier_line}, {result}" if carrier_line else result)
      carrier = _Carrier(transport.serial)
      watch = asyncio.ensure_future(_watch_carrier(carrier, transport, reader, port))
      return (SerialReader(reader, carrier),
              SerialWriter(writer, port, carrier, watch,
                           line_speed=line_speed(result, carrier_line)))
  except BaseException:
    _close_port(transport)
    raise


async def listen(port, baudrate, init_string, session):
  """Answer calls on *port*, one at a time, for ever: *session(reader,
  writer)* runs each; when it returns, the modem hangs up and is set up
  again for the next call. A port that cannot be opened, or fails, is tried
  again every RETRY seconds (its error logged once, until it works again)."""
  log.info("Modem on %s: starting (%d baud)", port, baudrate)
  failing = None

  def ready():
    nonlocal failing
    if failing is not None:
      log.info("Modem on %s: working again", port)
      failing = None

  while True:
    try:
      reader, writer = await wait_for_call(port, baudrate, init_string, ready)
    except Exception as exc:
      text = f"{type(exc).__name__}: {exc}"
      if text != failing:
        log.error("Modem on %s: %s (trying again every %g s)", port, text, RETRY)
        failing = text
      await asyncio.sleep(RETRY)
      continue
    try:
      await session(reader, writer)
    except Exception:
      log.error("Modem on %s: the session failed", port, exc_info=True)
    finally:
      writer.close()
      await writer.wait_closed()
    await asyncio.sleep(SETTLE)
