"""Teleconference and one-on-one chat: drawing on other members' screens, and the chat invitation."""
import asyncio
import time
import unittest
from unittest import mock

import _setup
import input_output as io
import oneonone
import teleconference


class Member:
    handle = "Bob"


def row_text(user, row):
    return "".join(ch.char for ch in user.screen[row - 1]).rstrip()


class TypingIndicator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user, self.bob = _setup.make_user(), Member()
        channel = teleconference.Channel("Test")
        channel.users.update({self.user, self.bob})
        patches = [mock.patch.dict(teleconference.channels, {"test": channel}),
                   mock.patch.dict(teleconference.user_typing, {self.bob: time.time()})]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    async def draw(self):
        await teleconference._draw_typing_indicator(self.user, teleconference._typers("test"))

    async def test_redrawn_only_when_row_2_shows_something_else(self):
        user = self.user
        await self.draw()
        self.assertEqual(row_text(user, 2), " Bob is typing...")
        user.writer.out.clear()
        await self.draw()                                   # (another keystroke)
        self.assertEqual(user.writer.text(), "")
        await io.ansi_move(user, 2, 1)                      # row 2 changed some other way (/clear)
        await io.ansi_clear_line_end(user)
        await self.draw()
        self.assertEqual(row_text(user, 2), " Bob is typing...")
        del teleconference.user_typing[self.bob]            # stopped typing
        await self.draw()
        self.assertEqual(row_text(user, 2), "")

    async def test_nothing_drawn_under_a_popup_and_all_redrawn_after(self):
        user = self.user
        redrawn = []

        async def redraw():
            redrawn.append(1)

        user.redraw_hook = redraw
        user.popup_depth = 1                                # a popup is up
        await self.draw()
        await teleconference._display_message(user, [(7, False, "a message")], 22)
        self.assertEqual(user.writer.text(), "")
        self.assertTrue(user.screen_stale)
        user.popup_depth = 0                                # it closes
        await io.screen_uncovered(user)
        self.assertEqual(redrawn, [1])
        self.assertFalse(user.screen_stale)


class Invitation(unittest.IsolatedAsyncioTestCase):
    async def test_closing_the_invitation_declines_it(self):
        user = _setup.make_user()
        answer = asyncio.get_running_loop().create_future()
        user._chat_invitation = (Member(), answer)
        replies = [None, "y"]        # [x] clicked; then, if the popup came back, Y

        async def popup(*args, **kwargs):
            return replies.pop(0)

        with mock.patch.object(oneonone, "show_message_box", popup):
            accepted = await oneonone._handle_invitation(user)
        self.assertFalse(accepted)
        self.assertIs(answer.result(), False)


if __name__ == "__main__":
    unittest.main()
