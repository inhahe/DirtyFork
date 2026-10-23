"""web/jsterm_bridge.py: the web terminal's WebSocket-to-telnet bridge, against a fake BBS."""
import asyncio
import os
import sys
import unittest

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web"))
import jsterm_bridge  # noqa: E402


class FakeBBS:
    """A telnet server that records each connection: what it received, and lets
    a test send to it or hang up."""

    def __init__(self):
        self.conns: list[tuple[asyncio.StreamReader, asyncio.StreamWriter]] = []
        self.arrived = asyncio.Event()

    async def start(self):
        self.server = await asyncio.start_server(self._accept, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]

    async def _accept(self, reader, writer):
        self.conns.append((reader, writer))
        self.arrived.set()

    async def next_conn(self, count):
        """Wait until `count` connections have arrived; return the last."""
        while len(self.conns) < count:
            self.arrived.clear()
            await asyncio.wait_for(self.arrived.wait(), 5)
        return self.conns[count - 1]

    async def stop(self):
        for _, w in self.conns:
            w.close()
        self.server.close()
        await self.server.wait_closed()


async def recv_text(ws, n):
    """Messages from the bridge until `n` characters have come."""
    got = ""
    while len(got) < n:
        got += await asyncio.wait_for(ws.recv(), 5)
    return got


class BridgeTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bbs = FakeBBS()
        await self.bbs.start()
        await self.start_bridge(("127.0.0.1", self.bbs.port))

    async def start_bridge(self, bbs_address, max_clients=50):
        self.bridge = jsterm_bridge.Bridge(bbs_address, max_clients)
        self.server = await serve(self.bridge.handle, "127.0.0.1", 0)
        self.url = f"ws://127.0.0.1:{self.server.sockets[0].getsockname()[1]}/"

    async def asyncTearDown(self):
        self.server.close()
        await self.server.wait_closed()
        await self.bbs.stop()

    async def test_connects_only_to_its_own_bbs(self):
        async with connect(self.url) as ws:
            await ws.send("telnet|smtp.example.com|25")
            reader, _ = await self.bbs.next_conn(1)
            await ws.send("x")
            self.assertEqual(await asyncio.wait_for(reader.readexactly(1), 5), b"x")

    async def test_every_byte_value_passes_both_ways(self):
        everything = bytes(range(256))
        async with connect(self.url) as ws:
            await ws.send("telnet|bbs|23")
            reader, writer = await self.bbs.next_conn(1)
            writer.write(everything)  # IAC (255) and all, untouched
            await writer.drain()
            text = await recv_text(ws, 256)
            self.assertEqual([ord(c) for c in text], list(range(256)))
            await ws.send(everything.decode("latin-1"))  # how jsTerm sends bytes
            self.assertEqual(await asyncio.wait_for(reader.readexactly(256), 5), everything)

    async def test_characters_beyond_a_byte_become_question_marks(self):
        async with connect(self.url) as ws:
            await ws.send("telnet|bbs|23")
            reader, _ = await self.bbs.next_conn(1)
            await ws.send("a☺b")
            self.assertEqual(await asyncio.wait_for(reader.readexactly(3), 5), b"a?b")

    async def test_input_before_connecting_connects_first(self):
        async with connect(self.url) as ws:
            await ws.send("hi")
            reader, _ = await self.bbs.next_conn(1)
            self.assertEqual(await asyncio.wait_for(reader.readexactly(2), 5), b"hi")

    async def test_connect_again_replaces_the_bbs_connection(self):
        async with connect(self.url) as ws:
            await ws.send("telnet|bbs|23")
            first_reader, _ = await self.bbs.next_conn(1)
            await ws.send("telnet|bbs|23")
            second_reader, _ = await self.bbs.next_conn(2)
            self.assertEqual(await asyncio.wait_for(first_reader.read(), 5), b"")  # closed
            await ws.send("z")
            self.assertEqual(await asyncio.wait_for(second_reader.readexactly(1), 5), b"z")

    async def test_bbs_hanging_up_closes_the_page(self):
        async with connect(self.url) as ws:
            await ws.send("telnet|bbs|23")
            _, writer = await self.bbs.next_conn(1)
            writer.write(b"bye")
            await writer.drain()
            writer.close()
            self.assertEqual(await recv_text(ws, 3), "bye")
            with self.assertRaises(ConnectionClosed):
                await asyncio.wait_for(ws.recv(), 5)
            self.assertEqual(ws.close_code, 1000)

    async def test_page_leaving_closes_the_bbs_connection(self):
        async with connect(self.url) as ws:
            await ws.send("telnet|bbs|23")
            reader, _ = await self.bbs.next_conn(1)
        self.assertEqual(await asyncio.wait_for(reader.read(), 5), b"")

    async def test_bbs_down_is_explained(self):
        self.server.close()
        await self.server.wait_closed()
        await self.bbs.stop()
        await self.start_bridge(("127.0.0.1", self.bbs.port))  # nothing listens there now
        self.bbs = FakeBBS()
        await self.bbs.start()  # for tearDown
        async with connect(self.url) as ws:
            await ws.send("telnet|bbs|23")
            self.assertEqual(await asyncio.wait_for(ws.recv(), 15), jsterm_bridge.DOWN_TEXT)
            with self.assertRaises(ConnectionClosed):
                await asyncio.wait_for(ws.recv(), 5)
            self.assertEqual(ws.close_code, 1011)

    async def test_too_many_web_terminals_are_turned_away(self):
        self.server.close()
        await self.server.wait_closed()
        await self.start_bridge(("127.0.0.1", self.bbs.port), max_clients=1)
        async with connect(self.url) as first:
            await first.send("telnet|bbs|23")
            await self.bbs.next_conn(1)
            async with connect(self.url) as second:
                self.assertEqual(await asyncio.wait_for(second.recv(), 5), jsterm_bridge.BUSY_TEXT)
                with self.assertRaises(ConnectionClosed):
                    await asyncio.wait_for(second.recv(), 5)
                self.assertEqual(second.close_code, 1013)
        self.assertEqual(len(self.bbs.conns), 1)


class HostPortTest(unittest.TestCase):
    def test_parsing(self):
        self.assertEqual(jsterm_bridge.host_port("127.0.0.1:23"), ("127.0.0.1", 23))
        self.assertEqual(jsterm_bridge.host_port("[::1]:23"), ("::1", 23))
        for bad in ("23", "host:", ":23", "host:x"):
            with self.assertRaises(Exception):
                jsterm_bridge.host_port(bad)

    def test_connect_messages(self):
        self.assertTrue(jsterm_bridge.CONNECT_RE.fullmatch("telnet|inhahe.com|23"))
        self.assertTrue(jsterm_bridge.CONNECT_RE.fullmatch("telnet||"))
        self.assertFalse(jsterm_bridge.CONNECT_RE.fullmatch("t"))
        self.assertFalse(jsterm_bridge.CONNECT_RE.fullmatch("telnet|a|b|c"))


if __name__ == "__main__":
    unittest.main()
