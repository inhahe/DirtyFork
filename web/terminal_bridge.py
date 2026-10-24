"""WebSocket-to-telnet bridge for the web terminal (xterm.js, with zmodem.js
for file transfers).

A web page cannot open a TCP connection, so the BBS's web terminal (served as
inhahe.com/bbs.html) talks WebSocket to this bridge, and the bridge talks
telnet to the BBS. It only ever connects to the one BBS it was started for.

The page's side (WebSocket subprotocol "dirtyfork-terminal"):

* Its first message is text, JSON: {"cols": C, "rows": R}, the terminal's
  size. The bridge then connects to the BBS.
* After that, binary messages carry the terminal's bytes both ways, exactly:
  what the caller types (UTF-8), mouse reports, and file transfer data one
  way; the BBS's output the other. No telnet reaches the page.

The BBS's side is telnet, which the bridge speaks as the client (Telnet,
below): it answers the BBS's option negotiation (terminal type "XTERMJS",
the window size, BINARY both ways, so transfers are 8-bit clean), doubles
0xFF in input, and takes telnet commands out of the output.

Run (it serves until stopped):

    python web/terminal_bridge.py [--listen 127.0.0.1:8023] [--bbs 127.0.0.1:23]

nginx proxies wss://inhahe.com/bbs-ws to it; see DOCS.md, "Web Terminal".
"""

from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
import logging
import logging.handlers
import re
import sys
from collections import Counter
from pathlib import Path

from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

log = logging.getLogger("terminal_bridge")

SUBPROTOCOL = "dirtyfork-terminal"
TERMINAL_TYPE = "XTERMJS"  # the BBS reads it as UTF-8, mouse, ZMODEM only
BUSY_TEXT = "\r\nToo many people are using the web terminal right now. Please try again later.\r\n"
DOWN_TEXT = "\r\nThe BBS is not answering right now. Please try again later.\r\n"
CONNECT_TIMEOUT_S = 10
# A socket must give its size this soon (the page sends it at once); until it
# does it holds a slot without a BBS session, whose own idle timeout would
# otherwise free it.
FIRST_MESSAGE_TIMEOUT_S = 10
MIN_COLS, MAX_COLS = 40, 400
MIN_ROWS, MAX_ROWS = 10, 200

# ---------------------------------------------------------------------------
# Telnet (client side)
# ---------------------------------------------------------------------------

IAC, DONT, DO, WONT, WILL, SB, SE = 255, 254, 253, 252, 251, 250, 240
CR, LF, NUL = 13, 10, 0
BINARY, ECHO, SGA, TTYPE, NAWS = 0, 1, 3, 24, 31
TTYPE_IS, TTYPE_SEND = 0, 1
# What we agree to: options we perform (the BBS asks DO), options it may
# perform (it offers WILL).
WE_WILL = {BINARY, SGA, TTYPE, NAWS}
THEY_MAY = {BINARY, SGA, ECHO}
MAX_SB = 1024  # a subnegotiation longer than this is not one we take


