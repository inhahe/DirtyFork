"""modem.py against a simulated modem (tests/fake_modem.py) on the real
pyserial-asyncio transport: setting the modem up, answering, the caller's
input and output, flow control at the line's speed, noticing a hang-up,
hanging up, a port that fails, answering one call at a time, and a ZMODEM
download over the line."""
import asyncio
import os
import tempfile
import threading
import unittest
from unittest import mock

import _setup  # noqa: F401
import modem
import zmodem
from fake_modem import FakeModem, plugged_in

PORT = "COM9"
# (shorter waits than a real modem needs, to keep the tests quick)
QUICK = dict(COMMAND_TIMEOUT=0.3, CARRIER_POLL=0.05, DTR_DROP=0.1, GUARD_TIME=0.25,
             RETRY=0.05, SETTLE=0.05)


def run(coro, timeout=30):
    """Run *coro* in an event loop of its own, in a thread: a test that stops
    the loop (as a port polled without end would) fails instead of hanging."""
    outcome = {}

    def report(loop, context):
        if "serial transport" not in context.get("message", ""):  # (a failing port's own)
            loop.default_exception_handler(context)

    def go():
        loop = asyncio.new_event_loop()
        loop.set_exception_handler(report)
        try:
            outcome["value"] = loop.run_until_complete(coro)
        except BaseException as exc:
            outcome["error"] = exc
        finally:
            loop.close()
    thread = threading.Thread(target=go, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise AssertionError(f"the event loop was still busy after {timeout} s")
    if "error" in outcome:
        raise outcome["error"]
    return outcome.get("value")


async def call(fake, init="ATZ"):
    """wait_for_call on *fake*, which rings once it has been set up."""
    return await asyncio.wait_for(modem.wait_for_call(PORT, 115200, init, ready=fake.ring), 10)


async def stop(task):
    """Cancel *task* and wait until it has finished (its hang-up included)."""
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def eventually(condition, timeout=5.0):
    """Wait until condition() is true (or fail)."""
    loop = asyncio.get_running_loop()
    end = loop.time() + timeout
    while not condition():
        if loop.time() > end:
            raise AssertionError("it did not happen in time")
        await asyncio.sleep(0.01)


@unittest.skipUnless(os.name == "nt", "pyserial-asyncio waits on a file descriptor here, "
                                      "which the simulated port has not got")
class Modem(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.multiple(modem, **QUICK)
        patcher.start()
        self.addCleanup(patcher.stop)

    def connected(self, fake, then, init="ATZ"):
        """Answer a call on *fake*, then run then(reader, writer)."""
        async def go():
            reader, writer = await call(fake, init)
            try:
                return await then(reader, writer)
            finally:
                writer.close()
                await writer.wait_closed()
        with plugged_in({PORT: fake}):
            return run(go())

    # -- setting up and answering ----------------------------------------

    def test_the_modem_is_set_up_and_a_call_answered(self):
        fake = FakeModem()

        async def then(reader, writer):
            writer.write("Welcome ░")  # (CP437 until the session chooses)
            await writer.drain()
            fake.type(b"y")
            return await reader.read(1)
        key = self.connected(fake, then, init="AT&F")
        self.assertEqual(fake.commands[:3], ["AT&F", modem.SETUP, "ATA"])
        self.assertTrue(fake.open_options["rtscts"])
        self.assertEqual(bytes(fake.to_caller), b"Welcome \xb0")
        self.assertEqual(key, "y")

    def test_a_modem_that_answers_nothing_is_reported(self):
        fake = FakeModem(results=False)

        async def go():
            waiting = asyncio.ensure_future(modem.wait_for_call(PORT, 115200, "ATZ"))
            await eventually(lambda: len(fake.commands) == 2)
            await stop(waiting)
        with self.assertLogs("dirtyfork", "WARNING") as logs, plugged_in({PORT: fake}):
            run(go())
        self.assertIn("no answer to ATZ", logs.output[0])

    def test_after_a_failed_answer_the_next_ring_is_answered(self):
        fake = FakeModem(answers=False)

        async def go():
            waiting = asyncio.ensure_future(modem.wait_for_call(PORT, 115200, "ATZ", ready=fake.ring))
            await eventually(lambda: "ATH" in fake.commands)
            fake.answers = True
            fake.ring()
            reader, writer = await asyncio.wait_for(waiting, 5)
            writer.close()
            await writer.wait_closed()
        with self.assertLogs("dirtyfork", "WARNING") as logs, plugged_in({PORT: fake}):
            run(go())
        self.assertEqual(fake.commands[2:], ["ATA", "ATH", "ATA"])
        self.assertIn("answered, but no connection (NO CARRIER)", logs.output[0])

    def test_the_line_speed_comes_from_connect(self):
        self.assertEqual(modem.line_speed("CONNECT 33600/ARQ/V34/LAPM/V42BIS"), 33600)
        self.assertEqual(modem.line_speed("CONNECT 2400"), 2400)
        self.assertEqual(modem.line_speed("CONNECT"), 300)

    # -- a port that fails --------------------------------------------------

    def test_a_port_that_fails_while_waiting_for_a_call_is_an_error_at_once(self):
        """Not a quiet line: read as one, the wait for RING went round at full
        speed without letting anything else run (the whole BBS stopped)."""
        fake = FakeModem()

        async def go():
            waiting = asyncio.ensure_future(modem.wait_for_call(PORT, 115200, "ATZ",
                                                                ready=fake.unplug))
            with self.assertRaises(modem.ModemGone):
                await asyncio.wait_for(waiting, 5)
        with plugged_in({PORT: fake}):
            run(go(), timeout=15)

    # -- during a call --------------------------------------------------------

    def test_the_callers_hang_up_ends_the_input_without_the_modems_words(self):
        fake = FakeModem()

        async def then(reader, writer):
            fake.type(b"a")
            first = await reader.read(10)
            fake.hang_up()  # (the carrier drops, and the modem says NO CARRIER)
            return first, await asyncio.wait_for(reader.read(10), 5)
        self.assertEqual(self.connected(fake, then), ("a", ""))

    def test_a_quiet_hang_up_ends_a_read_that_is_waiting(self):
        fake = FakeModem()

        async def then(reader, writer):
            reading = asyncio.ensure_future(reader.read(10))
            await asyncio.sleep(0.1)
            fake.hang_up(quietly=True)
            return await asyncio.wait_for(reading, 5)
        self.assertEqual(self.connected(fake, then), "")

    def test_a_modem_that_shows_no_carrier_is_reported_and_its_calls_go_on(self):
        fake = FakeModem(dcd=False)

        async def then(reader, writer):
            await asyncio.sleep(0.5)
            fake.type(b"k")
            return await asyncio.wait_for(reader.read(1), 5)
        with self.assertLogs("dirtyfork", "WARNING") as logs:
            key = self.connected(fake, then)
        self.assertEqual(key, "k")
        self.assertTrue(any("shows no carrier" in line for line in logs.output), logs.output)

    def test_drain_leaves_about_a_second_of_output_queued(self):
        """At 2400 bps: the port takes any amount at once, and pyserial-asyncio
        buffers 64 KiB more before its drain waits, minutes at this speed."""
        fake = FakeModem(connect="CONNECT 2400", cps=240)

        async def then(reader, writer):
            writer.write(b"x" * 4096)
            with self.assertRaises(asyncio.TimeoutError):
                await asyncio.wait_for(writer.drain(), 0.5)
            queued = len(fake.unsent)
            fake.cps = None  # (now the line takes it all)
            await asyncio.wait_for(writer.drain(), 5)
            return queued
        self.assertGreater(self.connected(fake, then), 3000)
        self.assertEqual(bytes(fake.to_caller), b"x" * 4096)

    def test_drain_stops_when_the_caller_hangs_up(self):
        fake = FakeModem(connect="CONNECT 2400", cps=240)

        async def then(reader, writer):
            writer.write(b"x" * 4096)
            draining = asyncio.ensure_future(writer.drain())
            await asyncio.sleep(0.1)
            fake.hang_up()
            with self.assertRaises(ConnectionResetError):
                await asyncio.wait_for(draining, 5)
        self.connected(fake, then)

    # -- hanging up -------------------------------------------------------------

    def test_hanging_up_waits_for_the_output_then_drops_dtr(self):
        fake = FakeModem(connect="CONNECT 33600", cps=4000)

        async def then(reader, writer):
            writer.write(b"Goodbye! " * 200)  # (half a second of the line)
        self.connected(fake, then)
        self.assertEqual(bytes(fake.to_caller), b"Goodbye! " * 200)
        self.assertEqual(fake.dtr_drops, [0])  # (dropped once, with nothing left to send)
        self.assertFalse(fake.carrier)
        self.assertFalse(fake.is_open)
        self.assertNotIn("ATH", fake.commands)

    def test_a_modem_that_ignores_dtr_is_hung_up_with_ath(self):
        fake = FakeModem(follows_dtr=False, guard=0.2)

        async def then(reader, writer):
            pass
        self.connected(fake, then)
        self.assertEqual(fake.commands[-1], "ATH")
        self.assertFalse(fake.carrier)
        self.assertEqual(bytes(fake.to_caller), b"")  # (the +++ was not taken for data)

    def test_closing_hangs_up_too(self):
        """The BBS closes connections itself (at shutdown, a second login,
        logout): a modem's close() hangs up as well."""
        fake = FakeModem()

        async def go():
            reader, writer = await call(fake)
            writer.close()
            writer.write("ignored")  # (closed: written nowhere)
            await writer.wait_closed()
        with plugged_in({PORT: fake}):
            run(go())
        self.assertEqual(fake.dtr_drops, [0])
        self.assertFalse(fake.carrier)

    # -- answering calls, one at a time -------------------------------------------

    def test_listen_answers_one_call_at_a_time(self):
        """While a call goes on the port stays the session's: it is opened
        again, and the modem set up again, only after the hang-up."""
        fake = FakeModem()
        sessions = []

        async def session(reader, writer):
            sessions.append(fake.opened)
            fake.type(b"q")
            await reader.read(1)
            await asyncio.sleep(0.3)  # (a call going on)

        async def go():
            listening = asyncio.ensure_future(modem.listen(PORT, 115200, "ATZ", session))
            await eventually(lambda: fake.opened == 1 and fake.commands[-1:] == [modem.SETUP])
            fake.ring()
            await eventually(lambda: fake.opened == 2 and fake.commands[-1:] == [modem.SETUP])
            fake.ring()
            await eventually(lambda: len(sessions) == 2)
            await stop(listening)
        with plugged_in({PORT: fake}):
            run(go())
        self.assertEqual(sessions, [1, 2])
        self.assertEqual(fake.commands[:6], ["ATZ", modem.SETUP, "ATA"] * 2)
        self.assertEqual(len(fake.dtr_drops), 2)  # (each call hung up)

    def test_a_port_that_cannot_be_opened_is_reported_once_and_tried_again(self):
        fake = FakeModem()
        fake.broken = True

        async def go():
            listening = asyncio.ensure_future(modem.listen(PORT, 115200, "ATZ", None))
            await asyncio.sleep(0.4)  # (several attempts)
            fake.broken = False
            await eventually(lambda: fake.opened == 1)
            await asyncio.sleep(0.1)
            await stop(listening)
        with self.assertLogs("dirtyfork", "INFO") as logs, plugged_in({PORT: fake}):
            run(go())
        errors = [line for line in logs.output if line.startswith("ERROR")]
        self.assertEqual(len(errors), 1, logs.output)
        self.assertIn("could not open port", errors[0])
        self.assertTrue(any("working again" in line for line in logs.output), logs.output)

    # -- a file transfer over the line ---------------------------------------------

    def test_a_zmodem_download_over_the_line(self):
        """Our sender over the session's reader and writer (in Latin-1, as
        file_transfer switches them), our receiver at the caller's end."""
        fake = FakeModem(connect="CONNECT 33600", cps=20000)
        data = bytes(range(256)) * 64 + os.urandom(20000)
        folder = tempfile.mkdtemp(prefix="modem-test-")
        path = os.path.join(folder, "over-the-line.bin")
        with open(path, "wb") as f:
            f.write(data)
        received = {}

        class Session:  # (the BBS's end, as file_transfer's link)
            def __init__(self, reader, writer):
                self.reader, self.writer = reader, writer

            async def read(self):
                return (await self.reader.read(1 << 20)).encode("latin-1")

            def write(self, data):
                self.writer.write(bytes(data).decode("latin-1"))

            async def drain(self):
                await self.writer.drain()

        class Caller:  # (the caller's end of the line)
            async def read(self):
                while not fake.to_caller:
                    fake.out_waiting  # (lets the line move on)
                    await asyncio.sleep(0.005)
                out = bytes(fake.to_caller)
                fake.to_caller.clear()
                return out

            def write(self, data):
                fake.type(bytes(data))

            async def drain(self):
                pass

        class Sink:
            def __init__(self, name):
                self.name, self.data = name, bytearray()

            def write(self, chunk):
                self.data += chunk

            def finish(self):
                received[self.name] = bytes(self.data)

            def discard(self):
                pass

        async def then(reader, writer):
            reader.set_encoding("latin-1")
            writer.set_encoding("latin-1")
            settings = zmodem.Settings(start_timeout=10, header_timeout=2, drain_every=1024)
            return await asyncio.gather(
                zmodem.send_files(Session(reader, writer), [path], settings),
                zmodem.receive_files(Caller(), lambda offer: Sink(offer.name), settings))
        try:
            sent, got = self.connected(fake, then)
        finally:
            os.remove(path)
            os.rmdir(folder)
        self.assertEqual([r.status for r in sent], ["sent"])
        self.assertEqual(received["over-the-line.bin"], data)


class SerialReader(unittest.TestCase):
    def test_a_character_split_across_reads_is_whole(self):
        class Line:  # (a StreamReader: a box-drawing character in UTF-8, in two reads)
            chunks = [b"\xe2\x94", b"\x80!"]

            async def read(self, n):
                return self.chunks.pop(0) if self.chunks else b""
        reader = modem.SerialReader(Line(), encoding="utf-8")
        self.assertEqual(run(reader.read(10)), "─!")

    def test_a_timed_out_read_is_a_timeout_not_a_hang_up(self):
        class Silent:  # (a line on which nothing arrives)
            async def read(self, n):
                await asyncio.Event().wait()

        async def go():
            return await asyncio.wait_for(modem.SerialReader(Silent()).read(10), 0.1)
        with self.assertRaises(asyncio.TimeoutError):
            run(go())


if __name__ == "__main__":
    unittest.main()
