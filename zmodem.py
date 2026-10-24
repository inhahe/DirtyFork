"""ZMODEM file transfers, sending and receiving, over an asyncio byte stream.

The protocol is Chuck Forsberg's ZMODEM (1988), as lrzsz, SyncTERM and
zmodem.js speak it:

* Frames start with a header: a type and four bytes (a file position, or
  flags), sent as hex (``**`` ZDLE ``B`` + hex digits; what receivers send),
  binary with a 16-bit CRC (``*`` ZDLE ``A``) or binary with a 32-bit CRC
  (``*`` ZDLE ``C``).
* Some headers are followed by data subpackets: the data, ZDLE and a
  frame-end byte saying whether more follows and whether to acknowledge,
  then a CRC (of the kind the header used) over the data and frame end.
* Binary data is ZDLE-escaped: ZDLE (0x18, which is also CAN) introduces an
  escaped byte (the byte XOR 0x40), so flow-control bytes never appear raw.
  Five CANs in a row cancel the session, from either side (a caller pressing
  Ctrl+X five times, say).

Both directions stream: the sender writes the file without waiting for
acknowledgements unless the receiver asked for a limited buffer, and a
receiver that finds a damaged subpacket asks for the data again from its
last good position (ZRPOS).

The link is anything with ``async read() -> bytes`` (some bytes, ``b""`` at
end of stream), ``write(bytes)`` and ``async drain()``; see ``Link``. Nothing
here knows about telnet or the BBS: the caller provides an 8-bit-clean link
and decides where received files go (``receive_files``'s *accept*).
"""

from __future__ import annotations

import asyncio
import binascii
import logging
import os
import re
import zlib
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional, Protocol, Sequence, Union

log = logging.getLogger("dirtyfork.zmodem")

# ---------------------------------------------------------------------------
# Protocol constants
# ---------------------------------------------------------------------------

ZPAD = 0x2A          # '*': starts every header
ZDLE = 0x18          # escape byte; also CAN
CAN = 0x18
BS = 0x08
XON, XOFF = 0x11, 0x13
ZBIN, ZHEX, ZBIN32 = 0x41, 0x42, 0x43  # 'A', 'B', 'C': header formats

# Frame types
ZRQINIT, ZRINIT, ZSINIT, ZACK, ZFILE, ZSKIP, ZNAK, ZABORT, ZFIN, ZRPOS = range(10)
ZDATA, ZEOF, ZFERR, ZCRC, ZCHALLENGE, ZCOMPL, ZCAN, ZFREECNT, ZCOMMAND, ZSTDERR = range(10, 20)
FRAME_NAMES = ("ZRQINIT ZRINIT ZSINIT ZACK ZFILE ZSKIP ZNAK ZABORT ZFIN ZRPOS ZDATA ZEOF "
               "ZFERR ZCRC ZCHALLENGE ZCOMPL ZCAN ZFREECNT ZCOMMAND ZSTDERR").split()

# Subpacket frame ends (the byte after ZDLE)
ZCRCE = 0x68  # 'h': end of frame; header follows
ZCRCG = 0x69  # 'i': frame continues, no acknowledgement
ZCRCQ = 0x6A  # 'j': frame continues; acknowledge with ZACK
ZCRCW = 0x6B  # 'k': end of frame; acknowledge with ZACK
FRAME_ENDS = (ZCRCE, ZCRCG, ZCRCQ, ZCRCW)
ZRUB0, ZRUB1 = 0x6C, 0x6D  # escaped 0x7F, 0xFF

# ZRINIT flags (ZF0)
CANFDX = 0x01   # full duplex
CANOVIO = 0x02  # can receive data while writing to disk
CANBRK = 0x04
CANFC32 = 0x20  # can use 32-bit CRCs
ESCCTL = 0x40   # wants every control character escaped
ESC8 = 0x80     # wants the 8th bit escaped (unsupported)
# ZSINIT flags (ZF0)
TESCCTL = 0x40
# ZFILE conversion option (ZF0)
ZCBIN = 1       # binary: no newline conversion

ABORT_SEQUENCE = bytes([CAN] * 10 + [BS] * 10)  # what lrzsz sends (its "canit")
CANS_TO_ABORT = 5

SUBPACKET_SIZE = 1024        # what we send: the size every receiver accepts
MAX_SUBPACKET = 8192 + 64    # what we accept (lrzsz and zmodem.js send up to 8 KiB)
MAX_GARBAGE = 16 * 1024      # bytes skipped while looking for a header before giving up

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class TransferError(Exception):
    """The transfer failed; ``str()`` is suitable for the caller to see."""


class Aborted(TransferError):
    """The other side cancelled the session (five CANs, ZABORT, ZFERR, ZCAN)."""


class TimedOut(TransferError):
    """The other side stopped answering."""


class LinkClosed(TransferError):
    """The connection ended."""


class _BadFrame(Exception):
    """A header or subpacket arrived damaged (bad CRC, bad escape, too long).
    Recoverable: the receiver asks for the data again."""


# ---------------------------------------------------------------------------
# Link and helpers
# ---------------------------------------------------------------------------


class Link(Protocol):
    """An 8-bit-clean byte stream to the other side."""

    async def read(self) -> bytes:
        """Some bytes as they arrive; b"" once the stream has ended."""

    def write(self, data: bytes) -> None:
        """Queue bytes for sending."""

    async def drain(self) -> None:
        """Wait until queued bytes have gone (flow control)."""


