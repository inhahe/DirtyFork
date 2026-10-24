"""input_output.py: helpers that write escape sequences, and the state they track."""
import asyncio
import unittest
from unittest import mock

import _setup
import input_output as io
from definitions import blue, black, cyan, green


def row_text(user, row):
    return "".join(ch.char for ch in user.screen[row - 1]).rstrip()


def blank_screen(user):
    return all(not row_text(user, r) for r in range(1, user.screen_height + 1))


async def any_key(user, *args, **kwargs):
    return " "


class LineFeed(unittest.IsolatedAsyncioTestCase):
    async def test_at_the_bottom_of_a_scroll_region(self):
        user = _setup.make_user()
        await io.ansi_move(user, 23, 1)
        await io.send(user, "separator")                  # below the region
        await io.ansi_set_region(user, 3, 22)
        await io.ansi_move(user, 22, 1)
        await io.send(user, "first")
        await io.send(user, "\r\nsecond")                 # the region scrolls; the cursor stays
        self.assertEqual(user.cur_row, 22)
        self.assertEqual((row_text(user, 21), row_text(user, 22), row_text(user, 23)),
                         ("first", "second", "separator"))


class MouseReporting(unittest.IsolatedAsyncioTestCase):
    async def test_on_off_and_a_forced_reset(self):
        user = _setup.make_user()
        await io.ansi_mouse_reporting(user, True)
        await io.ansi_mouse_reporting(user, True)                 # on already: nothing sent
        self.assertEqual(user.writer.text(), "\x1b[?1000h\x1b[?1002h\x1b[?1006h")
        self.assertTrue(user.mouse_reporting)
        user.writer.out.clear()
        await io.ansi_mouse_reporting(user, False)
        await io.ansi_mouse_reporting(user, False, force=True)    # state unknown: sent anyway
        self.assertEqual(user.writer.text(), "\x1b[?1006l\x1b[?1002l\x1b[?1000l" * 2)
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

    async def test_wrap_off_full_row_keeps_its_last_character(self):
        user = _setup.make_user()
        io.ansi_wrap(user, False)
        await io.ansi_move(user, 4, 1)
        await io.send(user, "z" * user.screen_width)       # the cursor stays on the last column
        user.writer.out.clear()
        await io.ansi_clear_line_end(user)
        self.assertNotIn("\x1b[K", user.writer.text())
        self.assertEqual(row_text(user, 4), "z" * user.screen_width)

    async def test_a_move_asked_for_after_a_full_row_is_honoured(self):
        user = _setup.make_user()
        await io.ansi_move(user, 4, 1)
        await io.send(user, "old text")
        await io.ansi_move(user, 3, 1)
        await io.send(user, "y" * user.screen_width)       # tracked at (4, 1) now
        await io.ansi_move_deferred(user, row=4, col=1)    # ... and asked for explicitly
        await io.ansi_clear_line_end(user)
        self.assertEqual(row_text(user, 4), "")

    async def test_nothing_to_clear_after_a_full_row(self):
        user = _setup.make_user()
        await io.ansi_move(user, 3, 1)
        await io.send(user, "y" * user.screen_width)              # fills row 3
        user.writer.out.clear()
        await io.ansi_clear_line_end(user)
        self.assertNotIn("\x1b[K", user.writer.text())
        self.assertEqual(row_text(user, 3), "y" * user.screen_width)


