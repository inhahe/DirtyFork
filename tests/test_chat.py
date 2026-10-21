"""Teleconference and one-on-one chat: the typing indicator and the chat invitation."""
import asyncio
import time
import unittest
from unittest import mock

import _setup
import oneonone
import teleconference


class Member:
    handle = "Bob"


class TypingIndicator(unittest.IsolatedAsyncioTestCase):
    async def test_redrawn_only_when_its_text_changes(self):
        user, bob = _setup.make_user(), Member()
        channel = teleconference.Channel("Test")
        channel.users.update({user, bob})
        with mock.patch.dict(teleconference.channels, {"test": channel}), \
             mock.patch.dict(teleconference.user_typing, {bob: time.time()}):
            await teleconference._draw_typing_indicator(user, "test")
            self.assertIn("Bob is typing...", user.writer.text())
            user.writer.out.clear()
            await teleconference._draw_typing_indicator(user, "test")   # (another keystroke)
            self.assertEqual(user.writer.text(), "")
            del teleconference.user_typing[bob]
            await teleconference._draw_typing_indicator(user, "test")   # stopped typing
            self.assertIn("\x1b[K", user.writer.text())
        self.assertEqual("".join(ch.char for ch in user.screen[1]).strip(), "")


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
