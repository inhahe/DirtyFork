"""zmodem.py: framing, and whole transfers between our sender and receiver
over an in-memory pipe (which can damage what passes through it)."""
import asyncio
import os
import random
import tempfile
import time
import unittest
import zlib

import _setup  # noqa: F401  (puts the project on sys.path)
import zmodem
from zmodem import (CANFC32, CANFDX, CANOVIO, ZCRCE, ZCRCG, ZRINIT, ZRQINIT,
                    Encoder, Reader, Settings)


class Pipe:
    """One direction of an in-memory connection. *damage* (optional) is
    called with each write's bytes and the count written so far, and
    returns what actually arrives."""

    def __init__(self, damage=None):
        self.queue = asyncio.Queue()
        self.damage = damage
        self.written = 0
        self.closed = False

    def write(self, data):
        if self.damage:
            data = self.damage(bytes(data), self.written)
        self.written += len(data)
        if data:
            self.queue.put_nowait(bytes(data))

    def close(self):
        self.closed = True
        self.queue.put_nowait(b"")


class End:
    """A Link: reads one pipe, writes the other."""

    def __init__(self, inbound, outbound):
        self.inbound, self.outbound = inbound, outbound

    async def read(self):
        return await self.inbound.queue.get()

    def write(self, data):
        self.outbound.write(data)

    async def drain(self):
        await asyncio.sleep(0)


def connected(damage_to_receiver=None, damage_to_sender=None):
    """(sender's end, receiver's end)."""
    a = Pipe(damage_to_receiver)
    b = Pipe(damage_to_sender)
    return End(b, a), End(a, b)


class MemorySink:
    def __init__(self, store, name, limit=None):
        self.store, self.name, self.limit = store, name, limit
        self.data = bytearray()
        self.state = "open"

    def write(self, data):
        self.data += data
        if self.limit is not None and len(self.data) > self.limit:
            raise zmodem.TransferError("too big")

    def finish(self):
        self.state = "finished"
        self.store[self.name] = bytes(self.data)

    def discard(self):
        self.state = "discarded"


FAST = Settings(start_timeout=5, header_timeout=0.5, retries=6)


def run(coro):
    return asyncio.run(asyncio.wait_for(coro, 60))


