"""idle.IdleMonitor: what passes through it to the reader underneath."""
import asyncio
import unittest

import _setup
import common
from idle import IdleMonitor


class EncodingThroughTheIdleMonitor(unittest.TestCase):
    """The BBS's reader is wrapped in an IdleMonitor; switching the
    connection's encoding must reach the reader underneath."""

    def test_the_telnet_reader_switches(self):
        class TelnetReader:
            fn_encoding = staticmethod(lambda **kw: "cp437")

        async def switch(inner):
            user = common.User(inner, _setup.FakeWriter())
            user.reader = IdleMonitor(inner, user)  # (made inside the event loop, as always)
            user.encoding = "latin-1"
            common._set_connection_encoding(user)

        telnet = TelnetReader()
        asyncio.run(switch(telnet))
        self.assertEqual(telnet.fn_encoding(incoming=True), "latin-1")


if __name__ == "__main__":
    unittest.main()
