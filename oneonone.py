"""
One-on-One Split-Screen Chat

Real-time character-by-character private chat between two users.
Top half shows the other person's typing, bottom half is your own editor.
"""

import asyncio

from input_output import send, ansi_move, ansi_move_deferred, ansi_color, ansi_cls, ansi_wrap, get_input_key
from input_fields import show_message_box
from keyboard_codes import *
from definitions import *
from config import get_config
from logger import log

config = get_config()


# ---------------------------------------------------------------------------
# ChatBuffer — lightweight text buffer with cursor and word wrap
# ---------------------------------------------------------------------------

class ChatBuffer:
  """Multi-line text buffer with cursor tracking and word wrap.
  Pure data — no I/O. Rendering is handled separately."""

  def __init__(self, width, max_lines=100):
    self.width = width
    self.max_lines = max_lines
    self.lines = [""]
    self.cursor_line = 0
    self.cursor_col = 0

  def get_display_rows(self):
    """Word-wrap lines into display rows. Returns list of strings."""
    rows = []
    for line in self.lines:
      if not line:
        rows.append("")
      else:
        i = 0
        while i < len(line):
          chunk = line[i:i + self.width]
          # Try to break at word boundary
          if len(chunk) == self.width and i + self.width < len(line):
            last_space = chunk.rfind(' ')
            if last_space > 0:
              chunk = chunk[:last_space + 1]
          rows.append(chunk)
          i += len(chunk)
    return rows

  def cursor_display_pos(self):
    """Return (display_row, display_col) accounting for word wrap."""
    row = 0
    for li in range(len(self.lines)):
      line = self.lines[li]
      if li == self.cursor_line:
        # Find which display row the cursor is on within this line
        if not line:
          return (row, self.cursor_col)
        i = 0
        while i < len(line):
          chunk_end = i + self.width
          chunk = line[i:chunk_end]
          if chunk_end < len(line):
            last_space = chunk.rfind(' ')
            if last_space > 0:
              chunk = chunk[:last_space + 1]
              chunk_end = i + len(chunk)
          if i <= self.cursor_col < chunk_end or chunk_end >= len(line):
            return (row, self.cursor_col - i)
          row += 1
          i = chunk_end
        return (row, 0)
      else:
        # Count display rows for this line
        if not line:
          row += 1
        else:
          i = 0
          while i < len(line):
            chunk_end = i + self.width
            chunk = line[i:chunk_end]
            if chunk_end < len(line):
              last_space = chunk.rfind(' ')
              if last_space > 0:
                chunk_end = i + last_space + 1
            row += 1
            i = chunk_end
    return (row, 0)

  def get_snapshot(self, scroll=0):
    """Return (lines_copy, cursor_line, cursor_col, scroll) for transmission to peer."""
    return (list(self.lines), self.cursor_line, self.cursor_col, scroll)

  def handle_char(self, ch):
    line = self.lines[self.cursor_line]
    self.lines[self.cursor_line] = line[:self.cursor_col] + ch + line[self.cursor_col:]
    self.cursor_col += 1

  def handle_backspace(self):
    if self.cursor_col > 0:
      line = self.lines[self.cursor_line]
      self.lines[self.cursor_line] = line[:self.cursor_col - 1] + line[self.cursor_col:]
      self.cursor_col -= 1
    elif self.cursor_line > 0:
      prev = self.lines[self.cursor_line - 1]
      cur = self.lines[self.cursor_line]
      self.cursor_col = len(prev)
      self.lines[self.cursor_line - 1] = prev + cur
      del self.lines[self.cursor_line]
      self.cursor_line -= 1

  def handle_delete(self):
    line = self.lines[self.cursor_line]
    if self.cursor_col < len(line):
      self.lines[self.cursor_line] = line[:self.cursor_col] + line[self.cursor_col + 1:]
    elif self.cursor_line + 1 < len(self.lines):
      self.lines[self.cursor_line] = line + self.lines[self.cursor_line + 1]
      del self.lines[self.cursor_line + 1]

  def handle_enter(self):
    if len(self.lines) >= self.max_lines:
      return
    line = self.lines[self.cursor_line]
    before = line[:self.cursor_col]
    after = line[self.cursor_col:]
    self.lines[self.cursor_line] = before
    self.lines.insert(self.cursor_line + 1, after)
    self.cursor_line += 1
    self.cursor_col = 0

  def handle_left(self):
    if self.cursor_col > 0:
      self.cursor_col -= 1
    elif self.cursor_line > 0:
      self.cursor_line -= 1
      self.cursor_col = len(self.lines[self.cursor_line])

  def handle_right(self):
    line = self.lines[self.cursor_line]
    if self.cursor_col < len(line):
      self.cursor_col += 1
    elif self.cursor_line + 1 < len(self.lines):
      self.cursor_line += 1
      self.cursor_col = 0

  def handle_up(self):
    if self.cursor_line > 0:
      self.cursor_line -= 1
      self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_line]))

  def handle_down(self):
    if self.cursor_line + 1 < len(self.lines):
      self.cursor_line += 1
      self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_line]))

  def handle_home(self):
    self.cursor_col = 0

  def handle_end(self):
    self.cursor_col = len(self.lines[self.cursor_line])