class Framing(unittest.TestCase):
    def test_hex_headers_match_lrzsz(self):
        # What lrzsz's sz sends to start, and its rz's ZRINIT (CANFDX|CANOVIO|CANFC32)
        self.assertEqual(Encoder.hex_header(ZRQINIT), b"**\x18B00000000000000\r\x8a\x11")
        self.assertEqual(Encoder.hex_header(ZRINIT, zmodem.flag_bytes(f0=0x23)),
                         b"**\x18B0100000023be50\r\x8a\x11")

    def decode(self, wire, crc32):
        async def go():
            pipe = Pipe()
            pipe.write(wire)
            return await Reader(End(pipe, Pipe())).subpacket(crc32, 5)
        return asyncio.run(go())

    def test_every_byte_survives_a_subpacket(self):
        data = bytes(range(256)) * 3
        for escape_ctrl in (False, True):
            for crc32 in (False, True):
                enc = Encoder(escape_ctrl)
                wire = enc.subpacket(data, ZCRCG, crc32)
                # Nothing that must be escaped appears raw (ZDLE pairs skipped)
                must = {0x0D, 0x10, 0x11, 0x13, 0x8D, 0x90, 0x91, 0x93}
                if escape_ctrl:
                    must |= {b for b in range(256) if not b & 0x60}
                i = 0
                while i < len(wire):
                    if wire[i] == 0x18:
                        i += 2
                        continue
                    self.assertNotIn(wire[i], must, (escape_ctrl, crc32, i))
                    i += 1
                self.assertEqual(self.decode(wire, crc32), (data, ZCRCG))

    def test_a_damaged_subpacket_is_refused(self):
        wire = bytearray(Encoder().subpacket(b"hello world", ZCRCE, True))
        wire[3] ^= 0x01
        with self.assertRaises(zmodem._BadFrame):
            self.decode(bytes(wire), True)

    def test_headers_in_every_format_round_trip(self):
        async def go():
            enc = Encoder(escape_ctrl=True)
            data = bytes([0x18, 0x11, 0xff, 0x0d])
            pipe = Pipe()
            pipe.write(b"noise before**garbage" + Encoder.hex_header(zmodem.ZRPOS, data)
                       + enc.bin_header(zmodem.ZDATA, data, False)
                       + enc.bin_header(zmodem.ZEOF, data, True))
            reader = Reader(End(pipe, Pipe()))
            return [await reader.header(5) for _ in range(3)]
        hdrs = asyncio.run(go())
        self.assertEqual([(h.type, h.data, h.crc32) for h in hdrs],
                         [(zmodem.ZRPOS, bytes([0x18, 0x11, 0xff, 0x0d]), False),
                          (zmodem.ZDATA, bytes([0x18, 0x11, 0xff, 0x0d]), False),
                          (zmodem.ZEOF, bytes([0x18, 0x11, 0xff, 0x0d]), True)])

    def test_a_subpacket_right_after_a_hex_header_keeps_its_first_byte(self):
        """A nonconforming sender's hex ZDATA, then data starting with LF
        (not escaped): only the header's own CR LF XON may be taken."""
        async def go():
            pipe = Pipe()
            pipe.write(Encoder.hex_header(zmodem.ZDATA, zmodem.pos_bytes(0))
                       + Encoder().subpacket(b"\nline", ZCRCE, False))
            reader = Reader(End(pipe, Pipe()))
            hdr = await reader.header(5)
            return await reader.subpacket(hdr.crc32, 5)
        self.assertEqual(asyncio.run(go()), (b"\nline", ZCRCE))

    def test_an_endless_subpacket_of_escaped_bytes_is_refused(self):
        async def go():
            pipe = Pipe()
            pipe.write(b"\x18\x41" * 20000)  # (ZDLE + 'A': the byte 1, escaped, 20000 times)
            await Reader(End(pipe, Pipe())).subpacket(False, 2, max_len=8192)
        with self.assertRaises(zmodem._BadFrame):
            asyncio.run(go())

    def test_a_big_buffer_of_escaped_data_decodes_quickly(self):
        """Reading from the front of a megabyte buffer must not copy the rest
        each time (it did: an upload crawled, stalling every session)."""
        enc = Encoder(escape_ctrl=True)
        rng = random.Random(5)
        packets = [rng.randbytes(8192) for _ in range(256)]  # 2 MiB, a quarter escaped
        wire = b"".join(enc.subpacket(p, ZCRCG, True) for p in packets)

        async def go():
            pipe = Pipe()
            pipe.write(wire)
            reader = Reader(End(pipe, Pipe()))
            return [(await reader.subpacket(True, 10))[0] for _ in packets]
        started = time.monotonic()
        got = asyncio.run(asyncio.wait_for(go(), 30))
        self.assertEqual(got, packets)
        self.assertLess(time.monotonic() - started, 10)

    def test_five_cans_abort(self):
        async def go():
            pipe = Pipe()
            pipe.write(b"**\x18" + b"\x18" * 5)
            await Reader(End(pipe, Pipe())).header(5)
        with self.assertRaises(zmodem.Aborted):
            asyncio.run(go())

    def test_file_info(self):
        info = zmodem.encode_file_info("café.zip", 1234, 0o1234567, files_left=2, bytes_left=5000)
        offer = zmodem.parse_file_info(info)
        self.assertEqual((offer.name, offer.size, offer.mtime, offer.files_left, offer.bytes_left),
                         ("café.zip", 1234, 0o1234567, 2, 5000))
        self.assertEqual(zmodem.parse_file_info(b"\x82t\xe9.txt\x00").name, "étΘ.txt")
        self.assertEqual(zmodem.parse_file_info(b"bare\x00").size, None)