class Telnet:
    """The client half of telnet, without I/O: feed it what the BBS sends,
    get back the terminal's data and the replies to send; give it the
    terminal's input, get back the bytes to send.

    Commands split across reads are handled (the parser keeps its state).
    Options are answered once per change of state (RFC 1143's rule against
    negotiation loops): a request for what is already so gets no reply.
    """

    def __init__(self, terminal_type: str, cols: int, rows: int):
        self.terminal_type = terminal_type
        self.cols, self.rows = cols, rows
        self.local: set[int] = set()   # options we perform
        self.remote: set[int] = set()  # options the BBS performs
        self.state = "data"
        self.command = 0
        self.sb = bytearray()
        self.cr = False  # the BBS's last data byte was a CR (non-binary: CR NUL)

    # -- what the BBS sends -------------------------------------------------

    def receive(self, data: bytes) -> tuple[bytes, bytes]:
        """(terminal data, replies for the BBS) from bytes the BBS sent."""
        out, reply = bytearray(), bytearray()
        for b in data:
            state = self.state
            if state == "data":
                if b == IAC:
                    self.state = "iac"
                elif self.cr and b == NUL and BINARY not in self.remote:
                    self.cr = False  # (CR NUL is a bare CR)
                else:
                    self.cr = b == CR
                    out.append(b)
            elif state == "iac":
                if b == IAC:
                    out.append(IAC)
                    self.cr = False
                    self.state = "data"
                elif b in (WILL, WONT, DO, DONT):
                    self.command = b
                    self.state = "option"
                elif b == SB:
                    self.sb.clear()
                    self.state = "sb"
                else:
                    self.state = "data"  # NOP, GA, DM, AYT and the like
            elif state == "option":
                reply += self._negotiate(self.command, b)
                self.state = "data"
            elif state == "sb":
                if b == IAC:
                    self.state = "sb-iac"
                elif len(self.sb) < MAX_SB:
                    self.sb.append(b)
            elif state == "sb-iac":
                if b == SE:
                    reply += self._subnegotiation(bytes(self.sb))
                    self.state = "data"
                else:
                    if b == IAC and len(self.sb) < MAX_SB:
                        self.sb.append(IAC)
                    self.state = "sb"
        return bytes(out), bytes(reply)

    def _negotiate(self, command: int, option: int) -> bytes:
        if command == DO:
            if option in WE_WILL:
                if option in self.local:
                    return b""
                self.local.add(option)
                reply = bytes([IAC, WILL, option])
                if option == NAWS:
                    reply += self._naws()
                return reply
            return bytes([IAC, WONT, option])
        if command == DONT:
            if option in self.local:
                self.local.discard(option)
                return bytes([IAC, WONT, option])
            return b""
        if command == WILL:
            if option in THEY_MAY:
                if option in self.remote:
                    return b""
                self.remote.add(option)
                return bytes([IAC, DO, option])
            return bytes([IAC, DONT, option])
        # WONT
        if option in self.remote:
            self.remote.discard(option)
            return bytes([IAC, DONT, option])
        return b""

    def _subnegotiation(self, sb: bytes) -> bytes:
        if sb[:2] == bytes([TTYPE, TTYPE_SEND]) and TTYPE in self.local:
            return (bytes([IAC, SB, TTYPE, TTYPE_IS]) + self.terminal_type.encode("ascii")
                    + bytes([IAC, SE]))
        return b""

    def _naws(self) -> bytes:
        size = self.cols.to_bytes(2, "big") + self.rows.to_bytes(2, "big")
        return bytes([IAC, SB, NAWS]) + size.replace(b"\xff", b"\xff\xff") + bytes([IAC, SE])

    # -- what the terminal sends ---------------------------------------------

    def send(self, data: bytes) -> bytes:
        """The terminal's input as telnet: 0xFF doubled, and (until BINARY is
        agreed) a CR not followed by LF sent as CR NUL."""
        data = data.replace(b"\xff", b"\xff\xff")
        if BINARY not in self.local:
            data = _BARE_CR.sub(b"\r\0", data)
        return data


_BARE_CR = re.compile(rb"\r(?!\n)")


# ---------------------------------------------------------------------------
# The bridge
# ---------------------------------------------------------------------------


def host_port(text: str) -> tuple[str, int]:
    """'host:port' (or '[ipv6]:port') -> (host, port)."""
    host, sep, port = text.rpartition(":")
    if not sep or not host or not port.isdigit():
        raise argparse.ArgumentTypeError(f"expected HOST:PORT, got {text!r}")
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    return host, int(port)


def caller_address(ws: ServerConnection) -> str:
    """The caller's address: nginx's X-Real-IP when the connection comes from this
    machine (nginx), else the peer's own. Elsewhere the header could be forged."""
    peer = ws.remote_address[0] if ws.remote_address else "?"
    try:
        local = ipaddress.ip_address(peer).is_loopback
    except ValueError:
        local = False
    forwarded = ws.request.headers.get("X-Real-IP") if local and ws.request else None
    return forwarded or peer


