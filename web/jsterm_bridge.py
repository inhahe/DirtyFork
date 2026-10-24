"""WebSocket-to-telnet bridge for the jsTerm web terminal.

A web page cannot open a TCP connection, so the BBS's web terminal (jsTerm,
served as inhahe.com/bbs.html) talks WebSocket to this bridge, and the bridge
talks telnet to the BBS. It only ever connects to the one BBS it was started
for: the host and port the page names are ignored, so nobody can use it to
reach anything else.

jsTerm's protocol (its src/telnet/Socket.js and Session.js):

* When its socket opens, the page sends one text message, "telnet|<host>|<port>",
  and the bridge connects to the BBS. Only a socket's first message is read this
  way; to connect again the page opens a new socket.
* Every other message is input, as text whose characters are bytes
  (U+0000..U+00FF): a key at a time, or a paste in pieces.
* The bridge forwards what the BBS sends as text messages whose characters are
  its bytes (Latin-1); the page reads them back with charCodeAt.

Telnet negotiation passes through untouched: jsTerm answers the BBS itself.

Run (it serves until stopped):

    python web/jsterm_bridge.py [--listen 127.0.0.1:8023] [--bbs 127.0.0.1:23]

nginx proxies wss://inhahe.com/bbs-ws to it; see DOCS.md, "Web Terminal".
"""

from __future__ import annotations

import argparse
import asyncio
import ipaddress
import logging
import logging.handlers
import re
import sys
from collections import Counter
from pathlib import Path

from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

log = logging.getLogger("jsterm_bridge")

# The page's first message: where to connect (ignored, but it must be this shape
# to be taken as a request rather than as input).
CONNECT_RE = re.compile(r"telnet\|[^|]*\|\d*")

BUSY_TEXT = "\r\nToo many people are using the web terminal right now. Please try again later.\r\n"
DOWN_TEXT = "\r\nThe BBS is not answering right now. Please try again later.\r\n"
CONNECT_TIMEOUT_S = 10
# A socket must say something this soon (jsTerm sends its connect request at
# once); until it does it holds a slot without a BBS session, whose own idle
# timeout would otherwise free it.
FIRST_MESSAGE_TIMEOUT_S = 10


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


class Bridge:
    """Accepts web terminals and gives each its own telnet connection to the BBS.

    bbs: where the BBS listens, (host, port).
    max_clients: web terminals allowed at once; the next is told to try later.
    max_per_address: of those, how many may come from one address.
    first_message_timeout: seconds a socket may stay silent before it is closed.
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
            await ws.send(BUSY_TEXT)
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
    """One web terminal and its connection to the BBS."""

    def __init__(self, bridge: Bridge, ws: ServerConnection, who: str):
        self.bridge = bridge
        self.ws = ws
        self.who = who
        self.writer: asyncio.StreamWriter | None = None
        self.pump: asyncio.Task | None = None

    async def run(self) -> None:
        try:
            try:
                first = await asyncio.wait_for(self.ws.recv(), self.bridge.first_message_timeout)
            except TimeoutError:
                log.info("%s said nothing; closed", self.who)
                await self.ws.close(1008, "no request")
                return
            if not await self.connect():
                return
            if not CONNECT_RE.fullmatch(_text(first)):
                await self.forward(first)  # input before any request: connect, then send it
            async for msg in self.ws:
                await self.forward(msg)
        except ConnectionClosed:
            pass
        except OSError as exc:  # the BBS connection broke while sending to it
            log.info("%s: BBS connection lost: %s", self.who, exc)
        finally:
            await self.disconnect()
            log.info("%s left", self.who)

    async def forward(self, msg: str | bytes) -> None:
        self.writer.write(_text(msg).encode("latin-1", "replace"))
        await self.writer.drain()

    async def connect(self) -> bool:
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
        log.info("%s connected to the BBS (from local port %s)", self.who, local[1] if local else "?")
        self.pump = asyncio.create_task(self._bbs_to_page(reader))
        return True

    async def _bbs_to_page(self, reader: asyncio.StreamReader) -> None:
        reason = "the BBS closed the connection"
        try:
            while data := await reader.read(65536):
                await self.ws.send(data.decode("latin-1"))
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


def _text(msg: str | bytes) -> str:
    return msg.decode("latin-1") if isinstance(msg, bytes) else msg


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="WebSocket-to-telnet bridge for the jsTerm web terminal.")
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
    ap.add_argument("--log", type=Path, default=Path(__file__).with_name("jsterm_bridge.log"),
                    help="log file (default web/jsterm_bridge.log)")
    return ap.parse_args(argv)


def setup_logging(path: Path) -> None:
    handlers: list[logging.Handler] = [
        logging.handlers.RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")]
    if sys.stderr is not None:  # None under pythonw (the scheduled task)
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, handlers=handlers,
                        format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("websockets").setLevel(logging.WARNING)


async def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    setup_logging(args.log)
    try:
        bridge = Bridge(args.bbs, args.max_clients, args.max_per_address)
        origins = args.origin + [None] if args.origin else None
        # Pings keep idle callers' connections open through nginx (and notice dead ones).
        async with serve(bridge.handle, *args.listen, origins=origins, ping_interval=30,
                         ping_timeout=30, max_size=64 * 1024) as server:
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
