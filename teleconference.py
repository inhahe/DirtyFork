"""
Teleconference — split-screen multi-channel chat module modeled after
Major BBS / Worldgroup teleconference.
"""

import asyncio
import time
from collections import deque

from definitions import (
    RetVals, Disconnected, Char, Estr,
    cr, lf, success, fail, null,
    white, black, red, green, blue, magenta, cyan, yellow, brown,
)
from input_output import (
    send, ansi_move_deferred, ansi_color, ansi_wrap, ansi_cls, get_input_key,
    ansi_set_region, ansi_set_region_strict,
)
from keyboard_codes import left, right, home, end, back, delete, up, down, pgup, pgdn


# ---------------------------------------------------------------------------
# Channel / global state
# ---------------------------------------------------------------------------

class Channel:
    def __init__(self, name):
        self.name = name          # display name (original casing)
        self.topic = ""
        self.users = set()        # set of User objects
        self.history = deque(maxlen=200)
        self.max_history = 200

channels = {"general": Channel("General")}
user_channels = {}  # user -> channel-key (lowercase)
user_typing = {}    # user -> time.time() of last input edit

TYPING_TIMEOUT = 6  # seconds before a user is no longer considered "typing"


# ---------------------------------------------------------------------------
# CP437 box-drawing helpers
# ---------------------------------------------------------------------------

_HORIZ = bytes([196]).decode("cp437")   # ─


# ---------------------------------------------------------------------------
# Message rendering helpers
# ---------------------------------------------------------------------------

def _timestamp():
    return time.strftime("%H:%M")


async def _display_message(target, parts, chat_bottom):
    """Write a single formatted line into the target user's chat scroll region.

    *parts* is a list of (fg, fg_br, text) tuples that together form one line.
    The scroll region must already be set so that a cr+lf at *chat_bottom*
    scrolls only the chat area.
    """
    # Save logical cursor position (the user may be mid-typing)
    saved_row = target.new_row
    saved_col = target.new_col

    # Move to the bottom of the chat region and issue a newline to scroll
    await ansi_move_deferred(target, row=chat_bottom, col=1)
    await send(target, cr + lf)

    # Now the cursor is on a fresh line at chat_bottom; write message parts
    for fg, fg_br, text in parts:
        ansi_color(target, fg=fg, fg_br=fg_br, bg=black)
        await send(target, text)

    # Clear to end of line (in case previous content was longer)
    target.writer.write("\x1b[K")

    # Restore cursor back to the input area
    await ansi_move_deferred(target, row=saved_row, col=saved_col)
    await send(target, "", drain=True)


def _chat_top():
    return 3  # row 1 = header, row 2 = typing indicator, row 3+ = chat

def _chat_bottom(user):
    return user.screen_height - 3


def _input_row(user):
    return user.screen_height - 1


# ---------------------------------------------------------------------------
# High-level message broadcast / display
# ---------------------------------------------------------------------------

async def _broadcast(channel_key, parts, msg_type="chat", sender="", text=""):
    """Send *parts* to every user in the channel and record in history."""
    ch = channels.get(channel_key)
    if not ch:
        return
    ch.history.append((_timestamp(), msg_type, sender, text))
    for u in list(ch.users):
        try:
            await _display_message(u, parts, _chat_bottom(u))
        except (Disconnected, Exception):
            pass


async def _send_to_user(target, parts):
    """Send a formatted message to a single user (e.g., PM, error)."""
    try:
        await _display_message(target, parts, _chat_bottom(target))
    except (Disconnected, Exception):
        pass


async def _send_chat(user, channel_key, text):
    ts = _timestamp()
    parts = [
        (white, False, f"[{ts}] "),
        (white, True,  f"{user.handle}"),
        (white, False, f": {text}"),
    ]
    await _broadcast(channel_key, parts, msg_type="chat", sender=user.handle, text=text)


async def _send_action(user, channel_key, action_text):
    ts = _timestamp()
    parts = [
        (cyan, True, f"[{ts}] * {user.handle} {action_text}"),
    ]
    await _broadcast(channel_key, parts, msg_type="action", sender=user.handle, text=action_text)


