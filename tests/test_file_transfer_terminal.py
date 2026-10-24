"""file.py: callers in the browser terminal are told file transfers need a real one."""
import asyncio
import unittest
from unittest import mock

import _setup
import file


class TransferTerminal(unittest.TestCase):
    def choose(self, ttype):
        """Run _choose_protocol for a caller with this terminal type, with no
        protocols installed; return its result and the popups it showed."""
        user = _setup.make_user()
        user.ttype = ttype
        shown = mock.AsyncMock()
        with mock.patch.object(file, "show_message_box", shown), \
                mock.patch.object(file, "get_available_protocols", return_value={}):
            result = asyncio.run(file._choose_protocol(user))
        return result, [call.args[1] for call in shown.await_args_list]

    def test_the_web_terminal_is_told_why(self):
        result, popups = self.choose("ANSI-JSTERM")
        self.assertIsNone(result)
        self.assertEqual(len(popups), 1)
        self.assertIn("web terminal", popups[0])

    def test_other_terminals_go_on_to_the_protocols(self):
        for ttype in ("ansi-bbs", "xterm", "unknown"):
            result, popups = self.choose(ttype)
            self.assertIsNone(result)
            self.assertEqual(popups, ["No file transfer protocols are available on this system."], ttype)


if __name__ == "__main__":
    unittest.main()
