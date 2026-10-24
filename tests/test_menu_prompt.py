"""The text menu's prompt line: what is typed there, and what an error leaves."""
import unittest
from unittest import mock

import _setup
import menu
from definitions import success


def row_text(user, row):
    return "".join(ch.char for ch in user.screen[row - 1]).rstrip()


class Prompt(unittest.IsolatedAsyncioTestCase):
    async def run_menu(self, typed):
        """Type *typed* at the main menu, then /q; returns the user."""
        user = _setup.make_user()
        user.keys = {"doors"}
        keys = list(typed + "/q\r")

        async def next_key(user, *args, **kwargs):
            return keys.pop(0)

        with mock.patch.object(menu, "get_input_key", next_key):
            r = await menu.do_menu(user, "main")
        self.assertEqual(r.status, success)
        self.assertFalse(keys)
        return user

    def prompt_rows(self, user):
        return [row_text(user, r) for r in range(1, user.screen_height + 1)
                if row_text(user, r).startswith("Enter an option:")]

    async def test_error_clears_all_that_was_typed(self):
        # The second error is shown in place, over the first; the input typed
        # before it, leading spaces and all, must be gone from the prompt.
        user = await self.run_menu("/j zzzz\r" + "   /j yyyy\r")
        self.assertEqual(self.prompt_rows(user), ["Enter an option: /q"])


class Prefixes(unittest.TestCase):
    def test_each_sysop_tool_takes_one_letter(self):
        # (two names beginning alike, Edit User and Edit Files, made both take six)
        menu._ensure_menu_tree()
        node = menu._menu_nodes["sysop"]
        self.assertEqual({n: p for n, p in node.prefixes.items() if p > 1}, {})


if __name__ == "__main__":
    unittest.main()
