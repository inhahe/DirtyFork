"""web/terminal_bridge.py: the web terminal's WebSocket-to-telnet bridge.

The telnet client (Telnet) on its own, and the bridge against a fake BBS."""
import asyncio
import json
import os
import sys
import unittest
from unittest import mock

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, InvalidStatus, NegotiationError

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web"))
import terminal_bridge as tb  # noqa: E402
from terminal_bridge import (BINARY, DO, DONT, ECHO, IAC, NAWS, SB, SE, SGA, TTYPE, WILL,  # noqa: E402
                             WONT)

SIZE = json.dumps({"cols": 100, "rows": 40})


def cmd(*b):
    return bytes(b)


class TelnetClient(unittest.TestCase):
    def setUp(self):
        self.t = tb.Telnet("XTERMJS", 100, 40)

    def test_answers_what_the_bbs_asks(self):
        data, reply = self.t.receive(
            cmd(IAC, DO, TTYPE, IAC, DO, NAWS, IAC, WILL, ECHO, IAC, WILL, SGA, IAC, DO, BINARY,
                IAC, WILL, BINARY, IAC, DO, 39, IAC, WILL, 99))
        self.assertEqual(data, b"")
        self.assertEqual(reply, cmd(IAC, WILL, TTYPE)
                         + cmd(IAC, WILL, NAWS, IAC, SB, NAWS, 0, 100, 0, 40, IAC, SE)
                         + cmd(IAC, DO, ECHO, IAC, DO, SGA, IAC, WILL, BINARY, IAC, DO, BINARY)
                         + cmd(IAC, WONT, 39, IAC, DONT, 99))

    def test_asking_again_for_what_is_so_gets_no_answer(self):
        self.t.receive(cmd(IAC, DO, BINARY, IAC, WILL, ECHO))
        self.assertEqual(self.t.receive(cmd(IAC, DO, BINARY, IAC, WILL, ECHO)), (b"", b""))
        # and turning off: answered once
        self.assertEqual(self.t.receive(cmd(IAC, DONT, BINARY))[1], cmd(IAC, WONT, BINARY))
        self.assertEqual(self.t.receive(cmd(IAC, DONT, BINARY))[1], b"")

    def test_terminal_type_even_when_the_request_is_split(self):
        self.t.receive(cmd(IAC, DO, TTYPE))
        parts = [b"he", cmd(IAC, SB, TTYPE), cmd(1, IAC), cmd(SE) + b"llo"]
        data, reply = b"", b""
        for part in parts:
            d, r = self.t.receive(part)
            data, reply = data + d, reply + r
        self.assertEqual(data, b"hello")
        self.assertEqual(reply, cmd(IAC, SB, TTYPE, 0) + b"XTERMJS" + cmd(IAC, SE))

    def test_every_byte_value_both_ways(self):
        self.t.receive(cmd(IAC, DO, BINARY, IAC, WILL, BINARY))
        everything = bytes(range(256))
        wire = everything.replace(b"\xff", b"\xff\xff")
        out = b""
        for i in range(len(wire)):  # one byte at a time: IAC IAC split too
            out += self.t.receive(wire[i:i + 1])[0]
        self.assertEqual(out, everything)
        self.assertEqual(self.t.send(everything), wire)

    def test_a_width_of_255_is_escaped_in_naws(self):
        t = tb.Telnet("XTERMJS", 255, 40)
        reply = t.receive(cmd(IAC, DO, NAWS))[1]
        self.assertEqual(reply, cmd(IAC, WILL, NAWS, IAC, SB, NAWS, 0, 255, 255, 0, 40, IAC, SE))

    def test_bare_carriage_returns_before_binary(self):
        self.assertEqual(self.t.send(b"a\rb\r\nc\r"), b"a\r\0b\r\nc\r\0")
        self.assertEqual(self.t.receive(b"x\r\0y\r\nz")[0], b"x\ry\r\nz")
        self.t.receive(cmd(IAC, DO, BINARY, IAC, WILL, BINARY))
        self.assertEqual(self.t.send(b"a\rb"), b"a\rb")
        self.assertEqual(self.t.receive(b"x\r\0y")[0], b"x\r\0y")


class FakeBBS:
    """A telnet server that records each connection: what it received, and lets
    a test send to it or hang up."""

    def __init__(self):
        self.conns = []
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


async def recv_bytes(ws, n):
    """Binary messages from the bridge until `n` bytes have come."""
    got = b""
    while len(got) < n:
        msg = await asyncio.wait_for(ws.recv(), 5)
        got += msg if isinstance(msg, bytes) else msg.encode("latin-1")
    return got


