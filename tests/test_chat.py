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
        await teleconference._draw_typing_indicator(self.user, "test")

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


class ChatArea(unittest.IsolatedAsyncioTestCase):
    """What a member's chat area shows is logged, so a redraw can put it all back."""

    def setUp(self):
        from collections import deque
        self.user = _setup.make_user()
        self.channel = teleconference.Channel("Test")
        self.channel.users.add(self.user)
        patches = [mock.patch.dict(teleconference.channels, {"test": self.channel}),
                   mock.patch.dict(teleconference.user_channels, {self.user: "test"}),
                   mock.patch.dict(teleconference.member_lines, {self.user: deque(maxlen=200)})]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    async def test_a_private_line_sent_while_covered_comes_back_on_the_redraw(self):
        user = self.user
        await teleconference._setup_screen(user, "test")
        user.popup_depth = 1
        await teleconference._send_to_user(user, [(7, False, "[PM from Bob] hi")])
        self.assertNotIn("PM from Bob", user.writer.text())
        user.popup_depth = 0
        await teleconference._setup_screen(user, "test")         # what run's _redraw does
        await teleconference._draw_chat_area(user)
        self.assertEqual(row_text(user, teleconference._chat_bottom(user)), "[PM from Bob] hi")

    async def test_msg_only_to_members(self):
        user, bob = self.user, Member()
        import common
        await teleconference._setup_screen(user, "test")
        with mock.patch.dict(common.global_data.users, {"bob": bob}):
            await teleconference._process_command(user, "/msg Bob hi")
        self.assertIn("isn't in Teleconference", row_text(user, teleconference._chat_bottom(user)))

    async def test_join_leaves_who_is_there_on_screen(self):
        user = self.user
        await teleconference._setup_screen(user, "test")
        await teleconference._process_command(user, "/join games")
        screen = [row_text(user, r) for r in range(1, user.screen_height + 1)]
        self.assertIn("You are the only one here.", screen)


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