@dataclass
class Header:
    """A received or sent header: its type and its four data bytes.

    For position headers (ZRPOS, ZDATA, ZEOF, ZACK, ...) the four bytes are a
    little-endian file position; for flag headers (ZRINIT, ZSINIT, ZFILE) they
    are ZF3, ZF2, ZF1, ZF0. ``crc32`` says which CRC the header itself used,
    which is the one its data subpackets use too.
    """
    type: int
    data: bytes = b"\0\0\0\0"
    crc32: bool = False

    @property
    def pos(self) -> int:
        return int.from_bytes(self.data, "little")

    @property
    def f0(self) -> int:
        return self.data[3]

    @property
    def name(self) -> str:
        return FRAME_NAMES[self.type] if 0 <= self.type < len(FRAME_NAMES) else f"type {self.type}"

    def __repr__(self) -> str:
        return f"<{self.name} {self.data.hex()}{' crc32' if self.crc32 else ''}>"


def pos_bytes(pos: int) -> bytes:
    """A file position as a header's four data bytes."""
    return (pos & 0xFFFFFFFF).to_bytes(4, "little")


def flag_bytes(f0: int = 0, f1: int = 0, f2: int = 0, f3: int = 0) -> bytes:
    """Flags ZF0..ZF3 as a header's four data bytes (ZF0 is sent last)."""
    return bytes((f3, f2, f1, f0))


def _crc16(data: bytes) -> int:
    return binascii.crc_hqx(data, 0)


def _crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Encoding (what we send)
# ---------------------------------------------------------------------------

class Encoder:
    """Builds headers and subpackets, ZDLE-escaping binary data.

    Always escaped: ZDLE, DLE, XON, XOFF (and their high-bit forms), and CR
    (and 0x8D). The protocol needs CR escaped only after '@', but escaping
    every CR costs little and keeps the data safe through a telnet layer that
    is not in binary mode. With *escape_ctrl* (the receiver's ESCCTL), every
    control character is escaped.
    """

    _BASIC = b"\x0d\x10\x11\x13\x18\x8d\x90\x91\x93"

    def __init__(self, escape_ctrl: bool = False):
        self.set_escape_ctrl(escape_ctrl)

    def set_escape_ctrl(self, on: bool) -> None:
        self.escape_ctrl = on
        if on:
            chars = bytes(b for b in range(256) if not b & 0x60)
        else:
            chars = self._BASIC
        self._re = re.compile(b"[" + b"".join(b"\\x%02x" % c for c in chars) + b"]")
        self._table = {bytes([c]): bytes([ZDLE, c ^ 0x40]) for c in chars}

    def escape(self, data: bytes) -> bytes:
        return self._re.sub(lambda m: self._table[m.group()], data)

    @staticmethod
    def hex_header(type_: int, data: bytes = b"\0\0\0\0") -> bytes:
        """A hex header: ``**`` ZDLE ``B``, the type, data and CRC-16 as hex,
        CR LF (with the high bit, as lrzsz sends it), and XON except after
        ZACK and ZFIN."""
        raw = bytes([type_]) + data
        crc = _crc16(raw)
        body = (raw + crc.to_bytes(2, "big")).hex().encode()
        tail = b"\r\x8a" + (b"" if type_ in (ZACK, ZFIN) else bytes([XON]))
        return bytes([ZPAD, ZPAD, ZDLE, ZHEX]) + body + tail

    def bin_header(self, type_: int, data: bytes, crc32: bool) -> bytes:
        """A binary header, with a 16- or 32-bit CRC."""
        raw = bytes([type_]) + data
        if crc32:
            raw += _crc32(raw).to_bytes(4, "little")
            return bytes([ZPAD, ZDLE, ZBIN32]) + self.escape(raw)
        raw += _crc16(raw).to_bytes(2, "big")
        return bytes([ZPAD, ZDLE, ZBIN]) + self.escape(raw)

    def subpacket(self, data: bytes, frame_end: int, crc32: bool) -> bytes:
        """A data subpacket: escaped data, ZDLE + frame end, escaped CRC (XON
        after ZCRCW, as lrzsz sends)."""
        covered = data + bytes([frame_end])
        if crc32:
            crc = _crc32(covered).to_bytes(4, "little")
        else:
            crc = _crc16(covered).to_bytes(2, "big")
        out = self.escape(data) + bytes([ZDLE, frame_end]) + self.escape(crc)
        if frame_end == ZCRCW:
            out += bytes([XON])
        return out


# ---------------------------------------------------------------------------
# Decoding (what we receive)
# ---------------------------------------------------------------------------

# Bytes a subpacket's fast path stops at: ZDLE, and flow-control bytes (which
# arrive unescaped only as noise from the line, and are dropped).
_SPECIAL = re.compile(b"[\x18\x11\x13\x91\x93]")
_FLOW = (XON, XOFF, XON | 0x80, XOFF | 0x80)
_HEXDIGITS = {c: int(chr(c), 16) for c in b"0123456789abcdefABCDEF"}


