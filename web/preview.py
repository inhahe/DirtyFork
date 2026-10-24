"""Serve the web terminal page (web/site) and its bridge on one local port,
to try the page without nginx: what the page fetches comes from web/site,
and /bbs-ws is the bridge (web/terminal_bridge.py).

    python web/preview.py [--port 8099] [--bbs 127.0.0.1:23]

then open http://127.0.0.1:8099/bbs.html (or bbs-local.html). It listens on
127.0.0.1 only and serves web/site read-only, nothing outside it.
"""

import argparse
import asyncio
import logging
import sys
from http import HTTPStatus
from pathlib import Path
from urllib.parse import unquote

from websockets.datastructures import Headers
from websockets.http11 import Response

sys.path.insert(0, str(Path(__file__).parent))
import terminal_bridge as tb  # noqa: E402

SITE = Path(__file__).with_name("site").resolve()
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".woff": "font/woff", ".txt": "text/plain; charset=utf-8"}


def static(connection, request):
    """websockets' process_request: a file from web/site for a plain GET; None
    (go on with the WebSocket handshake) for /bbs-ws."""
    path = unquote(request.path.split("?", 1)[0])
    if path == "/bbs-ws":
        return None
    file = (SITE / (path.lstrip("/") or "bbs.html")).resolve()
    if SITE not in file.parents or not file.is_file():
        return connection.respond(HTTPStatus.NOT_FOUND, "Not found\n")
    body = file.read_bytes()
    headers = Headers({"Content-Type": TYPES.get(file.suffix, "application/octet-stream"),
                       "Content-Length": str(len(body)), "Cache-Control": "no-store"})
    return Response(200, "OK", headers, body)


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--bbs", type=tb.host_port, default=("127.0.0.1", 23),
                    help="the BBS's telnet address (default 127.0.0.1:23)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("websockets").setLevel(logging.WARNING)
    bridge = tb.Bridge(args.bbs, max_clients=10, max_per_address=10)
    async with tb.serve_bridge(bridge, "127.0.0.1", args.port, process_request=static) as server:
        print(f"http://127.0.0.1:{args.port}/bbs.html  (BBS at {args.bbs[0]}:{args.bbs[1]})", flush=True)
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
