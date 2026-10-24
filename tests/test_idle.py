"""idle.IdleMonitor: what passes through it to the reader underneath."""
import asyncio
import unittest

import _setup
import common
from idle import IdleMonitor


class EncodingThroughTheIdleMonitor(unittest.TestCase):
    """The BBS's reader is wrapped in an IdleMonitor; switching the
    connection's encoding must reach the reader underneath."""

    def test_telnet_and_serial_readers(self):
        class TelnetReader:
            fn_encoding = staticmethod(lambda **kw: "cp437")

        class SerialReader:
            encoding = "cp437"

            def set_encoding(self, enc):
                self.encoding = enc

        async def switch(inner):
            user = common.User(inner, _setup.FakeWriter())
            user.reader = IdleMonitor(inner, user)  # (made inside the event loop, as always)
            common._set_connection_encoding(user, "latin-1")

        telnet, serial = TelnetReader(), SerialReader()
        asyncio.run(switch(telnet))
        asyncio.run(switch(serial))
        self.assertEqual(telnet.fn_encoding(incoming=True), "latin-1")
        self.assertEqual(serial.encoding, "latin-1")


if __name__ == "__main__":
    unittest.main()