class Reader:
    """Reads headers and subpackets from a link.

    Counts consecutive CAN bytes as it goes: five raise Aborted, whatever is
    being read. (ZDLE is CAN, but escaped data never has two in a row.)
    """

    def __init__(self, link: Link):
        self.link = link
        self.buf = bytearray()  # (deleting from its front is cheap: CPython moves its start)
        self.cans = 0

    async def _fill(self, deadline: Optional[float]) -> None:
        """Wait for more bytes, until *deadline* (loop time; None: forever)."""
        if deadline is None:
            data = await self.link.read()
        else:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise asyncio.TimeoutError()
            data = await asyncio.wait_for(self.link.read(), remaining)
        if not data:
            raise LinkClosed("the connection closed")
        self.buf += data

    async def byte(self, deadline: Optional[float]) -> int:
        """The next byte, raw (not unescaped)."""
        if not self.buf:
            await self._fill(deadline)
        b = self.buf[0]
        del self.buf[0]
        if b == CAN:
            self.cans += 1
            if self.cans >= CANS_TO_ABORT:
                raise Aborted("the transfer was cancelled")
        else:
            self.cans = 0
        return b

    async def _escaped(self, deadline: Optional[float]) -> int:
        """The byte after a ZDLE: a frame end (returned with 0x100 added), or
        the unescaped data byte."""
        c = await self.byte(deadline)
        while c in _FLOW:
            c = await self.byte(deadline)
        if c in FRAME_ENDS:
            return c | 0x100
        if c == ZRUB0:
            return 0x7F
        if c == ZRUB1:
            return 0xFF
        if c & 0x60 == 0x40:
            return c ^ 0x40
        raise _BadFrame(f"bad escape 0x{c:02x}")

    async def _data_byte(self, deadline: Optional[float]) -> int:
        """One unescaped byte of a header or a CRC; a frame end is an error."""
        b = await self.byte(deadline)
        while b in _FLOW:
            b = await self.byte(deadline)
        if b != ZDLE:
            return b
        c = await self._escaped(deadline)
        if c > 0xFF:
            raise _BadFrame("frame end inside a header or CRC")
        return c

    async def header(self, timeout: Optional[float]) -> Header:
        """The next header, skipping anything before it.

        Raises asyncio.TimeoutError when none arrives within *timeout*
        seconds, _BadFrame when one arrives damaged (or too much else arrives
        first), Aborted and LinkClosed.
        """
        deadline = None if timeout is None else asyncio.get_running_loop().time() + timeout
        skipped = 0
        while True:
            b = await self.byte(deadline)
            if b != ZPAD:
                skipped += 1
                if skipped > MAX_GARBAGE:
                    raise _BadFrame("no header found")
                continue
            b = await self.byte(deadline)
            while b == ZPAD:
                b = await self.byte(deadline)
            if b != ZDLE:
                skipped += 2
                continue
            fmt = await self.byte(deadline)
            if fmt == ZHEX:
                return await self._hex_header(deadline)
            if fmt in (ZBIN, ZBIN32):
                return await self._bin_header(deadline, fmt == ZBIN32)
            skipped += 3

    async def _hex_header(self, deadline: Optional[float]) -> Header:
        digits = []
        for _ in range(14):
            b = await self.byte(deadline)
            if b not in _HEXDIGITS:
                raise _BadFrame("bad hex header")
            digits.append(_HEXDIGITS[b])
        raw = bytes(digits[i] << 4 | digits[i + 1] for i in range(0, 14, 2))
        if _crc16(raw[:5]) != int.from_bytes(raw[5:], "big"):
            raise _BadFrame("bad CRC in a hex header")
        # The trailing CR, LF and XON (each with or without the high bit, in
        # that order, each at most once): consumed when they are already here,
        # so a subpacket after a hex header (which only nonconforming senders
        # send) does not start with them. Its data may itself start with an LF,
        # so nothing more is taken. Anything not here yet is skipped as noise
        # by the next header read.
        for expected in ((0x0D, 0x8D), (0x0A, 0x8A), (XON, XON | 0x80)):
            if self.buf and self.buf[0] in expected:
                del self.buf[0]
        return Header(raw[0], raw[1:5], crc32=False)

    async def _bin_header(self, deadline: Optional[float], crc32: bool) -> Header:
        n = 5 + (4 if crc32 else 2)
        raw = bytes([await self._data_byte(deadline) for _ in range(n)])
        if crc32:
            ok = _crc32(raw[:5]) == int.from_bytes(raw[5:], "little")
        else:
            ok = _crc16(raw[:5]) == int.from_bytes(raw[5:], "big")
        if not ok:
            raise _BadFrame("bad CRC in a binary header")
        return Header(raw[0], raw[1:5], crc32=crc32)

    async def subpacket(self, crc32: bool, timeout: Optional[float],
                        max_len: int = MAX_SUBPACKET) -> tuple[bytes, int]:
        """The next data subpacket: (data, frame end). *timeout* applies to
        the whole subpacket. Raises _BadFrame for a damaged or overlong one."""
        deadline = None if timeout is None else asyncio.get_running_loop().time() + timeout
        data = bytearray()
        while True:
            if len(data) > max_len:  # (counting escaped bytes too)
                raise _BadFrame("subpacket too long")
            if not self.buf:
                await self._fill(deadline)
            m = _SPECIAL.search(self.buf)
            end = m.start() if m else len(self.buf)
            if end:
                data += self.buf[:end]
                del self.buf[:end]
                self.cans = 0
            if not m:
                continue
            b = await self.byte(deadline)
            if b != ZDLE:
                continue  # flow-control noise
            c = await self._escaped(deadline)
            if c > 0xFF:
                frame_end = c & 0xFF
                break
            data.append(c)
        n = 4 if crc32 else 2
        crc = bytes([await self._data_byte(deadline) for _ in range(n)])
        covered = bytes(data) + bytes([frame_end])
        if crc32:
            ok = _crc32(covered) == int.from_bytes(crc, "little")
        else:
            ok = _crc16(covered) == int.from_bytes(crc, "big")
        if not ok:
            raise _BadFrame("bad CRC in a data subpacket")
        return bytes(data), frame_end


