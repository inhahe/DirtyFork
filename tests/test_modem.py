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
             RETRY=0.05, SETTLE=0.05, FLUSH_LIMIT=1.0, HANGUP_WAIT=1.0)


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
        self.assertEqual(fake.commands[:6], ["AT&F", *modem.SETUP, "ATA"])
        self.assertTrue(fake.open_options["rtscts"])
        self.assertEqual(bytes(fake.to_caller), b"Welcome \xb0")
        self.assertEqual(key, "y")

    def test_a_modem_that_answers_nothing_is_reported(self):
        fake = FakeModem(results=False)

        async def go():
            waiting = asyncio.ensure_future(modem.wait_for_call(PORT, 115200, "ATZ"))
            await eventually(lambda: len(fake.commands) == 1 + len(modem.SETUP))
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
        self.assertEqual(fake.commands[1 + len(modem.SETUP):], ["ATA", "ATH", "ATA"])
        self.assertIn("answered, but no connection (NO CARRIER)", logs.output[0])

    def test_the_line_speed_comes_from_carrier_or_connect(self):
        self.assertEqual(modem.line_speed("CONNECT 33600/ARQ/V34/LAPM/V42BIS"), 33600)
        self.assertEqual(modem.line_speed("CONNECT 2400"), 2400)
        self.assertEqual(modem.line_speed("CONNECT"), 300)
        # (many modems give the computer's speed in CONNECT, the line's in CARRIER)
        self.assertEqual(modem.line_speed("CONNECT 115200", "CARRIER 2400"), 2400)
        self.assertEqual(modem.line_speed("CONNECT 115200"), modem.ANALOG_TOP)

    def test_a_carrier_message_sets_the_pace(self):
        """CONNECT 115200 (the computer's speed) after CARRIER 2400: drain
        keeps to 2400 bps, not to 115200's 11 KiB a second."""
        fake = FakeModem(carrier="CARRIER 2400", connect="CONNECT 115200", cps=240)

        async def then(reader, writer):
            writer.write(b"x" * 2048)  # (8 s at 2400 bps; under a second at 33,600)
            with self.assertRaises(asyncio.TimeoutError):
                await asyncio.wait_for(writer.drain(), 0.5)
            fake.cps = None
        self.connected(fake, then)

    def test_a_distinctive_ring_is_answered(self):
        fake = FakeModem()

        async def go():
            ready = lambda: fake.ring("RING 1")  # noqa: E731
            reader, writer = await asyncio.wait_for(
                modem.wait_for_call(PORT, 115200, "ATZ", ready=ready), 5)
            writer.close()
            await writer.wait_closed()
        with plugged_in({PORT: fake}):
            run(go())
        self.assertIn("ATA", fake.commands)

    def test_numeric_results_with_echo_are_read(self):
        """A stored profile with E1 and V0: ATZ's echo ends in a CR, and its
        result is a digit and a CR, with no LF anywhere."""
        fake = FakeModem(numeric=True)

        async def go():
            waiting = asyncio.ensure_future(modem.wait_for_call(PORT, 115200, "ATZ"))
            await eventually(lambda: fake.commands == ["ATZ", *modem.SETUP])
            await asyncio.sleep(0.4)  # (longer than a command may take to answer)
            await stop(waiting)
        with self.assertNoLogs("dirtyfork", "WARNING"), plugged_in({PORT: fake}):
            run(go())

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

    def test_a_line_that_holds_its_output_does_not_hold_up_the_hang_up(self):
        """The modem stops taking data (switched off mid-call, or flow
        control held) with output queued: the hang-up gives up on that output
        and closes the port, rather than wait for it (pyserial-asyncio's
        close flushes the port on the event loop's thread, without limit)."""
        fake = FakeModem(connect="CONNECT 2400", cps=240)

        async def then(reader, writer):
            fake.powered = False  # (switched off: nothing leaves any more)
            writer.write(b"x" * 2048)
        self.connected(fake, then)
        self.assertFalse(fake.is_open)
        self.assertEqual(bytes(fake.unsent), b"")  # (dropped, not left queued)

    def test_a_switched_off_modem_does_not_stop_a_shutdown(self):
        """What setting it up wrote waits in the port for ever: stopping the
        port's task must still end at once (and close the port)."""
        fake = FakeModem(powered=False)

        async def go():
            listening = asyncio.ensure_future(modem.listen(PORT, 115200, "ATZ", None))
            await eventually(lambda: fake.opened == 1 and len(fake.unsent) > len("ATZ\r"))
            await stop(listening)
        with self.assertLogs("dirtyfork", "WARNING"), plugged_in({PORT: fake}):
            run(go(), timeout=15)
        self.assertFalse(fake.is_open)

    def test_a_modem_without_dcd_that_ignores_dtr_is_hung_up_with_ath(self):
        """With no carrier to tell by, it may still be connected after DTR
        dropped: ATH to be sure."""
        fake = FakeModem(dcd=False, follows_dtr=False, guard=0.2)

        async def then(reader, writer):
            pass
        self.connected(fake, then)
        self.assertEqual(fake.commands[-1], "ATH")
        self.assertFalse(fake.carrier)

    def test_a_modem_slow_to_drop_the_carrier_is_not_sent_ath(self):
        """It goes on hook a moment after DTR drops: that is no reason for
        the +++ escape and ATH (and a line in the log) at every call."""
        fake = FakeModem(hangup_delay=0.4, guard=0.2)

        async def then(reader, writer):
            pass
        with self.assertLogs("dirtyfork", "INFO") as logs:
            self.connected(fake, then)
        self.assertNotIn("ATH", fake.commands)
        self.assertFalse(fake.carrier)
        self.assertFalse([line for line in logs.output if "perhaps still connected" in line])

    def test_a_port_that_fails_closing_itself_with_output_buffered_is_still_closed(self):
        """A read fails while output waits in the transport's buffer:
        pyserial-asyncio starts its own graceful close, which never ends on
        Windows (its writer stops); the hang-up must still close the port, or
        every attempt to open it again fails."""
        fake = FakeModem(connect="CONNECT 2400", cps=240)

        async def then(reader, writer):
            fake.powered = False  # (it takes nothing more: what follows stays buffered)
            writer.write(b"x" * 2048)
            await asyncio.sleep(0.05)
            writer.write(b"y" * 2048)
            fake.failing_reads = True
            fake.rx += b"z"  # (something to read, whose read fails)
            await eventually(lambda: writer._transport.is_closing())
        self.connected(fake, then)
        self.assertFalse(fake.is_open)

    def test_drain_fails_once_the_port_has_failed(self):
        """Unplugged mid-call, and pyserial-asyncio has given the transport up
        (before the carrier's next look): what is written goes nowhere, so a
        sender that only writes must hear of it from drain()."""
        fake = FakeModem()

        async def then(reader, writer):
            await asyncio.sleep(0.05)  # (the carrier watch has had its first look)
            fake.unplug()
            await eventually(lambda: writer._transport.is_closing())
            writer.write(b"lost")
            with self.assertRaises(ConnectionResetError):
                await writer.drain()
        with mock.patch.object(modem, "CARRIER_POLL", 30):  # (and has no other meanwhile)
            self.connected(fake, then)

    def test_a_port_that_fails_mid_call_is_logged_as_such(self):
        """Not as the caller hanging up: the sysop must see the hardware failed."""
        fake = FakeModem()

        async def then(reader, writer):
            fake.unplug()
            self.assertEqual(await asyncio.wait_for(reader.read(10), 5), "")
            await asyncio.sleep(0.3)  # (the carrier's next looks)
        with self.assertLogs("dirtyfork", "INFO") as logs:
            self.connected(fake, then)
        self.assertTrue(any("the serial port failed during the call" in line
                            for line in logs.output), logs.output)
        self.assertFalse(any("the caller hung up" in line for line in logs.output), logs.output)

    def test_a_setting_the_modem_does_not_know_leaves_the_others(self):
        """It answers AT&C1 with ERROR, and (as many do) then applies none of
        that command: the other settings, each sent alone, still hold."""
        fake = FakeModem(rejects=("&C1",))

        async def go():
            waiting = asyncio.ensure_future(modem.wait_for_call(PORT, 115200, "ATZ"))
            await eventually(lambda: fake.commands[-1:] == [modem.SETUP[-1]])
            await asyncio.sleep(0.1)
            await stop(waiting)
        with self.assertLogs("dirtyfork", "WARNING") as logs, plugged_in({PORT: fake}):
            run(go())
        warnings = [line for line in logs.output if line.startswith("WARNING")]
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("AT&C1 gave ERROR", warnings[0])
        self.assertFalse(fake.echo)  # (E0 applied)

    def test_the_transfer_block_follows_the_line_speed(self):
        class Line:
            transport = None
        writer = modem.SerialWriter(Line())
        for bps, block in ((2400, 256), (4800, 512), (9600, 1024), (33600, 1024)):
            writer.set_line_speed(bps)
            self.assertEqual(writer.transfer_block, block, bps)

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
            await eventually(lambda: fake.opened == 1 and fake.commands[-1:] == [modem.SETUP[-1]])
            fake.ring()
            await eventually(lambda: fake.opened == 2 and fake.commands[-1:] == [modem.SETUP[-1]])
            fake.ring()
            await eventually(lambda: len(sessions) == 2)
            await stop(listening)
        with plugged_in({PORT: fake}):
            run(go())
        self.assertEqual(sessions, [1, 2])
        self.assertEqual(fake.commands[:12], ["ATZ", *modem.SETUP, "ATA"] * 2)
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
            settings = zmodem.Settings(start_timeout=10, header_timeout=2,
                                       drain_every=writer.transfer_block,
                                       subpacket_size=writer.transfer_block)
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