def parse_size_message(msg) -> tuple[int, int]:
    """(cols, rows) from the page's first message; ValueError if it is not one."""
    if not isinstance(msg, str):
        raise ValueError("expected the terminal size first")
    obj = json.loads(msg)
    if not isinstance(obj, dict):
        raise ValueError("expected a JSON object")
    cols, rows = obj.get("cols"), obj.get("rows")
    if not (isinstance(cols, int) and isinstance(rows, int)
            and MIN_COLS <= cols <= MAX_COLS and MIN_ROWS <= rows <= MAX_ROWS):
        raise ValueError(f"unusable size {cols!r}x{rows!r}")
    return cols, rows


class Bridge:
    """Accepts web terminals and gives each its own telnet connection to the BBS.

    bbs: where the BBS listens, (host, port).
    max_clients: web terminals allowed at once; the next is told to try later.
    max_per_address: of those, how many may come from one address.
    first_message_timeout: seconds a socket may take to send its size.
    """

    def __init__(self, bbs: tuple[str, int], max_clients: int, max_per_address: int,
                 first_message_timeout: float = FIRST_MESSAGE_TIMEOUT_S):
        self.bbs = bbs
        self.max_clients = max_clients
        self.max_per_address = max_per_address
        self.first_message_timeout = first_message_timeout
        self.by_address: Counter[str] = Counter()

    async def handle(self, ws: ServerConnection) -> None:
        who = caller_address(ws)
        total = sum(self.by_address.values())
        if total >= self.max_clients or self.by_address[who] >= self.max_per_address:
            log.warning("%s turned away: %d web terminals connected, %d from this address",
                        who, total, self.by_address[who])
            try:
                await ws.send(BUSY_TEXT)
            except ConnectionClosed:
                return  # gone already
            await ws.close(1013, "too many users")  # 1013: try again later
            return
        self.by_address[who] += 1
        try:
            await _Session(self, ws, who).run()
        finally:
            self.by_address[who] -= 1
            if not self.by_address[who]:
                del self.by_address[who]