# ---------------------------------------------------------------------------
# File information (the ZFILE subpacket)
# ---------------------------------------------------------------------------


@dataclass
class FileOffer:
    """A file the sender offers: what its ZFILE subpacket says.

    name: the file name as sent (may contain a path; the receiver must
    sanitise it). size, mtime (Unix time), mode: None when not sent.
    files_left, bytes_left: what the sender says remains, this file included.
    """
    name: str
    size: Optional[int] = None
    mtime: Optional[int] = None
    mode: Optional[int] = None
    files_left: Optional[int] = None
    bytes_left: Optional[int] = None


def encode_file_info(name: str, size: int, mtime: int, mode: int = 0o100644,
                     files_left: int = 1, bytes_left: Optional[int] = None) -> bytes:
    """The ZFILE subpacket's data, as lrzsz writes it."""
    if bytes_left is None:
        bytes_left = size
    meta = f"{size} {int(mtime):o} {mode:o} 0 {files_left} {bytes_left}"
    return name.encode("utf-8") + b"\0" + meta.encode("ascii") + b"\0"


def parse_file_info(data: bytes) -> FileOffer:
    """Parse a ZFILE subpacket. The name is UTF-8 when it decodes as such
    (zmodem.js, modern lrzsz), else CP437 (DOS-era terminals)."""
    raw_name, _, rest = data.partition(b"\0")
    try:
        name = raw_name.decode("utf-8")
    except UnicodeDecodeError:
        name = raw_name.decode("cp437")
    fields = rest.split(b"\0", 1)[0].split()

    def number(i: int, base: int) -> Optional[int]:
        try:
            return int(fields[i], base)
        except (IndexError, ValueError):
            return None

    return FileOffer(name=name, size=number(0, 10), mtime=number(1, 8), mode=number(2, 8),
                     files_left=number(4, 10), bytes_left=number(5, 10))


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


@dataclass
class FileResult:
    """What happened to one file: status is "sent"/"received", "skipped"
    (the receiver declined it, or we did) or "failed"; bytes is how much went
    through."""
    name: str
    status: str
    bytes: int = 0


@dataclass
class Settings:
    """Timeouts (seconds) and limits for a session.

    start_timeout: how long to wait for the other side to begin (a caller
    choosing files in a dialog takes a while). header_timeout: how long to
    wait for a header or subpacket once going; each expiry counts as an error
    and asks again. retries: errors in a row before giving up.
    stall_timeout: how long what we send may wait to leave (the other side
    has stopped reading) before giving up; generous, for slow modems.
    escape_ctrl: as receiver, ask the sender to escape every control
    character (for a link that is not 8-bit clean); as sender, escape them.
    """
    start_timeout: float = 120.0
    header_timeout: float = 10.0
    retries: int = 10
    stall_timeout: float = 300.0
    escape_ctrl: bool = False


class _Output:
    """What a session sends, with flow control that a failure can interrupt.

    Drains every DRAIN_EVERY bytes (and after control frames). A drain is
    abandoned when *failed* is set (the other side cancelled while we were
    blocked) or after the stall timeout.
    """
    DRAIN_EVERY = 16 * 1024

    def __init__(self, link: Link, settings: Settings):
        self.link = link
        self.settings = settings
        self.pending = 0
        self.failed = asyncio.Event()
        self.failure: Optional[BaseException] = None

    def fail(self, exc: BaseException) -> None:
        if self.failure is None:
            self.failure = exc
        self.failed.set()

    async def send(self, data: bytes, flush: bool = True) -> None:
        if self.failure is not None:
            raise self.failure
        self.link.write(data)
        self.pending += len(data)
        if flush or self.pending >= self.DRAIN_EVERY:
            self.pending = 0
            drain = asyncio.ensure_future(self.link.drain())
            failed = asyncio.ensure_future(self.failed.wait())
            done, _ = await asyncio.wait({drain, failed}, timeout=self.settings.stall_timeout,
                                         return_when=asyncio.FIRST_COMPLETED)
            failed.cancel()
            if drain not in done:
                drain.cancel()
                if self.failure is not None:
                    raise self.failure
                raise TimedOut("the other side stopped reading")
            drain.result()


# ---------------------------------------------------------------------------
# Sending
# ---------------------------------------------------------------------------


@dataclass
class SendFile:
    """A file to send. path: where it is; name: what to call it (default:
    the path's base name)."""
    path: str
    name: Optional[str] = None


