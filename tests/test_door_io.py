"""door.py: what flows between the caller and the door, and the door process."""
import asyncio
import sys
import types
import unittest

import _setup
import door
from config import Config


def pump_user(reader_data=None, fail_drain=False):
    """A caller for the pumps: reader returns *reader_data* (None = nothing, ever)."""
    async def read(n):
        if reader_data is None:
            await asyncio.sleep(3600)
        return reader_data
    return types.SimpleNamespace(writer=_setup.FakeWriter(fail_drain), popup_event=None,
                                 reader=types.SimpleNamespace(read=read))


async def nodrain():
    pass


class DoorOutput(unittest.TestCase):
    def test_clear_screen_also_homes(self):
        o = door._DoorOutput()
        self.assertEqual(o.feed("a\x1b[2Jb"), "a\x1b[2J\x1b[Hb")
        self.assertEqual(o.feed("x\x0cy"), "x\x1b[2J\x1b[Hy")

    def test_sequence_split_across_chunks(self):
        o = door._DoorOutput()
        self.assertEqual(o.feed("tail\x1b["), "tail")
        self.assertEqual(o.feed("2Jz"), "\x1b[2J\x1b[Hz")
        self.assertEqual(o.feed("q\x1b[2"), "q")
        self.assertEqual(o.feed(";5H"), "\x1b[2;5H")
        self.assertEqual(o.feed("end\x1b"), "end")
        self.assertEqual(o.flush(), "\x1b")


class DoorInput(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(door._DoorInput(Config({})).keys(b"abc\x1b[A"), [b"abc\x1b[A"])

    def test_doorway_translation(self):
        di = door._DoorInput(Config({"key_translation": "doorway"}))
        self.assertEqual(di.keys(b"x\x1b[Ay"), [b"x\x00\x48y"])
        self.assertEqual(di.keys(b"\x1b["), [])
        self.assertEqual(di.keys(b"B"), [b"\x00\x50"])
        self.assertEqual(di.keys(b"\x1b[11~\x1bOP\x1b[24~"), [b"\x00\x3b\x00\x3b\x00\x86"])
        self.assertEqual(di.keys(b"\x1b"), [])
        self.assertEqual(di.flush(), [b"\x1b"])           # a lone ESC still gets through
        self.assertEqual(di.keys(b"\x1b[Zq"), [b"\x1b[Zq"])  # unknown sequences pass through

    def test_pacing_splits_keys(self):
        di = door._DoorInput(Config({"input_pace_ms": 20, "key_translation": "doorway"}))
        self.assertEqual(di.keys(b"ab\x1b[C"), [b"a", b"b", b"\x00\x4d"])

    def test_ctrl_x_three_times_aborts(self):
        di = door._DoorInput(Config({}))
        self.assertFalse(di.aborted(b"\x18\x18", 0.0))
        self.assertTrue(di.aborted(b"\x18", 0.5))
        di = door._DoorInput(Config({}))
        self.assertFalse(di.aborted(b"\x18\x18", 10.0))
        self.assertFalse(di.aborted(b"\x18", 13.0))       # too slow


class Pumps(unittest.IsolatedAsyncioTestCase):
    async def test_output_side_hangup_is_the_caller(self):
        async def read(n):
            return b"hello"
        self.assertEqual(await door._pump_door_to_user(pump_user(fail_drain=True), read),
                         door.ENDED_BY_CALLER)

    async def test_door_eof_is_the_door(self):
        async def read(n):
            return b""
        self.assertEqual(await door._pump_door_to_user(pump_user(), read), door.ENDED_BY_DOOR)

    async def test_failing_session_log_does_not_end_the_session(self):
        chunks = [b"one", b"two", b""]
        async def read(n):
            return chunks.pop(0)
        class BadLog:
            def write(self, s):
                raise OSError(28, "No space left on device")
        user = pump_user()
        result = await door._pump_door_to_user(user, read, session_log=BadLog())
        self.assertEqual(result, door.ENDED_BY_DOOR)
        self.assertEqual(user.writer.text(), "onetwo")

    async def test_input_pump(self):
        di = door._DoorInput(Config({}))
        self.assertEqual(await door._pump_user_to_door(pump_user(reader_data=""), di,
                                                       lambda b: None, nodrain),
                         door.ENDED_BY_CALLER)                       # caller hung up
        def broken(b):
            raise BrokenPipeError("door gone")
        self.assertEqual(await door._pump_user_to_door(pump_user(reader_data="x"), di,
                                                       broken, nodrain),
                         door.ENDED_BY_DOOR)                         # writing to the door failed
        self.assertEqual(await door._pump_user_to_door(pump_user(), di, lambda b: None, nodrain,
                                                       still_running=lambda: False),
                         door.ENDED_BY_DOOR)                         # stdio door exited

    async def test_last_output_delivered_when_the_door_exits_first(self):
        user = pump_user()
        async def read(n, chunks=[b"final screen", b""]):
            await asyncio.sleep(0.2)                  # still on its way when the exit is seen
            return chunks.pop(0)
        async def exited():
            return door.ENDED_BY_DOOR
        di = door._DoorInput(Config({}))
        result = await door._run_until_first_done(
            door._pump_user_to_door(user, di, lambda b: None, nodrain),
            door._pump_door_to_user(user, read), exited(), output=1)
        self.assertEqual(result, door.ENDED_BY_DOOR)
        self.assertEqual(user.writer.text(), "final screen")

    async def test_first_result_wins(self):
        async def a():
            return "A"
        async def b():
            await asyncio.sleep(5)
            return "B"
        self.assertEqual(await door._run_until_first_done(b(), a()), "A")


class Processes(unittest.IsolatedAsyncioTestCase):
    async def test_stop_process(self):
        p = await asyncio.create_subprocess_exec(sys.executable, "-c", "import time; time.sleep(30)")
        self.assertTrue(await door._stop_process(p, 0.2))
        self.assertIsNotNone(p.returncode)
        p = await asyncio.create_subprocess_exec(sys.executable, "-c", "pass")
        self.assertFalse(await door._stop_process(p, 5))
        self.assertEqual(p.returncode, 0)
        self.assertFalse(await door._stop_process(None, 0))

    async def test_wait_for_dosbox(self):
        loop = asyncio.get_running_loop()
        p = await asyncio.create_subprocess_exec(sys.executable, "-c", "raise SystemExit(3)")
        with self.assertRaisesRegex(door._DoorStartError, "exited \\(code 3\\)"):
            await door._wait_for_dosbox(loop.create_future(), p, 30)   # doesn't wait 30 s
        p = await asyncio.create_subprocess_exec(sys.executable, "-c", "import time; time.sleep(30)")
        try:
            with self.assertRaisesRegex(door._DoorStartError, "timed out"):
                await door._wait_for_dosbox(loop.create_future(), p, 0.2)
            fut = loop.create_future()
            fut.set_result(("reader", "writer"))
            self.assertEqual(await door._wait_for_dosbox(fut, p, 5), ("reader", "writer"))
        finally:
            await door._stop_process(p, 0)

    async def test_native_socket_door_that_exits_is_an_error(self):
        proc = types.SimpleNamespace(returncode=3)
        with self.assertRaisesRegex(RuntimeError, "exited"):
            await door._bridge_socket(pump_user(), "127.0.0.1", 1, proc, Config({}))


if __name__ == "__main__":
    unittest.main()
