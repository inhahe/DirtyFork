"""Terminals that can't do file transfers (the browser terminal) are told so."""
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

    def test_the_browser_terminal_is_cp437_without_transfers(self):
        user = self.detect("ANSI-JSTERM")
        self.assertEqual((user.encoding, user.file_transfers), ("cp437", False))

    def test_other_terminals_keep_transfers(self):
        for ttype, encoding in (("ansi-bbs", "cp437"), ("xterm-256color", "utf-8"), ("SyncTERM", "cp437")):
            user = self.detect(ttype)
            self.assertEqual((user.encoding, user.file_transfers), (encoding, True), ttype)


class ChooseProtocol(unittest.TestCase):
    def choose(self, file_transfers):
        """Run _choose_protocol with no protocols installed; return its result and
        the popups it showed."""
        user = _setup.make_user()
        user.file_transfers = file_transfers
        shown = mock.AsyncMock()
        with mock.patch.object(file, "show_message_box", shown), \
                mock.patch.object(file, "get_available_protocols", return_value={}):
            result = asyncio.run(file._choose_protocol(user))
        return result, [call.args[1] for call in shown.await_args_list]

    def test_a_terminal_without_transfers_is_told_why(self):
        result, popups = self.choose(False)
        self.assertIsNone(result)
        self.assertEqual(len(popups), 1)
        self.assertIn("web terminal", popups[0])

    def test_other_terminals_go_on_to_the_protocols(self):
        result, popups = self.choose(True)
        self.assertIsNone(result)
        self.assertEqual(popups, ["No file transfer protocols are available on this system."])


class DownloadPrompt(unittest.TestCase):
    def test_a_terminal_without_transfers_is_told_before_naming_a_file(self):
        user = _setup.make_user()
        user.file_transfers = False
        shown = mock.AsyncMock()
        read_line = mock.AsyncMock(return_value="q")
        with mock.patch.object(file, "show_message_box", shown), \
                mock.patch.object(file, "_read_line", read_line):
            asyncio.run(file._download_file(user))
        read_line.assert_not_awaited()
        self.assertEqual(len(shown.await_args_list), 1)
        self.assertIn("web terminal", shown.await_args_list[0].args[1])


if __name__ == "__main__":
    unittest.main()