class Popup(unittest.IsolatedAsyncioTestCase):
    async def test_popup_leaves_the_interrupted_output_as_it_was(self):
        import input_fields
        user = _setup.make_user()
        await io.ansi_move(user, 10, 5)
        io.ansi_color(user, fg=cyan, fg_br=True)
        await io.ansi_color_2(user)                        # on the terminal: bright cyan
        io.ansi_color(user, fg=green)                      # staged, not sent
        await io.ansi_move_deferred(user, row=12, col=3)   # staged, not sent
        staged = (user.new_fg, user.new_fg_br, user.new_bg, user.new_row, user.new_col)
        self.assertEqual(staged[0::3], (green, 12))

        async def any_key(user, *args, **kwargs):
            return " "

        with mock.patch.object(input_fields, "get_input_key", any_key):
            await input_fields.show_message_box(user, "Hello there")
        self.assertEqual((user.cur_row, user.cur_col), (10, 5))
        self.assertEqual((user.cur_fg, user.cur_fg_br), (cyan, True))
        self.assertEqual((user.new_fg, user.new_fg_br, user.new_bg, user.new_row, user.new_col), staged)
        self.assertTrue(user.cur_show_cursor)

    async def test_clicking_the_close_button_closes_it(self):
        import input_fields
        from definitions import Eint
        from keyboard_codes import click, left
        user = _setup.make_user()
        button = "[" + bytes([254]).decode("cp437") + "]"
        keys_read = []

        async def click_the_button(user, *args, **kwargs):
            keys_read.append(1)
            if len(keys_read) > 1:
                return " "                                 # (the click didn't close it)
            row = next(r for r in range(1, user.screen_height + 1) if button in row_text(user, r))
            col = row_text(user, row).index(button) + 2    # the middle of [■], 1-based
            return Eint(click, button=left, row=row, col=col, motion=False,
                        shift=False, alt=False, ctrl=False, wheel=None)

        with mock.patch.object(input_fields, "get_input_key", click_the_button):
            await input_fields.show_message_box(user, "Hello there")
        self.assertEqual(len(keys_read), 1)

    async def test_a_cancelled_popup_still_restores(self):
        import input_fields
        user = _setup.make_user()
        up = asyncio.Event()

        async def no_key_yet(user, *args, **kwargs):
            up.set()
            await asyncio.sleep(3600)

        with mock.patch.object(input_fields, "get_input_key", no_key_yet):
            popup = asyncio.create_task(input_fields.show_message_box(user, "Hello there"))
            await up.wait()
            self.assertFalse(user.cur_show_cursor)
            popup.cancel()                                   # (a page arriving, say)
            with self.assertRaises(asyncio.CancelledError):
                await popup
        self.assertTrue(user.cur_show_cursor)
        self.assertTrue(blank_screen(user))

    async def test_popup_at_the_right_edge_restores_autowrap(self):
        import input_fields
        user = _setup.make_user()
        io.ansi_wrap(user, False)                            # (as the teleconference runs)
        with mock.patch.object(input_fields, "get_input_key", any_key):
            await input_fields.show_message_box(user, "x", col=62, width=18)   # reaches column 80
        self.assertFalse(user.cur_wrap)

    async def test_longest_title_keeps_the_border_inside_the_box(self):
        import input_fields
        user = _setup.make_user()
        with mock.patch.object(input_fields, "get_input_key", any_key):
            await input_fields.show_message_box(user, "x", title="T" * 70)    # cut to fit
        self.assertTrue(blank_screen(user))                  # (no corner left outside the box)

    async def test_scrolling_sideways_with_popups_queued(self):
        import input_fields
        from definitions import Eint
        from keyboard_codes import click, left
        user = _setup.make_user()
        keys = [Eint(click, button=left, row=1, col=1, motion=False, shift=False, alt=False,
                     ctrl=False, wheel=None), " "]

        async def click_then_key(user, *args, **kwargs):
            return keys.pop(0)

        with mock.patch.object(input_fields, "get_input_key", click_then_key):
            await input_fields.show_message_box(user, "w" * 200, word_wrap=False, queued_count=2)
        self.assertEqual(keys, [])


class Tabs(unittest.IsolatedAsyncioTestCase):
    async def test_tab_stops_every_eight_columns(self):
        user = _setup.make_user()
        for start, stop in ((1, 9), (8, 9), (9, 17), (75, 80)):
            await io.ansi_move(user, 1, start)
            await io.send(user, "\t")
            self.assertEqual(user.cur_col, stop, f"tab from column {start}")


class AfterADoor(unittest.IsolatedAsyncioTestCase):
    async def test_the_door_s_region_and_cursor_are_tracked_and_undone(self):
        from ansi_emulator import AnsiEmulator
        user = _setup.make_user()
        AnsiEmulator(user).feed("\x1b[1;23r\x1b[?25l")    # the door's own region, cursor hidden
        self.assertEqual((user.scroll_region_top, user.scroll_region_bottom), (1, 23))
        self.assertFalse(user.cur_show_cursor)
        user.writer.out.clear()
        await io.ansi_reset_modes(user)
        out = user.writer.text()
        for seq in ("\x1b[?6l", "\x1b[r", "\x1b[?7h", "\x1b[?25h", "\x1b[?1000l"):
            self.assertIn(seq, out)
        self.assertEqual((user.scroll_region_top, user.scroll_region_bottom), (None, None))
        self.assertTrue(user.cur_show_cursor)


class Emulator(unittest.IsolatedAsyncioTestCase):
    async def test_rendering_a_screen_file_leaves_the_terminal_tracking_alone(self):
        from ansi_emulator import AnsiEmulator
        user = _setup.make_user()
        AnsiEmulator(user, live=False).feed("\x1b[1;23r\x1b[?25l")
        self.assertEqual((user.scroll_region_top, user.scroll_region_bottom), (None, None))
        self.assertTrue(user.cur_show_cursor)

    async def test_a_door_s_full_reset_resets_what_is_tracked(self):
        from ansi_emulator import AnsiEmulator
        user = _setup.make_user()
        AnsiEmulator(user).feed("\x1b[5;20r\x1b[?25l\x1bc")
        self.assertEqual((user.scroll_region_top, user.scroll_region_bottom), (None, None))
        self.assertTrue(user.cur_show_cursor)