class Transfers(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="zmodem-test-")
        self.rng = random.Random(1234)

    def tearDown(self):
        for name in os.listdir(self.dir):
            os.remove(os.path.join(self.dir, name))
        os.rmdir(self.dir)

    def make(self, name, size):
        path = os.path.join(self.dir, name)
        data = bytes(range(256)) + self.rng.randbytes(max(0, size - 256))
        with open(path, "wb") as f:
            f.write(data[:size])
        return path, data[:size]

    def transfer(self, paths, accept=None, damage_to_receiver=None, damage_to_sender=None,
                 settings=FAST, max_files=100):
        """Send *paths* from our sender to our receiver. Returns (sender's
        results or exception, receiver's results or exception, files stored)."""
        store, sinks = {}, []

        def default_accept(offer):
            sink = MemorySink(store, offer.name)
            sinks.append(sink)
            return sink

        async def go():
            s_end, r_end = connected(damage_to_receiver, damage_to_sender)
            return await asyncio.gather(
                zmodem.send_files(s_end, paths, settings),
                zmodem.receive_files(r_end, accept or default_accept, settings, max_files),
                return_exceptions=True)
        sent, received = run(go())
        self.sinks = sinks
        return sent, received, store

    def test_files_of_every_awkward_size_arrive_whole(self):
        files = [self.make(f"f{n}.bin", n) for n in (0, 1, 1023, 1024, 1025, 70000)]
        sent, received, store = self.transfer([p for p, _ in files])
        self.assertEqual([r.status for r in sent], ["sent"] * 6)
        self.assertEqual([r.status for r in received], ["received"] * 6)
        for path, data in files:
            self.assertEqual(store[os.path.basename(path)], data)

    def test_damage_on_the_line_is_repaired(self):
        path, data = self.make("big.bin", 50000)
        hits = {9000, 21000, 33333}

        def damage(chunk, offset):
            chunk = bytearray(chunk)
            for at in hits:
                if offset <= at < offset + len(chunk):
                    chunk[at - offset] ^= 0x55
            return bytes(chunk)
        with self.assertLogs("dirtyfork.zmodem", "INFO") as logs:
            sent, received, store = self.transfer([path], damage_to_receiver=damage)
        self.assertEqual(received[0].status, "received")
        self.assertEqual(store["big.bin"], data)
        self.assertGreaterEqual(sum("again" in line for line in logs.output), 2, logs.output)

    def test_a_lost_stretch_is_sent_again(self):
        path, data = self.make("lost.bin", 30000)

        def damage(chunk, offset):
            # The 10th..11th KiB of the stream never arrive
            lo, hi = 10240, 11264
            keep = bytes(b for i, b in enumerate(chunk) if not lo <= offset + i < hi)
            return keep
        with self.assertLogs("dirtyfork.zmodem", "INFO") as logs:
            sent, received, store = self.transfer([path], damage_to_receiver=damage)
        self.assertEqual(store["lost.bin"], data)
        self.assertTrue(any("again" in line for line in logs.output), logs.output)

    def test_more_repairs_than_retries_each_further_on_still_finish(self):
        """A long file over a noisy line: what limits the sender's errors is
        how many come in a row, without the receiver getting further."""
        path, data = self.make("noisy.bin", 120000)
        hits = range(8000, 160000, 15000)  # (offsets in all that is sent, again included)

        def damage(chunk, offset):
            chunk = bytearray(chunk)
            for at in hits:
                if offset <= at < offset + len(chunk):
                    chunk[at - offset] ^= 0x55
            return bytes(chunk)
        settings = Settings(start_timeout=5, header_timeout=0.5, retries=2)
        with self.assertLogs("dirtyfork.zmodem", "INFO") as logs:
            sent, received, store = self.transfer([path], damage_to_receiver=damage,
                                                  settings=settings)
        self.assertNotIsInstance(sent, Exception, repr(sent))
        self.assertEqual([r.status for r in sent], ["sent"])
        self.assertEqual(store["noisy.bin"], data)
        restarts = sum("asked for the data again" in line for line in logs.output)
        self.assertGreater(restarts, settings.retries, logs.output)

    def test_a_receiver_that_gets_no_further_is_given_up_on(self):
        """From 20000 on everything it is sent is damaged, so it asks for the
        same place again and again: the sender stops after its retries."""
        path, _ = self.make("stuck.bin", 60000)

        def damage(chunk, offset):
            if offset + len(chunk) <= 20000:
                return chunk
            chunk = bytearray(chunk)
            chunk[len(chunk) // 2] ^= 0x55  # (in the abort sequence, after its CANs)
            return bytes(chunk)

        async def go():
            s_end, r_end = connected(damage_to_receiver=damage)
            return await asyncio.gather(
                zmodem.send_files(s_end, [path], Settings(start_timeout=5, header_timeout=0.5,
                                                          retries=3)),
                zmodem.receive_files(r_end, lambda offer: MemorySink({}, offer.name),
                                     Settings(start_timeout=5, header_timeout=0.5, retries=50)),
                return_exceptions=True)
        sent, received = run(go())
        self.assertIs(type(sent), zmodem.TransferError, repr(sent))
        self.assertEqual(str(sent), "too many errors")

    def test_a_receiver_without_32_bit_crcs_gets_16_bit_ones(self):
        path, data = self.make("crc16.bin", 9000)
        original = zmodem._Receiver.__init__

        def crc16_only(self, *args, **kwargs):
            original(self, *args, **kwargs)
            self.zrinit = Encoder.hex_header(ZRINIT, zmodem.flag_bytes(f0=CANFDX | CANOVIO))
        zmodem._Receiver.__init__ = crc16_only
        headers = []
        original_header = Reader.header

        async def spy(reader, timeout):
            hdr = await original_header(reader, timeout)
            headers.append(hdr)
            return hdr
        Reader.header = spy
        try:
            sent, received, store = self.transfer([path])
        finally:
            zmodem._Receiver.__init__ = original
            Reader.header = original_header
        self.assertEqual(store["crc16.bin"], data)
        data_headers = [h for h in headers if h.type == zmodem.ZDATA]
        self.assertTrue(data_headers and not any(h.crc32 for h in data_headers))

    def test_a_skipped_file_is_reported_and_the_next_still_comes(self):
        a, _ = self.make("skip-me.bin", 5000)
        b, data_b = self.make("keep.bin", 5000)
        store = {}

        def accept(offer):
            return None if offer.name == "skip-me.bin" else MemorySink(store, offer.name)
        sent, received, _ = self.transfer([a, b], accept=accept)
        self.assertEqual([r.status for r in sent], ["skipped", "sent"])
        self.assertEqual([r.status for r in received], ["skipped", "received"])
        self.assertEqual(store, {"keep.bin": data_b})

    def test_no_more_than_max_files_are_taken(self):
        files = [self.make(f"n{i}.bin", 10)[0] for i in range(3)]
        sent, received, store = self.transfer(files, max_files=2)
        self.assertEqual([r.status for r in received], ["received", "received", "skipped"])
        self.assertEqual(sorted(store), ["n0.bin", "n1.bin"])

    def test_a_sink_that_refuses_stops_the_transfer(self):
        path, _ = self.make("huge.bin", 40000)
        store = {}
        sinks = []

        def accept(offer):
            sinks.append(MemorySink(store, offer.name, limit=10000))
            return sinks[-1]
        sent, received, _ = self.transfer([path], accept=accept)
        self.assertIsInstance(received, zmodem.TransferError)
        self.assertIsInstance(sent, zmodem.Aborted)
        self.assertEqual(sinks[0].state, "discarded")
        self.assertEqual(store, {})

    def test_cancelling_midway_discards_the_partial_file(self):
        path, _ = self.make("cancel.bin", 200000)

        def damage(chunk, offset):
            # The caller presses Ctrl+X five times partway through
            return chunk + b"\x18" * 5 if offset < 20000 <= offset + len(chunk) else chunk
        sent, received, store = self.transfer([path], damage_to_receiver=damage)
        self.assertIsInstance(received, zmodem.Aborted)
        self.assertEqual(self.sinks[0].state, "discarded")
        self.assertEqual(store, {})

    def test_a_silent_sender_times_out(self):
        async def go():
            _, r_end = connected()
            await zmodem.receive_files(r_end, lambda o: None,
                                       Settings(start_timeout=1, header_timeout=0.2, retries=3))
        with self.assertRaises(zmodem.TimedOut):
            run(go())

    def test_a_silent_receiver_times_out(self):
        path, _ = self.make("x.bin", 10)

        async def go():
            s_end, _ = connected()
            await zmodem.send_files(s_end, [path],
                                    Settings(start_timeout=1, header_timeout=0.2, retries=3))
        with self.assertRaises(zmodem.TimedOut):
            run(go())

    def test_cancelling_while_the_sender_is_blocked_ends_it(self):
        """The receiver stops reading (its window is full, say) and the caller
        presses Ctrl+X five times: the sender, stuck waiting for its data to
        leave, must still notice and stop."""
        path, _ = self.make("blocked.bin", 300000)

        class Stuck(End):
            def __init__(self, *args):
                super().__init__(*args)
                self.blocked = asyncio.Event()

            async def drain(self):
                if self.outbound.written > 40000:
                    self.blocked.set()
                    await asyncio.Event().wait()  # never drains again

        async def go():
            a, b = Pipe(), Pipe()
            sender = Stuck(b, a)
            task = asyncio.create_task(zmodem.send_files(sender, [path], FAST))
            # Answer as a receiver would, then cancel once the sender is stuck
            b.write(Encoder.hex_header(ZRINIT, zmodem.flag_bytes(f0=CANFDX | CANOVIO | CANFC32)))
            while True:
                data = await a.queue.get()
                if b"\x18C\x04" in data or b"\x18A\x04" in data:  # its ZFILE
                    break
            b.write(Encoder.hex_header(zmodem.ZRPOS, zmodem.pos_bytes(0)))
            await asyncio.wait_for(sender.blocked.wait(), 10)
            b.write(b"\x18" * 5)
            await asyncio.wait_for(task, 5)
        with self.assertRaises(zmodem.Aborted):
            run(go())

    def test_a_receiver_that_stops_reading_times_out(self):
        path, _ = self.make("stalled.bin", 100000)

        class NeverDrains(End):
            async def drain(self):
                await asyncio.Event().wait()

        async def go():
            a, b = Pipe(), Pipe()
            b.write(Encoder.hex_header(ZRINIT, zmodem.flag_bytes(f0=CANFDX | CANOVIO | CANFC32)))
            await zmodem.send_files(NeverDrains(b, a), [path],
                                    Settings(start_timeout=2, header_timeout=0.5, retries=3,
                                             stall_timeout=0.5))
        with self.assertRaises(zmodem.TimedOut):
            run(go())

    def test_getting_back_in_step_through_much_data_in_flight(self):
        """A damaged subpacket, then 300 KiB the sender had already sent before
        it saw our request to send again (no header in it, now and then a false
        start of one): none of that may count as errors."""
        enc = Encoder()
        rng = random.Random(9)
        first, second = rng.randbytes(8192), rng.randbytes(8192)
        damaged = bytearray(enc.subpacket(second, ZCRCG, True))
        damaged[100] ^= 0x01
        in_flight = b"".join(enc.subpacket(rng.randbytes(8192), ZCRCG, True) for _ in range(38))
        in_flight += b"*\x18C" + b"\x00" * 9  # (a false header start)
        info = zmodem.encode_file_info("resync.bin", 2 * 8192, 0)
        stream = (enc.bin_header(zmodem.ZFILE, zmodem.flag_bytes(f0=zmodem.ZCBIN), True)
                  + enc.subpacket(info, zmodem.ZCRCW, True)
                  + enc.bin_header(zmodem.ZDATA, zmodem.pos_bytes(0), True)
                  + enc.subpacket(first, ZCRCG, True) + bytes(damaged) + in_flight
                  + enc.bin_header(zmodem.ZDATA, zmodem.pos_bytes(8192), True)
                  + enc.subpacket(second, ZCRCE, True)
                  + enc.bin_header(zmodem.ZEOF, zmodem.pos_bytes(2 * 8192), True)
                  + Encoder.hex_header(zmodem.ZFIN) + b"OO")
        store = {}

        async def go():
            a, b = Pipe(), Pipe()
            a.write(stream)  # (the sender's side, all at once)
            return await zmodem.receive_files(End(a, b), lambda o: MemorySink(store, o.name), FAST)
        results = run(go())
        self.assertEqual([r.status for r in results], ["received"])
        self.assertEqual(store["resync.bin"], first + second)

    def test_a_sender_that_never_starts_times_out_however_much_it_says(self):
        """It repeats ZRQINIT (it never hears our ZRINIT): the start timeout
        must still end the session."""
        async def go():
            a, b = Pipe(), Pipe()

            async def nag():
                while True:
                    a.write(Encoder.hex_header(ZRQINIT))
                    await asyncio.sleep(0.1)
            nagging = asyncio.create_task(nag())
            try:
                await zmodem.receive_files(End(a, b), lambda o: None,
                                           Settings(start_timeout=1, header_timeout=0.5, retries=3))
            finally:
                nagging.cancel()
        started = time.monotonic()
        with self.assertRaises(zmodem.TimedOut):
            run(go())
        self.assertLess(time.monotonic() - started, 5)

    def test_a_receiver_asking_for_the_file_crc_is_answered(self):
        path, data = self.make("crc.bin", 50000)

        async def go():
            a, b = Pipe(), Pipe()
            sender = End(b, a)
            receiver = Reader(End(a, Pipe()))
            task = asyncio.create_task(zmodem.send_files(sender, [path], FAST))
            b.write(Encoder.hex_header(ZRINIT, zmodem.flag_bytes(f0=CANFDX | CANOVIO | CANFC32)))
            while (await receiver.header(5)).type != zmodem.ZFILE:
                pass
            b.write(Encoder.hex_header(zmodem.ZCRC))
            while True:
                hdr = await receiver.header(5)
                if hdr.type == zmodem.ZCRC:
                    break
            b.write(Encoder.hex_header(zmodem.ZSKIP))
            b.write(Encoder.hex_header(zmodem.ZFIN))
            await asyncio.wait_for(task, 10)
            return hdr.pos
        self.assertEqual(run(go()), zlib.crc32(data) & 0xFFFFFFFF)

    def test_a_receiver_with_a_small_buffer_gets_acknowledged_windows(self):
        path, data = self.make("windowed.bin", 20000)
        original = zmodem._Receiver.__init__

        def small_buffer(self, *args, **kwargs):
            original(self, *args, **kwargs)
            # 4 KiB buffer, and no overlapped I/O: the sender must wait for ZACKs
            self.zrinit = Encoder.hex_header(ZRINIT, bytes([0x00, 0x10, 0, CANFDX | CANFC32]))
        zmodem._Receiver.__init__ = small_buffer
        try:
            sent, received, store = self.transfer([path])
        finally:
            zmodem._Receiver.__init__ = original
        self.assertEqual(store["windowed.bin"], data)


if __name__ == "__main__":
    unittest.main()