# ---------------------------------------------------------------------------
# Rendering — draw a buffer or snapshot onto a user's screen
# ---------------------------------------------------------------------------

async def _draw_pane(user, display_rows, top_row, height, width, col_offset,
                     fg, fg_br, bg, cursor_pos=None, scroll_offset=0):
  """Draw display rows into a screen region. Clears unused rows.
  cursor_pos: (row, col) within the display rows to place the terminal cursor."""
  for i in range(height):
    ri = scroll_offset + i
    await ansi_move(user, top_row + i, col_offset)
    ansi_color(user, fg=fg, fg_br=fg_br, bg=bg)
    if ri < len(display_rows):
      text = display_rows[ri][:width]
      await send(user, text.ljust(width), drain=False)
    else:
      await send(user, " " * width, drain=False)

  if cursor_pos is not None:
    cr_row, cr_col = cursor_pos
    screen_row = top_row + cr_row - scroll_offset
    screen_col = col_offset + cr_col
    if top_row <= screen_row < top_row + height:
      await ansi_move(user, screen_row, screen_col)

  await user.writer.drain()


async def _draw_separator(user, row, width, fg=white, fg_br=False):
  """Draw a horizontal separator line."""
  bar = bytes([196]).decode('cp437') * width
  await ansi_move(user, row, 1)
  ansi_color(user, fg=fg, fg_br=fg_br, bg=black)
  await send(user, bar, drain=False)


async def _draw_header(user, peer_handle, width):
  """Draw the header line."""
  title = f" One-on-One Chat with {peer_handle} "
  padded = title.center(width)
  await ansi_move(user, 1, 1)
  ansi_color(user, fg=black, bg=cyan, fg_br=False, bg_br=False)
  await send(user, padded, drain=False)


async def _draw_status(user, row, width):
  """Draw the status bar."""
  status = " ESC to exit "
  padded = status.ljust(width)
  ansi_wrap(user, False)
  await ansi_move(user, row, 1)
  ansi_color(user, fg=black, bg=white, fg_br=False, bg_br=False)
  await send(user, padded, drain=False)
  ansi_wrap(user, True)


async def _draw_status_msg(user, row, width, msg):
  """Draw a status bar with a custom message."""
  padded = msg.ljust(width)
  ansi_wrap(user, False)
  await ansi_move(user, row, 1)
  ansi_color(user, fg=white, bg=red, fg_br=True, bg_br=False)
  await send(user, padded, drain=True)
  ansi_wrap(user, True)


# ---------------------------------------------------------------------------
# Chat session
# ---------------------------------------------------------------------------