class Uncovering(unittest.IsolatedAsyncioTestCase):
    async def test_overlay_over_a_stale_screen_leaves_the_repaint_to_the_activity(self):
        user = _setup.make_user()
        await io.ansi_move(user, 5, 1)
        await io.send(user, "old text")
        redrawn = []

        async def redraw():
            redrawn.append(1)

        user.redraw_hook = redraw
        await io.push_screen(user)
        await io.ansi_cls(user)                              # the overlay
        user.screen_stale = True                             # something was missed meanwhile
        await io.pop_screen(user)
        self.assertEqual(redrawn, [1])
        self.assertEqual(row_text(user, 5), "")              # (the outdated picture not repainted)
        self.assertEqual(user.screen_stack, [])

    async def test_no_redraw_when_a_popup_ends_in_a_disconnect(self):
        import input_fields
        from definitions import Disconnected
        user = _setup.make_user()
        redrawn = []

        async def redraw():
            redrawn.append(1)

        async def gone(user, *args, **kwargs):
            raise Disconnected()

        user.redraw_hook, user.screen_stale = redraw, True
        with mock.patch.object(input_fields, "get_input_key", gone):
            with self.assertRaises(Disconnected):
                await input_fields.show_message_box(user, "Hello there")
        self.assertEqual(redrawn, [])
        self.assertEqual(user.popup_depth, 0)


class Moves(unittest.IsolatedAsyncioTestCase):
    async def test_moving_down_out_of_a_scroll_region(self):
        user = _setup.make_user()
        await io.ansi_set_region(user, 3, 22)
        await io.ansi_move(user, 22, 80)                     # the region's bottom margin
        user.writer.out.clear()
        await io.ansi_move_deferred(user, row=24, col=80, drain=True)   # to the input row
        self.assertEqual(user.writer.text(), "\x1b[24;80H")  # (line feeds would scroll the region)
        self.assertEqual((user.cur_row, user.cur_col), (24, 80))

    async def test_moving_up_into_the_region_from_below_it(self):
        user = _setup.make_user()
        await io.ansi_set_region(user, 3, 22)
        await io.ansi_move(user, 24, 5)
        user.writer.out.clear()
        await io.ansi_move_deferred(user, row=2, col=5, drain=True)     # above the region
        self.assertEqual(user.writer.text(), "\x1b[2;5H")

    async def test_short_moves_inside_the_region_stay_relative(self):
        user = _setup.make_user()
        await io.ansi_set_region(user, 3, 22)
        await io.ansi_move(user, 10, 5)
        user.writer.out.clear()
        await io.ansi_move_deferred(user, row=12, col=5, drain=True)
        self.assertEqual(user.writer.text(), "\n\n")


class SidewaysPopup(unittest.IsolatedAsyncioTestCase):
    async def test_long_title_and_prompt_fit_the_top_border(self):
        import input_fields
        from keyboard_codes import right
        user = _setup.make_user()
        draws = []

        async def key_after_two_draws(user, *args, **kwargs):
            draws.append(row_text(user, 1))
            return right if len(draws) == 1 else " "         # scroll right once (a redraw), then close

        with mock.patch.object(input_fields, "get_input_key", key_after_two_draws):
            await input_fields.show_message_box(user, "w" * 200, word_wrap=False, title="T" * 69)
        self.assertEqual(len(draws), 2)
        for line in draws:
            self.assertLessEqual(len(line), user.screen_width)
            self.assertTrue(line.endswith("]┐"), line[-6:])            # ends with [x] and its corner
        self.assertEqual(draws[0], draws[1])                               # (no shrinking per redraw)
        self.assertTrue(blank_screen(user))


class Overlay(unittest.IsolatedAsyncioTestCase):
    async def test_overlay_gets_the_whole_screen_and_gives_everything_back(self):
        user = _setup.make_user()
        await io.ansi_set_region(user, 3, 22)
        await io.ansi_move(user, 10, 4)
        io.ansi_color(user, fg=cyan)
        await io.ansi_color_2(user)
        io.ansi_color(user, fg=green)
        await io.ansi_move_deferred(user, row=12, col=6)
        staged = (user.new_fg, user.new_fg_br, user.new_row, user.new_col)
        await io.push_screen(user)
        self.assertEqual((user.scroll_region_top, user.scroll_region_bottom), (None, None))
        await io.ansi_cls(user)
        await io.send(user, "the overlay")
        await io.pop_screen(user)
        self.assertEqual((user.scroll_region_top, user.scroll_region_bottom), (3, 22))
        self.assertEqual((user.cur_row, user.cur_col, user.cur_fg), (10, 4, cyan))
        self.assertEqual((user.new_fg, user.new_fg_br, user.new_row, user.new_col), staged)


if __name__ == "__main__":
    unittest.main()