async def _send_system(channel_key, text):
    parts = [
        (yellow, True, f"-- {text} --"),
    ]
    await _broadcast(channel_key, parts, msg_type="system", sender="", text=text)


async def _send_error(user, text):
    parts = [(red, True, text)]
    await _send_to_user(user, parts)


async def _send_pm(sender, target, text):
    ts = _timestamp()
    to_parts = [
        (magenta, True, f"[{ts}] [PM from {sender.handle}] {text}"),
    ]
    from_parts = [
        (magenta, True, f"[{ts}] [PM to {target.handle}] {text}"),
    ]
    await _send_to_user(target, to_parts)
    await _send_to_user(sender, from_parts)


# ---------------------------------------------------------------------------
# Screen drawing
# ---------------------------------------------------------------------------

async def _draw_header(user, channel_key):
    ch = channels.get(channel_key)
    if not ch:
        return
    name = ch.name
    count = len(ch.users)
    topic_part = f"  Topic: {ch.topic}" if ch.topic else ""

    title = f" Teleconference - {name} "
    users_part = f" {count} user{'s' if count != 1 else ''} "

    left_text = f"{_HORIZ}{_HORIZ}[{title}]{_HORIZ}{_HORIZ}[{users_part}]"
    if topic_part:
        left_text += f"{_HORIZ}{_HORIZ}{topic_part}"
    pad = user.screen_width - len(left_text)
    if pad < 0:
        left_text = left_text[:user.screen_width]
        pad = 0
    header_line = left_text + _HORIZ * pad

    await ansi_move_deferred(user, row=1, col=1)
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await send(user, header_line[:user.screen_width])


async def _draw_separator(user):
    sep_row = user.screen_height - 2
    await ansi_move_deferred(user, row=sep_row, col=1)
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await send(user, _HORIZ * user.screen_width)


async def _draw_typing_indicator(user, channel_key):
    """Draw the typing indicator on row 2. Shows who's currently typing."""
    now = time.time()
    ch = channels.get(channel_key)
    if not ch:
        return
    typers = []
    for u in ch.users:
        if u is not user and u in user_typing:
            if now - user_typing[u] < TYPING_TIMEOUT:
                typers.append(u.handle)
    saved_r, saved_c = user.new_row, user.new_col
    await ansi_move_deferred(user, row=2, col=1)
    if typers:
        if len(typers) == 1:
            text = f" {typers[0]} is typing..."
        else:
            text = f" {', '.join(typers)} are typing..."
        text = text[:user.screen_width]
        ansi_color(user, fg=white, fg_br=False, bg=black)
        await send(user, text)
    user.writer.write("\x1b[K")  # clear rest of line
    await ansi_move_deferred(user, row=saved_r, col=saved_c, drain=True)


async def _broadcast_typing_indicator(channel_key):
    """Update the typing indicator for all users in the channel."""
    ch = channels.get(channel_key)
    if not ch:
        return
    for u in list(ch.users):
        try:
            await _draw_typing_indicator(u, channel_key)
        except Exception:
            pass


async def _draw_input_prompt(user):
    row = _input_row(user)
    await ansi_move_deferred(user, row=row, col=1)
    ansi_color(user, fg=green, fg_br=True, bg=black)
    await send(user, "> ", drain=True)


async def _setup_screen(user, channel_key):
    """Clear screen, draw layout, set scroll region."""
    # Clear screen
    await ansi_cls(user)

    ansi_wrap(user, False)

    await _draw_header(user, channel_key)
    await _draw_typing_indicator(user, channel_key)
    await _draw_separator(user)
    await _draw_input_prompt(user)

    # Set scroll region: rows 3 to (screen_height - 3) for the chat area
    chat_top = _chat_top()
    chat_bot = _chat_bottom(user)
    await ansi_set_region(user, chat_top, chat_bot)

    # Position cursor in input area
    row = _input_row(user)
    await ansi_move_deferred(user, row=row, col=3, drain=True)


