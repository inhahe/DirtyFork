"""logger.py: the console is written by a thread of its own, so a console
that stops taking output (a click in a Windows console with QuickEdit
pauses every program writing to it) does not stop the BBS."""
import io
import logging
import sys
import threading
import time
import unittest
import warnings
from unittest import mock

import _setup  # noqa: F401
import logger


class PausedConsole(io.TextIOBase):
    """A console that takes nothing until resumed."""

    def __init__(self):
        self.writing = threading.Event()  # (a write is waiting)
        self.resumed = threading.Event()
        self.lines = []

    def write(self, text):
        self.writing.set()
        self.resumed.wait()
        self.lines.append(text)
        return len(text)

    def flush(self):
        pass

    def shown(self, count, timeout=2.0):
        """What it has shown, once there are *count* writes (or *timeout*)."""
        end = time.monotonic() + timeout
        while len(self.lines) < count and time.monotonic() < end:
            time.sleep(0.01)
        return "".join(self.lines)


class Console(unittest.TestCase):
    def setUp(self):
        self.console = PausedConsole()
        self.addCleanup(self.console.resumed.set)  # (so that its writers end)

    def test_logging_goes_on_while_the_console_is_paused(self):
        dirtyfork, root = logging.getLogger("dirtyfork"), logging.getLogger()
        saved = (list(dirtyfork.handlers), dirtyfork.propagate, dirtyfork.level, list(root.handlers))

        def restore():
            self.console.resumed.set()  # (first: a writer stuck on it holds its handler's lock)
            for handler in dirtyfork.handlers:
                if isinstance(handler, logger.ConsoleLog):
                    handler.stop(timeout=1)
                handler.close()
            dirtyfork.handlers[:], dirtyfork.propagate = saved[0], saved[1]
            dirtyfork.setLevel(saved[2])
            root.handlers[:] = saved[3]
            logging.captureWarnings(False)
        self.addCleanup(restore)
        with mock.patch.object(sys, "stderr", self.console), \
                mock.patch.object(sys, "unraisablehook", sys.unraisablehook):
            logger.setup_logging()
            done = threading.Event()

            def go():  # (the BBS's event loop, logging)
                for n in range(5):
                    logger.log.info("line %d", n)
                logging.getLogger("asyncio").warning("from asyncio")
                with warnings.catch_warnings():
                    warnings.simplefilter("always")
                    warnings.warn("a Python warning", RuntimeWarning)
                logger.log.info("%d lines", "not a number")  # (a record that cannot be logged)
                done.set()
            threading.Thread(target=go, daemon=True).start()
            self.assertTrue(done.wait(2), "logging waited for the paused console")
            self.console.resumed.set()
            shown = self.console.shown(8)
        self.assertIn("line 4", shown)
        self.assertIn("from asyncio", shown)
        self.assertIn("a Python warning", shown)
        self.assertEqual(shown.count("--- Logging error ---"), 1, shown)  # (the file's and the console's, once)
        self.assertIn("not a number", shown)

    def test_lines_beyond_the_backlog_are_counted_not_kept(self):
        handler = logger.ConsoleLog(backlog=3, stream=self.console)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.addCleanup(handler.stop, 1)

        def emit(text):
            handler.handle(logging.makeLogRecord({"msg": text, "levelno": logging.INFO}))
        emit("line 0")
        self.assertTrue(self.console.writing.wait(2))  # (its thread is stuck writing that)
        for n in range(1, 10):
            emit(f"line {n}")  # (1-3 wait; 4-9 do not fit)
        self.console.resumed.set()
        self.console.shown(4)  # (the console catches up: room again)
        emit("after")
        shown = self.console.shown(6).splitlines()
        self.assertEqual(shown[:4], ["line 0", "line 1", "line 2", "line 3"])
        self.assertIn("6 log lines were not shown", shown[4])
        self.assertEqual(shown[5:], ["after"])


if __name__ == "__main__":
    unittest.main()
