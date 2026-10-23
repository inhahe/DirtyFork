"""WebSocket-to-telnet bridge for the jsTerm web terminal.

A web page cannot open a TCP connection, so the BBS's web terminal (jsTerm,
served as inhahe.com/bbs.html) talks WebSocket to this bridge, and the bridge
talks telnet to the BBS. It only ever connects to the one BBS it was started
for: the host and port the page names are ignored, so nobody can use it to
reach anything else.

jsTerm's protocol (its src/telnet/Socket.js and Session.js):

* When the socket opens, and on every Connect after that, the page sends one
  text message, "telnet|<host>|<port>". The bridge (re)opens its connection to
  the BBS.
* Every other message is input, as text whose characters are bytes
  (U+0000..U+00FF), usually one key per message.
* The bridge forwards what the BBS sends as text messages whose characters are
  its bytes (Latin-1); the page reads them back with charCodeAt.

Telnet negotiation passes through untouched: jsTerm answers the BBS itself.

Run (it serves until stopped):

    python web/jsterm_bridge.py [--listen 127.0.0.1:8023] [--bbs 127.0.0.1:23]

nginx proxies wss://inhahe.com/bbs-ws to it; see DOCS.md, "Web access".
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import logging.handlers
import re
import sys
from pathlib import Path

from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

log = logging.getLogger("jsterm_bridge")

# What jsTerm sends to (re)connect. Keyboard input arrives a key at a time, so
# input can only look like this if a user pastes it, which jsTerm cannot do.
CONNECT_RE = re.compile(r"telnet\|[^|]*\|\d*")

BUSY_TEXT = "\r\nToo many people are using the web terminal right now. Please try again later.\r\n"
DOWN_TEXT = "\r\nThe BBS is not answering right now. Please try again later.\r\n"
CONNECT_TIMEOUT_S = 10


def host_port(text: str) -> tuple[str, int]:
    """'host:port' (or '[ipv6]:port') -> (host, port)."""
    host, sep, port = text.rpartition(":")
    if not sep or not host or not port.isdigit():
        raise argparse.ArgumentTypeError(f"expected HOST:PORT, got {text!r}")
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    return host, int(port)


class Bridge:
    """Accepts web terminals and gives each its own telnet connection to the BBS.

    bbs: where the BBS listens, (host, port).
    max_clients: how many web terminals may be connected at once; the next one
    is told to try later and closed.
    """

    def __init__(self, bbs: tuple[str, int], max_clients: int):
        self.bbs = bbs
        self.max_clients = max_clients
        self.clients = 0

    async def handle(self, ws: ServerConnection) -> None:
        # nginx passes the caller's address on; a direct connection has its own.
        who = ws.request.headers.get("X-Real-IP") if ws.request else None
        who = who or (ws.remote_address[0] if ws.remote_address else "?")
        if self.clients >= self.max_clients:
            log.warning("%s turned away: %d web terminals already connected", who, self.clients)
            await ws.send(BUSY_TEXT)
            await ws.close(1013, "too many users")  # 1013: try again later
            return
        self.clients += 1
        try:
            await _Session(self.bbs, ws, who).run()
        finally:
            self.clients -= 1


class _Session:
    """One web terminal and its current connection to the BBS (none until it asks)."""

    def __init__(self, bbs: tuple[str, int], ws: ServerConnection, who: str):
        self.bbs = bbs
        self.ws = ws
        self.who = who
        self.writer: asyncio.StreamWriter | None = None
        self.pump: asyncio.Task | None = None

    async def run(self) -> None:
        try:
            async for msg in self.ws:
                if isinstance(msg, bytes):
                    msg = msg.decode("latin-1")
                if CONNECT_RE.fullmatch(msg):
                    if not await self.connect():
                        return
                    continue
                if self.writer is None and not await self.connect():
                    return  # input before any connect: connect first
                self.writer.write(msg.encode("latin-1", "replace"))
                await self.writer.drain()
        except ConnectionClosed:
            pass
        except OSError as exc:  # the BBS connection broke while sending to it
            log.info("%s: BBS connection lost: %s", self.who, exc)
        finally:
            await self.disconnect()
            log.info("%s left", self.who)

    async def connect(self) -> bool:
        """(Re)open the BBS connection. On failure, tells the page and closes it."""
        await self.disconnect()
        try:
            reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(*self.bbs), CONNECT_TIMEOUT_S)
        except (OSError, TimeoutError) as exc:
            log.warning("%s: cannot reach the BBS at %s:%d: %s", self.who, *self.bbs, exc)
            try:
                await self.ws.send(DOWN_TEXT)
                await self.ws.close(1011, "BBS not answering")
            except ConnectionClosed:
                pass
            return False
        log.info("%s connected to the BBS", self.who)
        self.pump = asyncio.create_task(self._bbs_to_page(reader))
        return True

    async def _bbs_to_page(self, reader: asyncio.StreamReader) -> None:
        try:
            while data := await reader.read(65536):
                await self.ws.send(data.decode("latin-1"))
        except (ConnectionClosed, OSError):
            return
        # The BBS hung up (the caller logged off): close the page's socket too,
        # so it can say so and offer to connect again.
        log.info("%s: the BBS closed the connection", self.who)
        try:
            await self.ws.close(1000, "the BBS closed the connection")
        except ConnectionClosed:
            pass

    async def disconnect(self) -> None:
        pump, self.pump = self.pump, None
        writer, self.writer = self.writer, None
        if pump is not None and pump is not asyncio.current_task():
            pump.cancel()
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="WebSocket-to-telnet bridge for the jsTerm web terminal.")
    ap.add_argument("--listen", type=host_port, default=("127.0.0.1", 8023),
                    help="where to accept WebSockets (default 127.0.0.1:8023; nginx proxies to it)")
    ap.add_argument("--bbs", type=host_port, default=("127.0.0.1", 23),
                    help="the BBS's telnet address (default 127.0.0.1:23)")
    ap.add_argument("--max-clients", type=int, default=50,
                    help="web terminals allowed at once (default 50)")
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
    bridge = Bridge(args.bbs, args.max_clients)
    # Pings keep idle callers' connections open through nginx (and notice dead ones).
    async with serve(bridge.handle, *args.listen, ping_interval=30, ping_timeout=30,
                     max_size=64 * 1024) as server:
        log.info("listening on %s:%d for web terminals; BBS at %s:%d", *args.listen, *args.bbs)
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