async def _restore_screen(user):
    """Reset scroll region and clear screen on exit."""
    await ansi_set_region(user)  # reset to full screen
    ansi_wrap(user, True)
    await ansi_cls(user)


# ---------------------------------------------------------------------------
# Replay history when joining a channel
# ---------------------------------------------------------------------------

async def _replay_history(user, channel_key):
    ch = channels.get(channel_key)
    if not ch:
        return
    for ts, msg_type, sender, text in ch.history:
        if msg_type == "chat":
            parts = [
                (white, False, f"[{ts}] "),
                (white, True,  f"{sender}"),
                (white, False, f": {text}"),
            ]
        elif msg_type == "action":
            parts = [(cyan, True, f"[{ts}] * {sender} {text}")]
        elif msg_type == "system":
            parts = [(yellow, True, f"-- {text} --")]
        else:
            parts = [(white, False, f"[{ts}] {text}")]
        await _display_message(user, parts, _chat_bottom(user))


# ---------------------------------------------------------------------------
# Channel join / leave helpers
# ---------------------------------------------------------------------------

async def _join_channel(user, channel_key, display_name=None):
    if display_name is None:
        display_name = channel_key.capitalize()

    if channel_key not in channels:
        channels[channel_key] = Channel(display_name)

    ch = channels[channel_key]
    others = sorted(u.handle for u in ch.users if u.handle and u is not user)
    ch.users.add(user)
    user_channels[user] = channel_key

    await _send_system(channel_key, f"{user.handle} has joined")
    # Update header for all users in channel to reflect new user count
    for u in list(ch.users):
      try:
        saved_r, saved_c = u.new_row, u.new_col
        await _draw_header(u, channel_key)
        await ansi_move_deferred(u, row=saved_r, col=saved_c, drain=True)
      except Exception:
        pass
    if others:
      await _send_to_user(user, [(green, False, f"Users here: {', '.join(others)}")])
    else:
      await _send_to_user(user, [(green, False, "You are the only one here.")])


async def _leave_channel(user, quiet=False):
    channel_key = user_channels.get(user)
    if not channel_key:
        return
    ch = channels.get(channel_key)
    if ch:
        ch.users.discard(user)
        if not quiet:
            await _send_system(channel_key, f"{user.handle} has left")
            # Update header for remaining users
            for u in list(ch.users):
              try:
                saved_r, saved_c = u.new_row, u.new_col
                await _draw_header(u, channel_key)
                await ansi_move_deferred(u, row=saved_r, col=saved_c, drain=True)
              except Exception:
                pass
        # Clean up empty non-default channels
        if not ch.users and channel_key != "general":
            del channels[channel_key]
    user_channels.pop(user, None)


# ---------------------------------------------------------------------------
# Command processing
# ---------------------------------------------------------------------------

