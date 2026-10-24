"""What the BBS makes of the caller's terminal type (encoding, transfer
protocols), and the protocol choice it leads to."""
import asyncio
import unittest
from unittest import mock

import _setup
import common
import file


class DetectTerminal(unittest.TestCase):
    def detect(self, ttype):
        user = _setup.make_user()
        user.writer.get_extra_info = lambda key, default=None: ttype if key == "TERM" else default
        asyncio.run(common.detect_terminal(user))
        return user

    def test_each_kind_of_terminal(self):
        for ttype, expected in (
                ("ANSI-JSTERM", ("cp437", frozenset())),  # the web terminal: none
                ("xterm-256color", ("utf-8", None)),
                ("ansi-bbs", ("cp437", None)),
                ("SyncTERM", ("cp437", None))):
            user = self.detect(ttype)
            self.assertEqual((user.encoding, user.transfer_protocols), expected, ttype)


class ChooseProtocol(unittest.TestCase):
    def choose(self, terminal, installed):
        """_choose_protocol for a terminal that can run *terminal* (None: any)
        on a BBS that has *installed*; returns (result, popups, keys read)."""
        user = _setup.make_user()
        user.transfer_protocols = terminal
        shown = mock.AsyncMock()
        keys = mock.AsyncMock(return_value="2")
        with mock.patch.object(file, "show_message_box", shown), \
                mock.patch.object(file, "get_input_key", keys), \
                mock.patch.object(file, "get_available_protocols", return_value=installed):
            result = asyncio.run(file._choose_protocol(user))
        return result, [call.args[1] for call in shown.await_args_list], keys.await_count

    def test_the_web_terminal_gets_zmodem_without_being_asked(self):
        self.assertEqual(self.choose(frozenset({"zmodem"}), {"zmodem": True, "ymodem": True}),
                         ("zmodem", [], 0))

    def test_a_terminal_that_can_run_both_is_asked(self):
        self.assertEqual(self.choose(None, {"zmodem": True, "ymodem": True}), ("ymodem", [], 1))

    def test_a_terminal_that_can_run_none_of_them_is_told_why(self):
        result, popups, _ = self.choose(frozenset({"zmodem"}), {"zmodem": False, "ymodem": True})
        self.assertIsNone(result)
        self.assertEqual(len(popups), 1)
        self.assertIn("Your terminal can't run", popups[0])

    def test_no_protocols_at_all(self):
        result, popups, _ = self.choose(None, {"zmodem": False, "ymodem": False})
        self.assertIsNone(result)
        self.assertEqual(popups, ["No file transfer protocols are available on this system."])


class DownloadPrompt(unittest.TestCase):
    def test_a_terminal_without_usable_protocols_is_told_before_naming_a_file(self):
        user = _setup.make_user()
        user.transfer_protocols = frozenset()
        shown = mock.AsyncMock()
        read_line = mock.AsyncMock(return_value="q")
        with mock.patch.object(file, "show_message_box", shown), \
                mock.patch.object(file, "_read_line", read_line):
            asyncio.run(file._download_file(user))
        read_line.assert_not_awaited()
        self.assertEqual(len(shown.await_args_list), 1)


if __name__ == "__main__":
    unittest.main()