class ChatSession:
  """Manages a one-on-one chat between two users."""

  def __init__(self, user_a, user_b):
    self.user_a = user_a
    self.user_b = user_b
    self.active = True

    # Screen layout
    h = min(user_a.screen_height, user_b.screen_height)
    w = min(user_a.screen_width, user_b.screen_width)
    self.height = h
    self.width = w
    self.sep_row = h // 2 + 1
    self.peer_top = 2  # rows 2 to sep_row-1
    self.peer_height = self.sep_row - self.peer_top
    self.own_top = self.sep_row + 1  # rows sep_row+1 to h-1
    self.own_height = h - 1 - self.own_top  # leave last row for status
    self.status_row = h

    # Buffers
    self.buffer_a = ChatBuffer(w, max_lines=50)
    self.buffer_b = ChatBuffer(w, max_lines=50)

    # Shared snapshots for peer display (set by one user, read by the other)
    self.snapshot_a = ([""], 0, 0, 0)
    self.snapshot_b = ([""], 0, 0, 0)

    # Events to notify the other user that a snapshot changed
    self.event_a = asyncio.Event()  # set when B should redraw A's content
    self.event_b = asyncio.Event()  # set when A should redraw B's content

    # Per-user scroll tracking for own pane
    self._own_scroll = {}

  async def setup_screen(self, user):
    """Set up one user's screen for the chat."""
    peer = self.user_b.handle if user is self.user_a else self.user_a.handle
    await ansi_cls(user)
    ansi_wrap(user, False)
    await _draw_header(user, peer, self.width)
    await _draw_separator(user, self.sep_row, self.width, fg=cyan, fg_br=True)
    await _draw_status(user, self.status_row, self.width)
    await user.writer.drain()
    ansi_wrap(user, True)

  async def _user_loop(self, user, own_buffer, peer_buffer,
                       my_update_event, peer_update_event, side):
    """Per-user input loop."""
    own_snapshot_attr = f'snapshot_{side}'
    peer_side = 'b' if side == 'a' else 'a'
    peer_snapshot_attr = f'snapshot_{peer_side}'

    try:
      while True:
        if not self.active:
          # Other user left — show message and wait for ESC
          await _draw_status_msg(user, self.status_row, self.width,
                                  " Other user has left. Press ESC to exit. ")
          while True:
            key = await self._read_key(user, my_update_event)
            if key == "esc" or key == "\x1b":
              return
            if key == 'chat_update' or key == 'popup':
              continue

        # Wait for either: user input, peer update, or popup
        key = await self._read_key(user, my_update_event)

        if key == 'chat_update':
          # Peer typed something — redraw peer pane using peer's scroll offset
          snap = getattr(self, peer_snapshot_attr)
          peer_buf_temp = ChatBuffer(self.width)
          peer_buf_temp.lines = list(snap[0])
          peer_buf_temp.cursor_line = snap[1]
          peer_buf_temp.cursor_col = snap[2]
          display = peer_buf_temp.get_display_rows()
          cpos = peer_buf_temp.cursor_display_pos()
          scroll = snap[3] if len(snap) > 3 else max(0, len(display) - self.peer_height)
          await _draw_pane(user, display, self.peer_top, self.peer_height,
                           self.width, 1, fg=white, fg_br=False, bg=black,
                           cursor_pos=None, scroll_offset=scroll)
          # Reposition cursor to own pane
          own_cpos = own_buffer.cursor_display_pos()
          own_scroll = self._own_scroll.get(id(user), 0)
          cur_r, cur_c = own_cpos
          await ansi_move(user, self.own_top + cur_r - own_scroll, 1 + cur_c)
          await user.writer.drain()
          continue

        if key == 'popup':
          # Popup was handled by _drain_popup_queue, just continue
          continue

        # Handle ESC — exit chat
        if key == "esc" or key == "\x1b":
          return

        # Handle editing keys
        if key == cr:
          own_buffer.handle_enter()
        elif key == back:
          own_buffer.handle_backspace()
        elif key == delete:
          own_buffer.handle_delete()
        elif key == left:
          own_buffer.handle_left()
        elif key == right:
          own_buffer.handle_right()
        elif key == up:
          own_buffer.handle_up()
        elif key == down:
          own_buffer.handle_down()
        elif key == home:
          own_buffer.handle_home()
        elif key == end:
          own_buffer.handle_end()
        elif isinstance(key, str) and len(key) == 1 and ord(key) >= 32:
          own_buffer.handle_char(key)
        else:
          continue  # ignore unrecognized keys

        # Redraw own pane — scroll follows cursor
        display = own_buffer.get_display_rows()
        cpos = own_buffer.cursor_display_pos()
        cursor_row = cpos[0]
        # Ensure cursor is visible within the pane
        if not hasattr(self, '_own_scroll'):
          self._own_scroll = {}
        scroll = self._own_scroll.get(id(user), 0)
        if cursor_row < scroll:
          scroll = cursor_row
        elif cursor_row >= scroll + self.own_height:
          scroll = cursor_row - self.own_height + 1
        scroll = max(0, scroll)
        self._own_scroll[id(user)] = scroll
        await _draw_pane(user, display, self.own_top, self.own_height,
                         self.width, 1, fg=white, fg_br=True, bg=black,
                         cursor_pos=cpos, scroll_offset=scroll)

        # Push snapshot for peer (include scroll offset so peer sees the same view)
        setattr(self, own_snapshot_attr, own_buffer.get_snapshot(scroll=scroll))
        peer_update_event.set()

    except Disconnected:
      return
    except asyncio.CancelledError:
      return

  async def _read_key(self, user, chat_event):
    """Read a key from user, but also wake on chat updates or popups.
    Returns the key, 'chat_update', or 'popup'."""
    from input_output import _drain_popup_queue
    await _drain_popup_queue(user)

    while True:
      read_task = asyncio.ensure_future(user.reader.read(1))
      chat_task = asyncio.ensure_future(chat_event.wait())
      notify_task = asyncio.ensure_future(user.popup_notify.wait())

      try:
        done, pending = await asyncio.wait(
          [read_task, chat_task, notify_task],
          return_when=asyncio.FIRST_COMPLETED)

        for t in pending:
          t.cancel()
          try:
            await t
          except (asyncio.CancelledError, Exception):
            pass

        if chat_task in done:
          chat_event.clear()
          if read_task in done:
            # Both fired — process the chat update, key will be handled next loop
            char = read_task.result()
            if char:
              # Put the char back by processing it
              return await self._process_char(user, char)
          return 'chat_update'

        if notify_task in done:
          user.popup_notify.clear()
          await _drain_popup_queue(user)
          if read_task in done:
            char = read_task.result()
            if char:
              return await self._process_char(user, char)
          return 'popup'

        if read_task in done:
          char = read_task.result()
          if not char:
            raise Disconnected()
          return await self._process_char(user, char)

      except asyncio.CancelledError:
        read_task.cancel()
        chat_task.cancel()
        notify_task.cancel()
        raise

  async def _process_char(self, user, char):
    """Process a raw character through keyboard code parsing.
    Returns parsed key or the character itself."""
    from keyboard_codes import check, check_partial
    if char in "\x00\x1b":
      # Start of escape sequence — collect more chars
      buf = char
      for _ in range(10):
        try:
          next_char = await asyncio.wait_for(user.reader.read(1), timeout=0.05)
        except asyncio.TimeoutError:
          break
        if not next_char:
          break
        buf += next_char
        r = check(buf)
        if r and r != partial_code:
          return r
        if not check_partial(buf):
          break
      r = check(buf)
      if r and r != partial_code:
        return r
      if buf == "\x1b":
        return "esc"
      return None  # unrecognized sequence
    r = check(char)
    if r and r != partial_code:
      return r
    return char