def page(url, **kwargs):
    """Connect as the page does."""
    return connect(url, subprotocols=[tb.SUBPROTOCOL], **kwargs)


class BridgeTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bbs = FakeBBS()
        await self.bbs.start()
        await self.start_bridge(("127.0.0.1", self.bbs.port))

    async def start_bridge(self, bbs_address, max_clients=50, max_per_address=50, origins=None,
                           first_message_timeout=tb.FIRST_MESSAGE_TIMEOUT_S):
        self.bridge = tb.Bridge(bbs_address, max_clients, max_per_address, first_message_timeout)
        self.server = await tb.serve_bridge(self.bridge, "127.0.0.1", 0, origins=origins)
        self.url = f"ws://127.0.0.1:{self.server.sockets[0].getsockname()[1]}/"

    async def restart_bridge(self, **kwargs):
        self.server.close()
        await self.server.wait_closed()
        await self.start_bridge(("127.0.0.1", self.bbs.port), **kwargs)

    async def slots_freed(self):
        """Wait for the bridge to give back every slot: its handler finishes a
        moment after the client sees the socket close."""
        for _ in range(100):
            if not self.bridge.by_address:
                return
            await asyncio.sleep(0.05)
        self.fail(f"slots still held: {dict(self.bridge.by_address)}")

    async def asyncTearDown(self):
        self.server.close()
        await self.server.wait_closed()
        await self.bbs.stop()

    async def test_negotiates_for_the_page_and_carries_bytes(self):
        async with page(self.url) as ws:
            await ws.send(SIZE)
            reader, writer = await self.bbs.next_conn(1)
            writer.write(cmd(IAC, DO, TTYPE, IAC, DO, NAWS, IAC, SB, TTYPE, 1, IAC, SE) + b"hello")
            await writer.drain()
            self.assertEqual(await recv_bytes(ws, 5), b"hello")  # no telnet reaches the page
            expected = (cmd(IAC, WILL, TTYPE, IAC, WILL, NAWS, IAC, SB, NAWS, 0, 100, 0, 40, IAC, SE)
                        + cmd(IAC, SB, TTYPE, 0) + b"XTERMJS" + cmd(IAC, SE))
            self.assertEqual(await asyncio.wait_for(reader.readexactly(len(expected)), 5), expected)
            # Typed text (UTF-8) and a raw 0xFF (a mouse report's byte): the 0xFF doubled
            await ws.send("é\xff".encode("utf-8") + b"\xff")
            self.assertEqual(await asyncio.wait_for(reader.readexactly(6), 5),
                             b"\xc3\xa9\xc3\xbf\xff\xff")

    async def test_every_byte_value_passes_both_ways(self):
        everything = bytes(range(256))
        async with page(self.url) as ws:
            await ws.send(SIZE)
            reader, writer = await self.bbs.next_conn(1)
            writer.write(cmd(IAC, DO, BINARY, IAC, WILL, BINARY))
            await writer.drain()
            self.assertEqual(await asyncio.wait_for(reader.readexactly(6), 5),
                             cmd(IAC, WILL, BINARY, IAC, DO, BINARY))
            writer.write(everything.replace(b"\xff", b"\xff\xff"))
            await writer.drain()
            self.assertEqual(await recv_bytes(ws, 256), everything)
            await ws.send(everything)
            self.assertEqual(await asyncio.wait_for(reader.readexactly(257), 5),
                             everything.replace(b"\xff", b"\xff\xff"))

    async def test_a_page_without_the_subprotocol_is_refused(self):
        with self.assertRaises((InvalidStatus, NegotiationError)):
            async with connect(self.url) as ws:
                await ws.send(SIZE)
                await asyncio.wait_for(ws.recv(), 5)
        self.assertEqual(self.bbs.conns, [])

    async def test_the_first_message_must_be_a_usable_size(self):
        for first in ('{"cols": 80}', '{"cols": 9999, "rows": 25}', "telnet|bbs|23", b"\x00",
                      '[80, 25]', '{"cols": "80", "rows": 25}'):
            async with page(self.url) as ws:
                await ws.send(first)
                with self.assertRaises(ConnectionClosed):
                    await asyncio.wait_for(ws.recv(), 5)
                self.assertEqual(ws.close_code, 1008, first)
        self.assertEqual(self.bbs.conns, [])
        await self.slots_freed()

    async def test_bbs_hanging_up_closes_the_page(self):
        async with page(self.url) as ws:
            await ws.send(SIZE)
            _, writer = await self.bbs.next_conn(1)
            writer.write(b"bye")
            await writer.drain()
            writer.close()
            self.assertEqual(await recv_bytes(ws, 3), b"bye")
            with self.assertRaises(ConnectionClosed):
                await asyncio.wait_for(ws.recv(), 5)
            self.assertEqual(ws.close_code, 1000)

    async def test_page_leaving_closes_the_bbs_connection(self):
        async with page(self.url) as ws:
            await ws.send(SIZE)
            reader, _ = await self.bbs.next_conn(1)
        self.assertEqual(await asyncio.wait_for(reader.read(), 5), b"")

    async def test_bbs_down_is_explained(self):
        self.server.close()
        await self.server.wait_closed()
        await self.bbs.stop()
        await self.start_bridge(("127.0.0.1", self.bbs.port))  # nothing listens there now
        self.bbs = FakeBBS()
        await self.bbs.start()  # for tearDown
        async with page(self.url) as ws:
            await ws.send(SIZE)
            self.assertEqual(await asyncio.wait_for(ws.recv(), 15), tb.DOWN_TEXT)
            with self.assertRaises(ConnectionClosed):
                await asyncio.wait_for(ws.recv(), 5)
            self.assertEqual(ws.close_code, 1011)

    async def test_too_many_web_terminals_are_turned_away(self):
        await self.restart_bridge(max_clients=1)
        async with page(self.url) as first:
            await first.send(SIZE)
            await self.bbs.next_conn(1)
            async with page(self.url) as second:
                self.assertEqual(await asyncio.wait_for(second.recv(), 5), tb.BUSY_TEXT)
                with self.assertRaises(ConnectionClosed):
                    await asyncio.wait_for(second.recv(), 5)
                self.assertEqual(second.close_code, 1013)
        self.assertEqual(len(self.bbs.conns), 1)

    async def test_one_address_cannot_take_every_slot(self):
        await self.restart_bridge(max_per_address=1)
        # Through nginx (a loopback peer), the caller is X-Real-IP.
        async with page(self.url, additional_headers={"X-Real-IP": "203.0.113.5"}) as first:
            await first.send(SIZE)
            await self.bbs.next_conn(1)
            async with page(self.url, additional_headers={"X-Real-IP": "203.0.113.5"}) as again:
                self.assertEqual(await asyncio.wait_for(again.recv(), 5), tb.BUSY_TEXT)
            async with page(self.url, additional_headers={"X-Real-IP": "198.51.100.7"}) as other:
                await other.send(SIZE)
                await self.bbs.next_conn(2)
        await self.slots_freed()

    async def test_a_silent_socket_is_closed(self):
        await self.restart_bridge(first_message_timeout=0.3)
        async with page(self.url) as ws:
            with self.assertRaises(ConnectionClosed):
                await asyncio.wait_for(ws.recv(), 5)
            self.assertEqual(ws.close_code, 1008)
        self.assertEqual(self.bbs.conns, [])
        await self.slots_freed()

    async def test_bbs_connection_error_closes_the_page(self):
        # Reading from the BBS fails, not ends (on Windows even a reset usually
        # reads as an orderly end, so the error is made here).
        real_open = asyncio.open_connection
        fail = asyncio.Event()

        async def open_then_fail(*args, **kwargs):
            reader, writer = await real_open(*args, **kwargs)

            async def read(n=-1):
                await fail.wait()
                raise ConnectionResetError(10054, "An existing connection was forcibly closed")
            reader.read = read
            return reader, writer

        with mock.patch.object(tb.asyncio, "open_connection", open_then_fail):
            async with page(self.url) as ws:
                await ws.send(SIZE)
                await self.bbs.next_conn(1)
                fail.set()
                with self.assertRaises(ConnectionClosed):
                    await asyncio.wait_for(ws.recv(), 5)
                self.assertEqual(ws.close_code, 1000)
                self.assertEqual(ws.close_reason, "the connection to the BBS was lost")

    async def test_origins_other_than_the_sites_are_refused(self):
        await self.restart_bridge(origins=["https://inhahe.com", None])
        with self.assertRaises(InvalidStatus):
            async with page(self.url, origin="https://evil.example"):
                pass
        async with page(self.url, origin="https://inhahe.com") as ws:
            await ws.send(SIZE)
            await self.bbs.next_conn(1)
        async with page(self.url) as ws:  # no Origin: not a browser
            await ws.send(SIZE)
            await self.bbs.next_conn(2)


class HostPortTest(unittest.TestCase):
    def test_parsing(self):
        self.assertEqual(tb.host_port("127.0.0.1:23"), ("127.0.0.1", 23))
        self.assertEqual(tb.host_port("[::1]:23"), ("::1", 23))
        for bad in ("23", "host:", ":23", "host:x"):
            with self.assertRaises(Exception):
                tb.host_port(bad)


if __name__ == "__main__":
    unittest.main()