async def _process_command(user, line):
    """Process a /command.  Returns True if the user should quit."""
    parts = line.split(None, 1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    channel_key = user_channels.get(user, "general")

    if cmd in ("/quit", "/q"):
        return True

    elif cmd in ("/help", "/h"):
        help_lines = [
            "Commands:",
            "  /help, /h          - Show this help",
            "  /who, /w           - List users in channel",
            "  /join <ch>, /j     - Join/switch channel",
            "  /list, /l          - List active channels",
            "  /msg <user> <txt>  - Private message",
            "  /me <action>       - Emote/action",
            "  /topic <text>      - Set channel topic",
            "  /page <user>       - Page user elsewhere on BBS",
            "  /clear             - Clear chat area",
            "  /quit, /q          - Leave teleconference",
        ]
        for h in help_lines:
            await _send_to_user(user, [(green, True, h)])

    elif cmd in ("/who", "/w"):
        ch = channels.get(channel_key)
        if ch:
            handles = sorted(u.handle for u in ch.users if u.handle)
            await _send_to_user(user, [(green, True, f"Users in {ch.name}: {', '.join(handles)}")])
        else:
            await _send_error(user, "You are not in a channel.")

    elif cmd in ("/join", "/j"):
        if not args.strip():
            await _send_error(user, "Usage: /join <channel>")
            return False
        new_key = args.strip().lower()
        new_display = args.strip()
        if new_key == channel_key:
            await _send_error(user, f"You are already in {channels[channel_key].name}.")
            return False
        await _leave_channel(user)
        await _join_channel(user, new_key, new_display)
        # Redraw screen for new channel
        await _setup_screen(user, new_key)
        await _replay_history(user, new_key)

    elif cmd in ("/list", "/l"):
        if not channels:
            await _send_to_user(user, [(green, True, "No active channels.")])
        else:
            await _send_to_user(user, [(green, True, "Active channels:")])
            for key, ch in channels.items():
                topic_str = f" - {ch.topic}" if ch.topic else ""
                await _send_to_user(user, [(green, False, f"  {ch.name} ({len(ch.users)} users){topic_str}")])

    elif cmd in ("/msg", "/m"):
        msg_parts = args.split(None, 1)
        if len(msg_parts) < 2:
            await _send_error(user, "Usage: /msg <user> <message>")
            return False
        target_handle = msg_parts[0]
        msg_text = msg_parts[1]
        from common import global_data
        target = global_data.users.get(target_handle.lower())
        if not target:
            await _send_error(user, f"User '{target_handle}' not found.")
            return False
        await _send_pm(user, target, msg_text)

    elif cmd in ("/me", "/action"):
        if not args.strip():
            await _send_error(user, "Usage: /me <action>")
            return False
        await _send_action(user, channel_key, args.strip())

    elif cmd == "/topic":
        ch = channels.get(channel_key)
        if ch:
            ch.topic = args.strip()
            if ch.topic:
                await _send_system(channel_key, f"{user.handle} set topic to: {ch.topic}")
            else:
                await _send_system(channel_key, f"{user.handle} cleared the topic")
            # Redraw header for all users in channel
            for u in list(ch.users):
                try:
                    saved_r = u.new_row
                    saved_c = u.new_col
                    await _draw_header(u, channel_key)
                    await ansi_move_deferred(u, row=saved_r, col=saved_c, drain=True)
                except (Disconnected, Exception):
                    pass

    elif cmd == "/page":
        msg_parts = args.split(None, 1)
        if not msg_parts or not msg_parts[0].strip():
            await _send_error(user, "Usage: /page <user> [message]")
            return False
        target_handle = msg_parts[0].strip()
        page_text = msg_parts[1].strip() if len(msg_parts) > 1 else None
        from common import global_data
        target = global_data.users.get(target_handle.lower())
        if not target:
            await _send_error(user, f"User '{target_handle}' is not online.")
            return False
        if target is user:
            await _send_error(user, "You can't page yourself.")
            return False
        if target in user_channels:
            await _send_error(user, f"{target.handle} is already in Teleconference. Use /msg instead.")
            return False
        from bbs_msg import send_popup_to_user
        if page_text:
            popup_text = f"{user.handle} says: {page_text}"
        else:
            popup_text = f"{user.handle} is paging you from Teleconference!"
        shown, reason = await send_popup_to_user(
            target_handle, popup_text,
            title="Page", from_user=user.handle, from_handle=user.handle,
            sender=user
        )
        if shown:
            await _send_to_user(user, [(green, True, f"Page sent to {target.handle}.")])
        else:
            await _send_error(user, reason or f"Could not page {target_handle}.")

    elif cmd == "/clear":
        # Clear the chat area by overwriting each line
        chat_top = 2
        chat_bot = _chat_bottom(user)
        for row in range(chat_top, chat_bot + 1):
            await ansi_move_deferred(user, row=row, col=1)
            ansi_color(user, fg=white, bg=black)
            user.writer.write("\x1b[K")
        # Re-position cursor in input area
        await ansi_move_deferred(user, row=_input_row(user), col=3, drain=True)

    else:
        await _send_error(user, f"Unknown command: {cmd}. Type /help for a list of commands.")

    return False


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def run(user, destination, menu_item=None):
    from common import Destinations

    channel_key = "general"

    try:
        await _setup_screen(user, channel_key)
        await _replay_history(user, channel_key)
        await _join_channel(user, channel_key, "General")
        await _draw_header(user, channel_key)
        await ansi_move_deferred(user, row=_input_row(user), col=3, drain=True)

        # Input buffer state
        buf = []
        cursor_pos = 0

        prompt = "> "
        input_row = _input_row(user)

        async def _mark_typing():
            """Record that this user is typing and update the indicator for others."""
            user_typing[user] = time.time()
            current_key = user_channels.get(user, channel_key)
            await _broadcast_typing_indicator(current_key)

        async def _clear_typing():
            """Clear this user's typing state and update the indicator."""
            user_typing.pop(user, None)
            current_key = user_channels.get(user, channel_key)
            await _broadcast_typing_indicator(current_key)

        async def _typing_expiry_task():
            """Background task that clears expired typing indicators."""
            try:
                while True:
                    await asyncio.sleep(2)
                    now = time.time()
                    expired = [u for u, t in list(user_typing.items()) if now - t >= TYPING_TIMEOUT]
                    if expired:
                        for u in expired:
                            user_typing.pop(u, None)
                        # Update indicator for all affected channels
                        updated = set()
                        for u in expired:
                            ck = user_channels.get(u)
                            if ck and ck not in updated:
                                updated.add(ck)
                                await _broadcast_typing_indicator(ck)
            except asyncio.CancelledError:
                pass

        expiry_task = asyncio.create_task(_typing_expiry_task())

        async def _refresh_input():
            """Redraw the input line and place cursor."""
            nonlocal input_row
            input_row = _input_row(user)
            max_visible = user.screen_width - len(prompt)

            if cursor_pos > max_visible:
                scroll_off = cursor_pos - max_visible
            else:
                scroll_off = 0

            visible = "".join(buf[scroll_off:scroll_off + max_visible])

            await ansi_move_deferred(user, row=input_row, col=1)
            ansi_color(user, fg=green, fg_br=True, bg=black)
            await send(user, prompt)
            ansi_color(user, fg=white, fg_br=False, bg=black)
            await send(user, visible)
            user.writer.write("\x1b[K")  # clear to end of line
            display_col = len(prompt) + (cursor_pos - scroll_off) + 1
            await ansi_move_deferred(user, row=input_row, col=display_col, drain=True)

        while True:
            key = await get_input_key(user)

            if isinstance(key, str) and len(key) == 1 and ord(key) >= 32:
                # Printable character
                buf.insert(cursor_pos, key)
                cursor_pos += 1
                await _refresh_input()
                await _mark_typing()

            elif key == back:
                if cursor_pos > 0:
                    cursor_pos -= 1
                    del buf[cursor_pos]
                    await _refresh_input()
                    await _mark_typing()

            elif key == delete:
                if cursor_pos < len(buf):
                    del buf[cursor_pos]
                    await _refresh_input()
                    await _mark_typing()

            elif key == left:
                if cursor_pos > 0:
                    cursor_pos -= 1
                    await _refresh_input()

            elif key == right:
                if cursor_pos < len(buf):
                    cursor_pos += 1
                    await _refresh_input()

            elif key == home:
                if cursor_pos != 0:
                    cursor_pos = 0
                    await _refresh_input()

            elif key == end:
                if cursor_pos != len(buf):
                    cursor_pos = len(buf)
                    await _refresh_input()

            elif key == cr or key == "\n":
                line = "".join(buf).strip()
                buf.clear()
                cursor_pos = 0
                await _clear_typing()

                if line:
                    if line.startswith("/"):
                        should_quit = await _process_command(user, line)
                        if should_quit:
                            break
                    else:
                        current_key = user_channels.get(user, channel_key)
                        await _send_chat(user, current_key, line)

                # Clear input area and redraw prompt
                await _refresh_input()

            elif key == "esc":
                # Treat escape same as /quit
                break

            # Silently ignore other keys (function keys, etc.)

    except Disconnected:
        pass
    finally:
        expiry_task.cancel()
        user_typing.pop(user, None)
        await _leave_channel(user)
        try:
            await _restore_screen(user)
        except (Disconnected, Exception):
            pass

    return RetVals(status=success, next_destination=Destinations.main)
