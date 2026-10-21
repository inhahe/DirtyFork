"""input_output.py: helpers that write escape sequences, and the state they track."""
import unittest

import _setup
import input_output as io
from definitions import blue, black


def row_text(user, row):
    return "".join(ch.char for ch in user.screen[row - 1]).rstrip()


class MouseReporting(unittest.IsolatedAsyncioTestCase):
    async def test_on_off_and_a_forced_reset(self):
        user = _setup.make_user()
        await io.ansi_mouse_reporting(user, True)
        await io.ansi_mouse_reporting(user, True)                 # on already: nothing sent
        self.assertEqual(user.writer.text(), "\x1b[?1000h\x1b[?1002h")
        self.assertTrue(user.mouse_reporting)
        user.writer.out.clear()
        await io.ansi_mouse_reporting(user, False)
        await io.ansi_mouse_reporting(user, False, force=True)    # state unknown: sent anyway
        self.assertEqual(user.writer.text(), "\x1b[?1002l\x1b[?1000l" * 2)
        self.assertFalse(user.mouse_reporting)


class ClearLineEnd(unittest.IsolatedAsyncioTestCase):
    async def test_clears_where_the_pending_move_points(self):
        user = _setup.make_user()
        await io.send(user, "x" * 30)                             # row 1
        await io.ansi_move(user, 5, 1)
        await io.send(user, "typing...")                          # the cursor is on row 5
        await io.ansi_move_deferred(user, row=1, col=11)          # staged, not sent
        io.ansi_color(user, bg=blue)                              # staged, not sent
        user.writer.out.clear()
        await io.ansi_clear_line_end(user)
        self.assertRegex(user.writer.text(), r"^\x1b\[1;11H.*\x1b\[K$")   # moved first
        self.assertEqual(row_text(user, 1), "x" * 10)
        self.assertEqual(row_text(user, 5), "typing...")
        self.assertEqual(user.screen[0][10].bg, blue)             # in the pending background
        self.assertEqual(user.screen[0][9].bg, black)

    async def test_nothing_to_clear_after_a_full_row(self):
        user = _setup.make_user()
        await io.ansi_move(user, 3, 1)
        await io.send(user, "y" * user.screen_width)              # fills row 3
        user.writer.out.clear()
        await io.ansi_clear_line_end(user)
        self.assertNotIn("\x1b[K", user.writer.text())
        self.assertEqual(row_text(user, 3), "y" * user.screen_width)


if __name__ == "__main__":
    unittest.main()