# ---------------------------------------------------------------------------
# Pending sessions — shared between inviter and target
# ---------------------------------------------------------------------------

_pending_sessions = {}  # user -> ChatSession (target user looks up their session here)


# ---------------------------------------------------------------------------
# Invitation and entry point
# ---------------------------------------------------------------------------

async def send_chat_invitation(from_user, to_handle):
  """Send a chat invitation. Returns (accepted: bool, reason: str)."""
  from common import global_data

  target = global_data.users.get(to_handle.lower())
  if not target:
    return False, f"User '{to_handle}' is not online."

  if target is from_user:
    return False, "You can't chat with yourself."

  # Can't chat while either user is in a door
  if from_user.in_door:
    return False, "You can't start a chat while in a door game."
  if target.in_door:
    return False, f"{to_handle} is in a door game."

  # Check if target allows chat invitations
  is_sysop = hasattr(from_user, 'keys') and 'sysop' in from_user.keys
  target_conf = getattr(target, 'conf', null)
  if not is_sysop and target_conf and target_conf is not null:
    allow_chat = target_conf.allow_chat
    if allow_chat is not null and allow_chat is not None:
      if isinstance(allow_chat, bool) and not allow_chat:
        return False, f"{to_handle} has chat invitations disabled."
      elif isinstance(allow_chat, str) and allow_chat.lower() in ("false", "no", "0", "off"):
        return False, f"{to_handle} has chat invitations disabled."

  # Check if sender is blocked by target
  if not is_sysop:
    target_conf_val = getattr(target, 'conf', null)
    blocked = []
    if target_conf_val and target_conf_val is not null:
      b = target_conf_val.blocked_users
      if b and b is not null:
        blocked = [str(h).lower() for h in b] if isinstance(b, list) else []
    if from_user.handle and from_user.handle.lower() in blocked:
      return False, f"{to_handle} is not available."

  # Send invitation popup to target and wait for response
  # We use a Future that the target resolves
  invitation_future = asyncio.get_event_loop().create_future()
  target._chat_invitation = (from_user, invitation_future)
  target.popup_notify.set()

  try:
    accepted = await asyncio.wait_for(invitation_future, timeout=30.0)
  except asyncio.TimeoutError:
    target._chat_invitation = None
    return False, f"{to_handle} didn't respond in time."

  if not accepted:
    return False, f"{to_handle} declined."

  return True, None


