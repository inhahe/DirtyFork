"""Mouse reports in both forms, and bright backgrounds by terminal type."""
import asyncio
import unittest

import _setup
import common
import input_output as io
from definitions import blue, white
from keyboard_codes import check, check_partial, click, down, left, release, up


class BrightBackgroundsByTerminal(unittest.TestCase):
    def test_xterm_family_terminals_get_colours_bbs_terminals_blink(self):
        for ttype, expected in (("XTERMJS", "aixterm"), ("xterm-256color", "aixterm"),
                                ("ansi-bbs", "blink"), ("SyncTERM", "blink")):
            user = _setup.make_user()
            user.writer.get_extra_info = lambda key, default=None: ttype if key == "TERM" else default
            asyncio.run(common.detect_terminal(user))
            self.assertEqual(user.bright_bg, expected, ttype)


class BrightBackgrounds(unittest.TestCase):
    def colour(self, bright_bg):
        user = _setup.make_user()
        user.bright_bg = bright_bg
        io.ansi_color(user, fg=white, bg=blue, fg_br=False, bg_br=True)
        io._ansi_color_write(user)
        return user.writer.text()

    def test_xterm_family_gets_aixterm_codes_not_blink(self):
        text = self.colour("aixterm")
        self.assertIn("104", text)
        self.assertNotIn("5;", text)

    def test_bbs_terminals_keep_blink(self):
        text = self.colour("blink")
        self.assertIn("5", text.split("[")[1].split(";"))
        self.assertIn("44", text)


class MouseReports(unittest.TestCase):
    def parse(self, seq):
        # As _get_input_key feeds them: every prefix is partial, the whole is a key
        for i in range(1, len(seq)):
            self.assertTrue(check_partial(seq[:i]), repr(seq[:i]))
        return check(seq)

    def test_x10_click(self):
        key = self.parse("\x1b[M" + chr(32 + 0) + chr(32 + 10) + chr(32 + 5))
        self.assertEqual((key, key.button, key.col, key.row, key.wheel), (click, left, 10, 5, None))

    def test_the_wheel_is_never_a_click(self):
        # X10 wheel up is button 64, down 65: once read as a left and a middle click
        for code, direction in ((64, up), (65, down)):
            key = self.parse("\x1b[M" + chr(32 + code) + chr(32 + 3) + chr(32 + 4))
            self.assertEqual((key.button, key.wheel), (None, direction), code)
            key = self.parse(f"\x1b[<{code};3;4M")
            self.assertEqual((key.button, key.wheel), (None, direction), code)

    def test_sgr_press_and_release_anywhere_on_a_wide_screen(self):
        key = self.parse("\x1b[<0;150;60M")
        self.assertEqual((key, key.button, key.col, key.row), (click, left, 150, 60))
        key = self.parse("\x1b[<0;150;60m")
        self.assertEqual(key.button, release)

    def test_sgr_modifiers_and_motion(self):
        key = self.parse("\x1b[<52;7;8M")  # left + ctrl (16) + motion (32) + shift (4)
        self.assertEqual((key.button, key.ctrl, key.motion, key.shift), (left, True, True, True))


if __name__ == "__main__":
    unittest.main()