class _Sender:
    def __init__(self, link: Link, settings: Settings):
        self.link = link
        self.settings = settings
        self.reader = Reader(link)
        self.out = _Output(link, settings)
        self.enc = Encoder(settings.escape_ctrl)
        self.crc32 = False
        self.window = 0  # bytes between acknowledgements (0: stream)
        self.headers: asyncio.Queue = asyncio.Queue()
        self.monitor: Optional[asyncio.Task] = None

    async def _monitor(self) -> None:
        """Read the receiver's headers into self.headers, so the sending loop
        can look for them between subpackets without blocking. Damaged
        headers are dropped; an abort or a closed link is queued, interrupts
        a send that is blocked, and ends the task."""
        while True:
            try:
                hdr = await self.reader.header(None)
            except _BadFrame as exc:
                log.debug("send: dropped a damaged header: %s", exc)
                continue
            except asyncio.CancelledError:
                return
            except BaseException as exc:  # Aborted, LinkClosed
                self.headers.put_nowait(exc)
                self.out.fail(exc)
                return
            self.headers.put_nowait(hdr)

    async def next_header(self, timeout: float) -> Header:
        item = await asyncio.wait_for(self.headers.get(), timeout)
        if isinstance(item, BaseException):
            raise item
        return item

    def pending_header(self) -> Optional[Header]:
        """A header that has already arrived, if any."""
        try:
            item = self.headers.get_nowait()
        except asyncio.QueueEmpty:
            return None
        if isinstance(item, BaseException):
            raise item
        return item

    async def send(self, data: bytes, flush: bool = True) -> None:
        await self.out.send(data, flush)

    async def run(self, files: Sequence[SendFile]) -> list[FileResult]:
        self.monitor = asyncio.create_task(self._monitor())
        try:
            await self._handshake()
            results = []
            sizes = [os.path.getsize(f.path) for f in files]
            for i, f in enumerate(files):
                results.append(await self._send_file(f, files_left=len(files) - i,
                                                     bytes_left=sum(sizes[i:])))
            await self._finish()
            return results
        except (Aborted, LinkClosed):
            raise
        except Exception:
            await _try_cancel(self.link)
            raise
        finally:
            self.monitor.cancel()
            try:
                await self.monitor
            except BaseException:
                pass

    async def _handshake(self) -> None:
        """ZRQINIT until the receiver answers ZRINIT; adopt its capabilities."""
        loop = asyncio.get_running_loop()
        give_up = loop.time() + self.settings.start_timeout
        await self.send(Encoder.hex_header(ZRQINIT))
        while True:
            timeout = min(self.settings.header_timeout, give_up - loop.time())
            if timeout <= 0:
                raise TimedOut("the receiver never started")
            try:
                hdr = await self.next_header(timeout)
            except asyncio.TimeoutError:
                await self.send(Encoder.hex_header(ZRQINIT))
                continue
            if hdr.type == ZRINIT:
                break
            if hdr.type == ZCHALLENGE:
                await self.send(Encoder.hex_header(ZACK, hdr.data))
            elif hdr.type in (ZABORT, ZFERR, ZCAN):
                raise Aborted("the receiver cancelled")
            elif hdr.type == ZNAK:
                await self.send(Encoder.hex_header(ZRQINIT))
        f0 = hdr.f0
        self.crc32 = bool(f0 & CANFC32)
        self.enc.set_escape_ctrl(self.settings.escape_ctrl or bool(f0 & ESCCTL))
        bufsize = hdr.data[0] | hdr.data[1] << 8
        if bufsize:
            self.window = max(SUBPACKET_SIZE, bufsize - bufsize % SUBPACKET_SIZE)
        elif not (f0 & CANFDX and f0 & CANOVIO):
            self.window = SUBPACKET_SIZE  # it cannot take data while writing it
        log.debug("send: receiver flags 0x%02x, buffer %d, crc32 %s", f0, bufsize, self.crc32)

    async def _send_file(self, f: SendFile, files_left: int, bytes_left: int) -> FileResult:
        name = f.name or os.path.basename(f.path)
        st = os.stat(f.path)
        size = st.st_size
        info = encode_file_info(name, size, int(st.st_mtime), files_left=files_left,
                                bytes_left=bytes_left)
        zfile = (self.enc.bin_header(ZFILE, flag_bytes(f0=ZCBIN), self.crc32)
                 + self.enc.subpacket(info, ZCRCW, self.crc32))
        loop = asyncio.get_running_loop()
        # A ZRINIT this soon after an offer was sent before the receiver saw
        # it (one answers each ZRQINIT, and one follows each file): ignore it.
        # A later one means the offer was lost.
        stale = min(2.0, self.settings.header_timeout / 2)
        with open(f.path, "rb") as fp:
            # Offer the file until the receiver says where to start (or skips it)
            errors = 0
            await self.send(zfile)
            offered = loop.time()
            while True:
                try:
                    hdr = await self.next_header(self.settings.header_timeout)
                except asyncio.TimeoutError:
                    hdr = None
                if hdr is not None and hdr.type == ZRPOS:
                    start = min(hdr.pos, size)
                    break
                if hdr is not None and hdr.type == ZSKIP:
                    log.info("send: the receiver skipped %s", name)
                    return FileResult(name, "skipped")
                if hdr is not None and hdr.type == ZCRC:
                    # (in a thread: a big file would stop every other session meanwhile)
                    crc = await asyncio.to_thread(_file_crc, f.path)
                    await self.send(Encoder.hex_header(ZCRC, pos_bytes(crc)))
                    continue
                if hdr is not None and hdr.type in (ZABORT, ZFERR, ZCAN, ZFIN):
                    raise Aborted("the receiver cancelled")
                if hdr is not None and hdr.type == ZRINIT and loop.time() - offered < stale:
                    continue
                errors += 1  # a timeout, ZNAK, or a later ZRINIT: offer again
                if errors > self.settings.retries:
                    raise TimedOut("the receiver did not accept the file")
                await self.send(zfile)
                offered = loop.time()
            status, sent = await self._stream(fp, name, start, size)
            return FileResult(name, status, sent)

    def _count_error(self, errors: int) -> int:
        errors += 1
        if errors > self.settings.retries:
            raise TransferError("too many errors")
        return errors

    async def _stream(self, fp, name: str, pos: int, size: int) -> tuple[str, int]:
        """Send the file's data from *pos*, then ZEOF, until the receiver
        confirms the end with ZRINIT (or skips the file). Returns ("sent" or
        "skipped", position reached)."""
        errors = 0
        while True:  # once per (re)start at a position
            restart = await self._send_data(fp, pos, size)
            if restart == "skip":
                return "skipped", pos
            if restart is not None:
                errors = self._count_error(errors)
                log.info("send: %s: the receiver asked for the data again from %d", name, restart)
                pos = restart
                continue
            pos = fp.tell()
            # All sent: ZEOF until the receiver confirms the file (ZRINIT)
            eof = self.enc.bin_header(ZEOF, pos_bytes(pos), self.crc32)
            await self.send(eof)
            while True:
                try:
                    hdr = await self.next_header(self.settings.header_timeout)
                except asyncio.TimeoutError:
                    errors = self._count_error(errors)
                    await self.send(eof)
                    continue
                if hdr.type == ZRINIT:
                    return "sent", pos
                if hdr.type == ZSKIP:
                    return "skipped", pos
                if hdr.type == ZRPOS:
                    errors = self._count_error(errors)
                    pos = min(hdr.pos, size)
                    break  # send again from there
                if hdr.type in (ZABORT, ZFERR, ZCAN, ZFIN):
                    raise Aborted("the receiver cancelled")
                # ZACK and the like: keep waiting

    async def _send_data(self, fp, pos: int, size: int):
        """Send ZDATA and the file from *pos* to *size* (the size announced).
        Returns None once it has all gone, a position to send again from, or
        "skip"."""
        fp.seek(pos)
        await self.send(self.enc.bin_header(ZDATA, pos_bytes(pos), self.crc32))
        acked, unacked = pos, 0
        first = True
        while True:
            # Headers that arrived meanwhile are looked at only after a
            # subpacket has followed the ZDATA: a receiver hunting for the
            # restart needs a header *and* data, or it asks again, forever.
            hdr = None if first else self.pending_header()
            first = False
            if hdr is not None:
                restart = self._mid_stream(hdr, pos)
                if restart is not None:
                    return restart
            chunk = fp.read(min(SUBPACKET_SIZE, size - pos))
            last = not chunk or pos + len(chunk) >= size
            unacked += len(chunk)
            if last:
                end = ZCRCE
            elif self.window and unacked >= self.window:
                end = ZCRCW
            else:
                end = ZCRCG
            await self.send(self.enc.subpacket(chunk, end, self.crc32), flush=end != ZCRCG)
            pos += len(chunk)
            if last:
                return None
            if end == ZCRCW:
                restart = await self._wait_ack(pos, acked)
                if restart is not None:
                    return restart
                acked, unacked = pos, 0
                await self.send(self.enc.bin_header(ZDATA, pos_bytes(pos), self.crc32))

    def _mid_stream(self, hdr: Header, pos: int):
        """React to a header that arrived while sending data: a position to
        send again from, "skip", or None to carry on."""
        if hdr.type == ZRPOS:
            return min(hdr.pos, pos)
        if hdr.type == ZSKIP:
            return "skip"
        if hdr.type in (ZABORT, ZFERR, ZCAN, ZFIN):
            raise Aborted("the receiver cancelled")
        return None  # ZACK, ZNAK, a late ZRINIT: nothing to do

    async def _wait_ack(self, pos: int, acked: int):
        """After a ZCRCW at *pos*: wait for the receiver's ZACK. Returns None
        when acknowledged, else a position to send again from (*acked*, the
        last acknowledged one, if it never answers) or "skip"."""
        for _ in range(self.settings.retries):
            try:
                hdr = await self.next_header(self.settings.header_timeout)
            except asyncio.TimeoutError:
                return acked
            if hdr.type == ZACK:
                return None
            restart = self._mid_stream(hdr, pos)
            if restart is not None:
                return restart
        raise TimedOut("the receiver stopped acknowledging")

    async def _finish(self) -> None:
        """ZFIN until the receiver answers ZFIN, then "OO" (over and out)."""
        for _ in range(3):
            await self.send(Encoder.hex_header(ZFIN))
            try:
                while True:
                    hdr = await self.next_header(self.settings.header_timeout)
                    if hdr.type == ZFIN:
                        await self.send(b"OO")
                        return
                    if hdr.type in (ZABORT, ZFERR, ZCAN):
                        return  # done anyway
            except asyncio.TimeoutError:
                continue
        log.info("send: the receiver did not answer ZFIN; ending anyway")