async def _handle_invitation(user):
  """Show chat invitation Y/N popup. Called from popup drain.
  Returns True if accepted, False if declined."""
  inv = getattr(user, '_chat_invitation', None)
  if not inv:
    return False
  from_user, future = inv
  user._chat_invitation = None

  text = (f"{from_user.handle} wants to chat with you.\n\n"
          "Press Y to accept, any other key to decline.")
  while True:
    key = await show_message_box(
      user, text, title="Chat Invitation",
      fg=white, fg_br=True, bg=black,
      outline_fg=cyan, outline_fg_br=True,
      return_key=True,
    )
    # Ignore mouse events / non-string keys — re-show the popup
    if not isinstance(key, str):
      continue
    accepted = (key.lower() == 'y')
    if not future.done():
      future.set_result(accepted)
    return accepted


async def _run_invitee_session(user, session):
  """Run the invitee's side of an existing ChatSession. Shared by the
  legacy destination path and the inline overlay path."""
  side = 'b' if user is session.user_b else 'a'
  own_buf = session.buffer_b if side == 'b' else session.buffer_a
  peer_buf = session.buffer_a if side == 'b' else session.buffer_b
  my_event = session.event_b if side == 'b' else session.event_a
  peer_event = session.event_a if side == 'b' else session.event_b

  # Signal the inviter that we've joined
  session.joined.set()

  await session.setup_screen(user)
  try:
    await session._user_loop(user, own_buf, peer_buf, my_event, peer_event, side)
  except (Disconnected, asyncio.CancelledError):
    pass
  finally:
    session.active = False
    peer_event.set()  # wake the other user so they notice we left


