"""modem.py's serial adapters: flow control, and timed-out reads."""
import asyncio
import unittest

import _setup  # noqa: F401
import modem


class SerialAdapters(unittest.TestCase):
    def test_drain_waits_for_the_line(self):
        """A file transfer relies on drain(): without it a download would be
        queued whole in the serial transport at once."""
        class Stream:  # (pyserial-asyncio's StreamWriter)
            drained = 0

            async def drain(self):
                Stream.drained += 1

        class Transport:
            def write(self, data):
                pass

            def is_closing(self):
                return False
        writer = modem.SerialWriter(Transport(), None, Stream())
        writer.write(b"data")
        asyncio.run(writer.drain())
        self.assertEqual(Stream.drained, 1)

    def test_a_timed_out_read_is_a_timeout_not_a_hang_up(self):
        class Silent:  # (a line on which nothing arrives)
            async def read(self, n):
                await asyncio.Event().wait()

        async def go():
            return await asyncio.wait_for(modem.SerialReader(Silent()).read(10), 0.1)
        with self.assertRaises(asyncio.TimeoutError):
            asyncio.run(go())


if __name__ == "__main__":
    unittest.main()