async def _try_cancel(link: Link) -> None:
    """Tell the other side we are giving up, if the link still works."""
    try:
        link.write(ABORT_SEQUENCE)
        await asyncio.wait_for(link.drain(), 5)
    except Exception:
        pass


def _file_crc(path: str) -> int:
    """CRC-32 of a whole file (the answer to ZCRC)."""
    crc = 0
    with open(path, "rb") as fp:
        while chunk := fp.read(65536):
            crc = zlib.crc32(chunk, crc)
    return crc & 0xFFFFFFFF


async def send_files(link: Link, files: Sequence[Union[SendFile, str]],
                     settings: Optional[Settings] = None) -> list[FileResult]:
    """Send *files* (SendFile, or paths) to the other side.

    Returns one FileResult per file sent or skipped. Raises TransferError
    (Aborted, TimedOut, LinkClosed) when the session fails; on our own
    errors the other side has been sent the abort sequence.
    """
    files = [f if isinstance(f, SendFile) else SendFile(f) for f in files]
    return await _Sender(link, settings or Settings()).run(files)


# ---------------------------------------------------------------------------
# Receiving
# ---------------------------------------------------------------------------


class Sink(Protocol):
    """Where a received file's data goes (see receive_files' *accept*)."""

    def write(self, data: bytes) -> None:
        """Store data. Raise TransferError to stop the whole transfer (a size
        limit, a full disk)."""

    def finish(self) -> None:
        """The file arrived whole: keep it."""

    def discard(self) -> None:
        """The file did not arrive whole: throw away what was written."""