async def run_invitee_overlay(user):
  """Wait for the inviter to create a ChatSession, then run the invitee
  side of the chat. The caller is responsible for push_screen / pop_screen
  around this call so the underlying activity is preserved and restored."""
  ev = getattr(user, '_chat_session_ready', None)
  if ev is None:
    user._chat_session_ready = asyncio.Event()
    ev = user._chat_session_ready
  try:
    await asyncio.wait_for(ev.wait(), timeout=10.0)
  except asyncio.TimeoutError:
    log.info("Invitee %s timed out waiting for chat session", getattr(user, 'handle', '?'))
    return
  ev.clear()

  session = _pending_sessions.pop(user, None)
  if not session:
    return

  await _run_invitee_session(user, session)


async def run(user, dest_conf, menu_item=None):
  """Module entry point — start a one-on-one chat.
  If user has a pending session (was invited and accepted), join it.
  Otherwise, prompt for a target handle and send an invitation."""
  from common import Destinations, global_data
  from input_fields import InputField

  # Inviter flow — prompt for target
  target_handle = None
  if menu_item and menu_item is not null:
    if isinstance(menu_item, tuple):
      target_handle = str(menu_item[0]).strip()
    else:
      target_handle = str(menu_item).strip()

  if not target_handle:
    await ansi_cls(user)
    ansi_color(user, fg=white, bg=black, fg_br=True)
    await send(user, "One-on-One Chat" + cr + lf + cr + lf, drain=False)
    ansi_color(user, fg=white, bg=black, fg_br=False)
    await send(user, "Chat with: ", drain=True)
    r = await InputField.create(user=user, conf=config.input_fields.input_field,
                                 width=30, max_length=50)
    target_handle = r.content.strip() if hasattr(r, 'content') else ""
    if not target_handle:
      return RetVals(status=success, next_destination=Destinations.main)

  err = await chat_with(user, target_handle)
  if err:
    await show_message_box(user, err, title="Chat",
                           fg=white, fg_br=True, bg=black,
                           outline_fg=red, outline_fg_br=True)
  return RetVals(status=success, next_destination=Destinations.main)


async def chat_with(user, target_handle):
  """Inviter side of a one-on-one chat. Sends an invitation, runs the chat
  session if accepted. Returns None on success, or an error string on
  failure (target offline, declined, timeout, etc.).

  The caller is responsible for push_screen / pop_screen if it wants the
  underlying activity restored after the chat ends. Suitable for inline
  use from teleconference, /j, slash commands, etc."""
  from common import global_data

  await ansi_cls(user)
  ansi_color(user, fg=white, bg=black, fg_br=True)
  await send(user, f"Waiting for {target_handle} to accept..." + cr + lf, drain=True)

  accepted, reason = await send_chat_invitation(user, target_handle)
  if not accepted:
    return reason

  target = global_data.users.get(target_handle.lower())
  if not target:
    return f"User '{target_handle}' is no longer online."

  session = ChatSession(user, target)
  session.joined = asyncio.Event()

  # Hand the session off to the invitee, who is parked in
  # _drain_popup_queue waiting on _chat_session_ready.
  _pending_sessions[target] = session
  if not hasattr(target, '_chat_session_ready') or target._chat_session_ready is None:
    target._chat_session_ready = asyncio.Event()
  target._chat_session_ready.set()

  try:
    await asyncio.wait_for(session.joined.wait(), timeout=10.0)
  except asyncio.TimeoutError:
    _pending_sessions.pop(target, None)
    return f"{target_handle} failed to join the chat."

  await session.setup_screen(user)
  try:
    await session._user_loop(user, session.buffer_a, session.buffer_b,
                              session.event_a, session.event_b, 'a')
  except (Disconnected, asyncio.CancelledError):
    pass
  finally:
    session.active = False
    session.event_b.set()

  return None