class _Session:
    """One web terminal and its telnet connection to the BBS."""

    def __init__(self, bridge: Bridge, ws: ServerConnection, who: str):
        self.bridge = bridge
        self.ws = ws
        self.who = who
        self.telnet: Telnet | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.pump: asyncio.Task | None = None

    async def run(self) -> None:
        try:
            try:
                first = await asyncio.wait_for(self.ws.recv(), self.bridge.first_message_timeout)
            except TimeoutError:
                log.info("%s said nothing; closed", self.who)
                await self.ws.close(1008, "no terminal size")
                return
            try:
                cols, rows = parse_size_message(first)
            except ValueError as exc:
                log.info("%s: bad first message: %s", self.who, exc)
                await self.ws.close(1008, "expected the terminal size")
                return
            self.telnet = Telnet(TERMINAL_TYPE, cols, rows)
            if not await self.connect(cols, rows):
                return
            async for msg in self.ws:
                if isinstance(msg, bytes):
                    self.writer.write(self.telnet.send(msg))
                    await self.writer.drain()
                # (text after the first message: nothing is defined; ignored)
        except ConnectionClosed:
            pass
        except OSError as exc:  # the BBS connection broke while sending to it
            log.info("%s: BBS connection lost: %s", self.who, exc)
        finally:
            await self.disconnect()
            log.info("%s left", self.who)

    async def connect(self, cols: int, rows: int) -> bool:
        """Open the BBS connection. On failure, tells the page and closes it."""
        try:
            reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(*self.bridge.bbs), CONNECT_TIMEOUT_S)
        except (OSError, TimeoutError) as exc:
            log.warning("%s: cannot reach the BBS at %s:%d: %s", self.who, *self.bridge.bbs, exc)
            try:
                await self.ws.send(DOWN_TEXT)
            except ConnectionClosed:
                pass
            await self.ws.close(1011, "BBS not answering")
            return False
        local = self.writer.get_extra_info("sockname")
        log.info("%s connected to the BBS (%dx%d, from local port %s)", self.who, cols, rows,
                 local[1] if local else "?")
        self.pump = asyncio.create_task(self._bbs_to_page(reader))
        return True

    async def _bbs_to_page(self, reader: asyncio.StreamReader) -> None:
        reason = "the BBS closed the connection"
        try:
            while data := await reader.read(65536):
                out, reply = self.telnet.receive(data)
                if reply:
                    self.writer.write(reply)
                    await self.writer.drain()
                if out:
                    await self.ws.send(out)
        except ConnectionClosed:
            return  # the page left; run() cleans up
        except OSError as exc:
            reason = "the connection to the BBS was lost"
            log.info("%s: %s: %s", self.who, reason, exc)
        else:
            log.info("%s: %s", self.who, reason)
        # The BBS side ended (the caller logged off, or the BBS went away): close
        # the page's socket too, so it can say so and offer to connect again.
        await self.ws.close(1000, reason)

    async def disconnect(self) -> None:
        pump, self.pump = self.pump, None
        writer, self.writer = self.writer, None
        if pump is not None:
            pump.cancel()
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="WebSocket-to-telnet bridge for the web terminal.")
    ap.add_argument("--listen", type=host_port, default=("127.0.0.1", 8023),
                    help="where to accept WebSockets (default 127.0.0.1:8023; nginx proxies to it)")
    ap.add_argument("--bbs", type=host_port, default=("127.0.0.1", 23),
                    help="the BBS's telnet address (default 127.0.0.1:23)")
    ap.add_argument("--max-clients", type=int, default=50,
                    help="web terminals allowed at once (default 50)")
    ap.add_argument("--max-per-address", type=int, default=4,
                    help="web terminals allowed at once from one address (default 4)")
    ap.add_argument("--origin", action="append", default=None, metavar="URL",
                    help="a page origin allowed to connect, e.g. https://inhahe.com; repeat for "
                         "several. Without any, every origin is allowed. A client that sends no "
                         "Origin (not a browser) is always allowed: it could claim any.")
    ap.add_argument("--log", type=Path, default=Path(__file__).with_name("terminal_bridge.log"),
                    help="log file (default web/terminal_bridge.log)")
    return ap.parse_args(argv)


def setup_logging(path: Path) -> None:
    handlers: list[logging.Handler] = [
        logging.handlers.RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")]
    if sys.stderr is not None:  # None under pythonw (the scheduled task)
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, handlers=handlers,
                        format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("websockets").setLevel(logging.WARNING)


def serve_bridge(bridge: Bridge, host: str, port: int, origins=None, process_request=None):
    """The WebSocket server for *bridge* (use as an async context manager).
    *process_request*: websockets' hook, to answer plain HTTP requests too
    (web/preview.py serves the page with it)."""
    return serve(bridge.handle, host, port, origins=origins, subprotocols=[SUBPROTOCOL],
                 process_request=process_request,
                 # Pings keep idle callers' connections open through nginx (and notice dead ones)
                 ping_interval=30, ping_timeout=30,
                 # Transfers send up to a few dozen KiB per message
                 max_size=1024 * 1024)


async def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    setup_logging(args.log)
    try:
        bridge = Bridge(args.bbs, args.max_clients, args.max_per_address)
        origins = args.origin + [None] if args.origin else None
        async with serve_bridge(bridge, *args.listen, origins=origins) as server:
            log.info("listening on %s:%d for web terminals; BBS at %s:%d", *args.listen, *args.bbs)
            await server.serve_forever()
    except Exception:
        # Under the scheduled task nobody sees stderr: say why in the log.
        log.exception("the bridge stopped")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