Accept = Callable[[FileOffer], Union[Optional[Sink], Awaitable[Optional[Sink]]]]


class _Receiver:
    def __init__(self, link: Link, accept: Accept, settings: Settings, max_files: int):
        self.link = link
        self.accept = accept
        self.settings = settings
        self.max_files = max_files
        self.reader = Reader(link)
        self.accepted = 0
        flags = CANFDX | CANOVIO | CANFC32 | (ESCCTL if settings.escape_ctrl else 0)
        self.zrinit = Encoder.hex_header(ZRINIT, flag_bytes(f0=flags))
        self.out = _Output(link, settings)

    async def send(self, data: bytes) -> None:
        await self.out.send(data)

    async def run(self) -> list[FileResult]:
        results: list[FileResult] = []
        loop = asyncio.get_running_loop()
        give_up = loop.time() + self.settings.start_timeout
        errors = 0
        await self.send(self.zrinit)
        try:
            while True:
                # (checked whatever arrives: a sender repeating ZRQINIT, say,
                # because it never hears us, must not hold the session forever)
                if loop.time() >= give_up:
                    raise TimedOut("nothing was sent")
                try:
                    hdr = await self.reader.header(self.settings.header_timeout)
                except asyncio.TimeoutError:
                    await self.send(self.zrinit)
                    continue
                except _BadFrame as exc:
                    errors += 1
                    log.debug("receive: %s", exc)
                    if errors > self.settings.retries:
                        raise TransferError("too many errors")
                    await self.send(self.zrinit)
                    continue
                if hdr.type == ZRQINIT:
                    await self.send(self.zrinit)
                elif hdr.type == ZSINIT:
                    await self._zsinit(hdr)
                elif hdr.type == ZFILE:
                    result = await self._file(hdr)
                    if result is not None:  # (None: the offer arrived damaged; it comes again)
                        results.append(result)
                        errors = 0
                        give_up = loop.time() + self.settings.start_timeout
                        # A received file is acknowledged with ZRINIT; a skipped one
                        # has its ZSKIP, and a ZRINIT now would meet a sender
                        # waiting for the answer to its next offer (zmodem.js
                        # gives up on it). As lrzsz does: ZRINIT again only if
                        # nothing comes.
                        if result.status == "received":
                            await self.send(self.zrinit)
                elif hdr.type == ZFIN:
                    await self.send(Encoder.hex_header(ZFIN))
                    await self._over_and_out()
                    return results
                elif hdr.type == ZFREECNT:
                    await self.send(Encoder.hex_header(ZACK, pos_bytes(0xFFFFFFFF)))
                elif hdr.type == ZCHALLENGE:
                    await self.send(Encoder.hex_header(ZACK, hdr.data))
                elif hdr.type == ZCOMMAND:
                    raise TransferError("the sender asked to run a command; refused")
                elif hdr.type in (ZABORT, ZFERR, ZCAN):
                    raise Aborted("the sender cancelled")
                else:
                    # ZDATA/ZEOF for a file we skipped, and the like
                    await self.send(self.zrinit)
        except (Aborted, LinkClosed):
            raise
        except Exception:
            await _try_cancel(self.link)
            raise

    async def _zsinit(self, hdr: Header) -> None:
        """The sender's options (and attention string, which we never use)."""
        try:
            await self.reader.subpacket(hdr.crc32, self.settings.header_timeout, max_len=64)
        except (_BadFrame, asyncio.TimeoutError):
            await self.send(Encoder.hex_header(ZNAK))
            return
        await self.send(Encoder.hex_header(ZACK, pos_bytes(1)))

    async def _file(self, hdr: Header) -> Optional[FileResult]:
        """Take a ZFILE offer: skip it or receive it. None when its subpacket
        arrived damaged (we answered ZNAK, and the sender offers it again)."""
        try:
            info, _ = await self.reader.subpacket(hdr.crc32, self.settings.header_timeout,
                                                  max_len=4096)
        except (_BadFrame, asyncio.TimeoutError):
            await self.send(Encoder.hex_header(ZNAK))
            return None
        offer = parse_file_info(info)
        if self.accepted >= self.max_files:
            log.info("receive: skipping %r: no more than %d files", offer.name, self.max_files)
            sink = None
        else:
            sink = self.accept(offer)
            if asyncio.iscoroutine(sink) or isinstance(sink, asyncio.Future):
                sink = await sink
        if sink is None:
            await self.send(Encoder.hex_header(ZSKIP))
            return FileResult(offer.name, "skipped")
        self.accepted += 1
        try:
            received = await self._data(sink)
            sink.finish()
        except OSError as exc:
            sink.discard()
            raise TransferError(f"the file could not be saved: {exc.strerror or exc}") from exc
        except BaseException:
            sink.discard()
            raise
        return FileResult(offer.name, "received", received)

    async def _data(self, sink: Sink) -> int:
        """Receive one file's data into *sink*, from position 0. Returns its
        length once ZEOF confirms it.

        After we ask for data again (ZRPOS), what the sender had sent before
        it saw that still arrives: until the ZDATA for our position, damaged
        frames and noise in it are expected, not errors. Silence is one, and
        getting back in step has a time limit."""
        loop = asyncio.get_running_loop()
        pos = 0
        errors = 0
        resync_until = None  # (loop time) while getting back in step after a ZRPOS

        async def ask_again(why: str, silence: bool = False) -> None:
            nonlocal errors, resync_until
            errors += 1
            if errors > self.settings.retries:
                if silence:
                    raise TimedOut("the sender stopped sending")
                raise TransferError("too many errors")
            log.debug("receive: %s at %d: asking again", why, pos)
            await self.send(Encoder.hex_header(ZRPOS, pos_bytes(pos)))
            resync_until = loop.time() + self.settings.header_timeout * self.settings.retries

        await self.send(Encoder.hex_header(ZRPOS, pos_bytes(pos)))
        while True:
            if resync_until is not None and loop.time() > resync_until:
                raise TimedOut("the sender did not send the data again")
            try:
                hdr = await self.reader.header(self.settings.header_timeout)
            except asyncio.TimeoutError:
                await ask_again("nothing came", silence=True)
                continue
            except _BadFrame as exc:
                if resync_until is None:
                    await ask_again(str(exc))
                continue  # (while resynchronising: the rest of the old stream)
            if hdr.type == ZDATA:
                if hdr.pos != pos:
                    if resync_until is None:
                        await ask_again(f"data for {hdr.pos}")
                    continue
                resync_until = None
                while True:
                    try:
                        data, end = await self.reader.subpacket(hdr.crc32,
                                                                self.settings.header_timeout)
                    except asyncio.TimeoutError:
                        await ask_again("nothing came", silence=True)
                        break
                    except _BadFrame as exc:
                        await ask_again(str(exc))
                        break
                    sink.write(data)
                    pos += len(data)
                    errors = 0
                    if end == ZCRCQ:
                        await self.send(Encoder.hex_header(ZACK, pos_bytes(pos)))
                    elif end == ZCRCW:
                        await self.send(Encoder.hex_header(ZACK, pos_bytes(pos)))
                        break
                    elif end == ZCRCE:
                        break
            elif hdr.type == ZEOF:
                if hdr.pos == pos:
                    return pos
                # At the wrong place it crossed our last ZRPOS, and the data is
                # coming again; if not, the next timeout asks for it (as lrzsz
                # does). Answering it would set off a second restart.
            elif hdr.type == ZFILE:
                # It did not hear our ZRPOS: take the offer again, and repeat it.
                try:
                    await self.reader.subpacket(hdr.crc32, self.settings.header_timeout,
                                                max_len=4096)
                except (_BadFrame, asyncio.TimeoutError):
                    pass
                await self.send(Encoder.hex_header(ZRPOS, pos_bytes(pos)))
            elif hdr.type == ZNAK:
                await self.send(Encoder.hex_header(ZRPOS, pos_bytes(pos)))
            elif hdr.type in (ZABORT, ZFERR, ZCAN, ZFIN):
                raise Aborted("the sender cancelled")

    async def _over_and_out(self) -> None:
        """Read the sender's closing "OO", if it sends one (briefly)."""
        try:
            for _ in range(2):
                await self.reader.byte(asyncio.get_running_loop().time() + 2)
        except (asyncio.TimeoutError, TransferError):
            pass


async def receive_files(link: Link, accept: Accept, settings: Optional[Settings] = None,
                        max_files: int = 100) -> list[FileResult]:
    """Receive files from the other side.

    *accept* is called with each FileOffer and returns a Sink for its data,
    or None to skip it (it may be a coroutine function). At most *max_files*
    are accepted; later offers are skipped. Returns one FileResult per
    offer. Raises TransferError (Aborted, TimedOut, LinkClosed) when the
    session fails; the file being received is discarded first.
    """
    return await _Receiver(link, accept, settings or Settings(), max_files).run()


async def cancel(link: Link) -> None:
    """Send the abort sequence (ten CANs, ten backspaces)."""
    link.write(ABORT_SEQUENCE)
    await link.drain()
