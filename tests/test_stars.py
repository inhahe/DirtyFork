"""stars.py: when stars show, erasing them, and drawing without disturbing the BBS."""
import asyncio
import math
import random
import types
import unittest
from unittest import mock

import _setup
import input_output
import stars
from definitions import cyan, white


def system(**stars_block):
    return types.SimpleNamespace(stars=types.SimpleNamespace(**stars_block) if stars_block else None)


def star_cells(user):
    glyphs = set(stars._FRAMES) - {" "}
    return [(r, c) for r, row in enumerate(user.screen) for c, ch in enumerate(row) if ch.char in glyphs]


class Settings(unittest.TestCase):
    def enabled(self, sys_cfg, conf):
        with mock.patch.object(stars, "_sys_config", sys_cfg):
            return stars._settings(types.SimpleNamespace(conf=conf))[0]

    def test_system_setting_is_the_master_switch(self):
        on = system(enabled=True)
        off = system(enabled=False)
        self.assertTrue(self.enabled(on, None))                                   # login screen
        self.assertFalse(self.enabled(off, None))
        self.assertFalse(self.enabled(system(), None))                            # no stars: block
        self.assertFalse(self.enabled(system(interval=100), None))                # no enabled:
        self.assertTrue(self.enabled(on, types.SimpleNamespace()))                # user didn't say
        self.assertFalse(self.enabled(on, types.SimpleNamespace(show_stars=False)))
        self.assertFalse(self.enabled(off, types.SimpleNamespace(show_stars=True)))  # can't turn on


class ChosenCells(unittest.TestCase):
    def test_edges(self):
        self.assertEqual(list(stars._chosen_cells(100, 0)), [])
        self.assertEqual(list(stars._chosen_cells(5, 1)), [0, 1, 2, 3, 4])
        self.assertEqual(list(stars._chosen_cells(100, math.nan)), [])
        self.assertEqual(list(stars._chosen_cells(100, -1)), [])
        self.assertEqual(list(stars._chosen_cells(100, 1e-320)), [])   # no overflow

    def test_distribution(self):
        random.seed(1)
        counts = []
        for _ in range(3000):
            cells = list(stars._chosen_cells(2000, 0.01))
            self.assertEqual(cells, sorted(set(cells)))
            self.assertTrue(all(0 <= c < 2000 for c in cells))
            counts.append(len(cells))
        self.assertAlmostEqual(sum(counts) / len(counts), 20, delta=1)   # n * p


class Drawing(unittest.IsolatedAsyncioTestCase):
    async def test_pending_colour_and_move_survive_a_tick(self):
        user = _setup.make_user()
        input_output.ansi_color(user, fg=cyan, fg_br=True)          # staged by the BBS, not sent yet
        await input_output.ansi_move_deferred(user, row=10, col=5)
        async with input_output.cursor_preserved(user, hide_cursor=True):
            await stars._draw(user, 3, 3, "*", 4, False)
        self.assertEqual((user.new_fg, user.new_fg_br, user.new_row, user.new_col), (cyan, True, 10, 5))
        self.assertEqual((user.cur_fg, user.cur_row, user.cur_col), (white, 1, 1))
        self.assertTrue(user.cur_show_cursor)

    async def test_stars_erased_when_they_switch_off(self):
        user = _setup.make_user()
        user.conf = types.SimpleNamespace(show_stars=True)
        sys_cfg = system(enabled=True, interval=100, probability=0.01, fg=4, fg_br=False)
        with mock.patch.object(stars, "_sys_config", sys_cfg):
            task = asyncio.create_task(stars.stars_loop(user))
            try:
                await asyncio.sleep(1.5)
                self.assertTrue(star_cells(user), "no stars appeared")
                user.conf.show_stars = False
                await asyncio.sleep(0.3)
                self.assertEqual(star_cells(user), [])
                self.assertEqual(user._stars_active, [])
            finally:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

    async def test_an_idle_tick_writes_nothing(self):
        user = _setup.make_user()
        async with user.write_lock:
            await stars._tick(user, [], 4, False, 0.0, 100)   # no stars, none to spawn
        self.assertEqual(user.writer.text(), "")

    async def test_repaint_after_clear_only_while_wanted(self):
        user = _setup.make_user()
        user._stars_active = [(2, 2, 0, 0.0, 4, False)]
        user.conf = types.SimpleNamespace(show_stars=False)
        with mock.patch.object(stars, "_sys_config", system(enabled=True)):
            await stars._repaint_after_cls(user)
        self.assertEqual(user._stars_active, [])
        self.assertEqual(star_cells(user), [])


class ScrollRegion(unittest.IsolatedAsyncioTestCase):
    async def test_region_homes_the_tracked_cursor(self):
        user = _setup.make_user()
        await input_output.ansi_move(user, 20, 7)
        await input_output.ansi_set_region(user, 1, 24)
        self.assertEqual((user.cur_row, user.cur_col, user.new_row, user.new_col), (1, 1, 20, 7))
        user.writer.out.clear()
        await input_output.send(user, "x")
        self.assertIn("\x1b[20;7H", user.writer.text())        # moves back before writing


if __name__ == "__main__":
    unittest.main()
