# todo: change fg, bg, fg_br, bg_br to fg, fg_br, bg, bg_br

import asyncio as _asyncio_for_lock
import time

from definitions import *
from keyboard_codes import *


class ReentrantAsyncLock:
  """A reentrant async lock — same task can re-acquire without deadlock.
  Used as the per-user write lock so background tasks (e.g. ambient stars)
  can safely call locking I/O helpers from inside their own held lock."""
  def __init__(self):
    self._lock = _asyncio_for_lock.Lock()
    self._owner = None
    self._depth = 0

  async def acquire(self):
    task = _asyncio_for_lock.current_task()
    if self._owner is task:
      self._depth += 1
      return
    await self._lock.acquire()
    self._owner = task
    self._depth = 1

  def release(self):
    self._depth -= 1
    if self._depth == 0:
      self._owner = None
      self._lock.release()

  async def __aenter__(self):
    await self.acquire()
    return self

  async def __aexit__(self, exc_type, exc, tb):
    self.release()

def _blank_cell(user):
  """A space cell using the user's current color attrs — matches what the
  terminal actually shows when CLS or scroll fills with the current bg."""
  return Char(' ', user.cur_fg, user.cur_fg_br, user.cur_bg, user.cur_bg_br)

def emu_scroll(user): # todo: add scroll region paramaters?
  del user.screen[0]
  user.screen.append([_blank_cell(user) for _ in range(user.screen_width)])

def emu_clear(user):
  for x in range(len(user.screen)):
    user.screen[x] = [_blank_cell(user) for col in range(user.screen_width)]
  user.cur_col = user.cur_row = 1

async def send(user, message, word_wrap=False, drain=False):
  async with user.write_lock:
    await _send_locked(user, message, drain)

async def _send_locked(user, message, drain):
  if message or drain:
    await ansi_move_2(user)
    await ansi_color_2(user)
  if message:
    # On UTF-8 terminals, remap CP437 low-byte glyph code points (e.g.
    # '\x0f' → '☼') so callers can keep using the byte form and have the
    # visible glyph appear regardless of encoding. Only the bytes going
    # to the wire are translated; the screen model below still stores the
    # original characters so callers can match against the byte form.
    if getattr(user, 'encoding', 'cp437') == 'utf-8':
      user.writer.write(message.translate(CP437_LOW_TO_UTF8_TRANSLATION))
    else:
      user.writer.write(message)
  if drain:
    await user.writer.drain()
  for char in message:
    if char=="\x00":
      pass
    elif char=="\x08":
      user.cur_col = max(user.cur_col-1, 1)
    elif char=="\x09":
      user.cur_col = (user.cur_col//8)*8+8
    elif char=="\x0a":
      if user.cur_row < user.screen_height:
        user.cur_row += 1
      else:
        emu_scroll(user)
    elif char=="\x0c":
      emu_clear(user)
      user.cur_col = user.cur_row = 1
    elif char=="\x0d":
      user.cur_col = 1
    else:
      if user.terminal == PuTTy and ord(char)<32:
        return
      if user.screen and 0 < user.cur_row <= len(user.screen) and 0 < user.cur_col <= len(user.screen[0]):
        user.screen[user.cur_row-1][user.cur_col-1] = Char(char, fg=user.cur_fg, fg_br=user.cur_fg_br, bg=user.cur_bg, bg_br=user.cur_bg_br)
      if not user.cur_wrap:
        user.cur_col = min(user.cur_col+1, user.screen_width)
      else:
        if user.cur_col==user.screen_width:
          # After writing to the last column, the cursor position is ambiguous:
          # deferred-wrap terminals keep cursor at col 80, immediate-wrap terminals
          # move to col 1 of the next row. We track as wrapped (col 1, next row)
          # and set a flag so ansi_move_2 uses absolute positioning next time.
          if user.cur_row==user.screen_height:
            emu_scroll(user)
          else:
            user.cur_row += 1
          user.cur_col = 1
          user._wrap_ambiguous = True
        else:
          user.cur_col += 1
  # Keep new_row/new_col in sync so the next send() doesn't reposition backwards
  user.new_row = user.cur_row
  user.new_col = user.cur_col

async def send_wrapped(user, text, drain=False):
  """Send text with word wrapping to the user's screen width.
  Wraps at word boundaries, respecting the current cursor column.
  Sends cr+lf for line breaks."""
  width = user.screen_width
  words = text.split(' ')
  col = user.cur_col  # 1-based current column
  first = True
  for word in words:
    word_len = len(word)
    if first:
      # First word — just send it
      await send(user, word, drain=False)
      col += word_len
      first = False
    elif col + 1 + word_len <= width:
      # Fits on this line with a space
      await send(user, ' ' + word, drain=False)
      col += 1 + word_len
    else:
      # Wrap to next line
      await send(user, cr + lf + word, drain=False)
      col = 1 + word_len
  if drain:
    await user.writer.drain()


import re as _re
_markup_re = _re.compile(r'\{!([^}]*)\}')

async def send_markup(user, text, fg=white, bg=black, fg_br=False, bg_br=False, drain=False):
  """Send text with inline color markup tags.
  Tags use {!color} syntax where color is a color name from definitions.py.
  Options: {!red} {!red,br} {!white,on_blue} {!red,br,on_blue,bg_br}
  {!} resets to the default fg/bg passed to this function.
  Text outside tags is sent with the current color state."""
  default_fg, default_bg = fg, bg
  default_fg_br, default_bg_br = fg_br, bg_br
  ansi_color(user, fg=fg, bg=bg, fg_br=fg_br, bg_br=bg_br)

  pos = 0
  for m in _markup_re.finditer(text):
    # Send text before this tag
    if m.start() > pos:
      await send(user, text[pos:m.start()], drain=False)
    pos = m.end()

    # Parse the tag
    tag = m.group(1).strip()
    if not tag:
      # {!} = reset to defaults
      ansi_color(user, fg=default_fg, bg=default_bg, fg_br=default_fg_br, bg_br=default_bg_br)
    else:
      kwargs = {}
      for part in tag.split(','):
        part = part.strip().lower()
        if part == 'br':
          kwargs['fg_br'] = True
        elif part == 'nobr':
          kwargs['fg_br'] = False
        elif part == 'bg_br':
          kwargs['bg_br'] = True
        elif part == 'nobg_br':
          kwargs['bg_br'] = False
        elif part.startswith('on_'):
          color_name = part[3:]
          if color_name in colors:
            kwargs['bg'] = colors[color_name]
        elif part in colors:
          kwargs['fg'] = colors[part]
      if kwargs:
        ansi_color(user, **kwargs)

  # Send remaining text after last tag
  if pos < len(text):
    await send(user, text[pos:], drain=False)

  if drain:
    await user.writer.drain()


def ansi_wrap(user, wrap=True):
  if user.cur_wrap != wrap:
    if wrap:
      user.writer.write("\x1b[?7h") 
    else:
      user.writer.write("\x1b[?7l") 
    user.cur_wrap = wrap

# todo: have an ansi_leftright and an ansi_updown which can take negative numbers and call the appropriate function, just for convenience?

async def ansi_move(user, row, col, drain=False):
  """Move cursor using absolute positioning. Always sends ESC[row;colH
  regardless of current tracked state, and syncs all tracking."""
  async with user.write_lock:
    user.writer.write(f"\x1b[{row};{col}H")
    user.cur_row = user.new_row = row
    user.cur_col = user.new_col = col
    user._wrap_ambiguous = False
    if drain:
      await user.writer.drain()

async def ansi_hide_cursor(user, drain=False):
  async with user.write_lock:
    if getattr(user, 'cur_show_cursor', True):
      user.cur_show_cursor = False
      user.writer.write("\x1b[?25l")
      if drain:
        await user.writer.drain()

async def ansi_show_cursor(user, drain=False):
  async with user.write_lock:
    if not getattr(user, 'cur_show_cursor', True):
      user.cur_show_cursor = True
      user.writer.write("\x1b[?25h")
      if drain:
        await user.writer.drain()

async def ansi_left(user, val=1, drain=False):
  assert val >= 0
  user.new_col = max(user.new_col-val, 1)
  if drain:
    await ansi_move_2(user, drain)
  
async def ansi_right(user, val=1, drain=False):
  assert val >= 0
  user.new_col = min(user.new_col+val, user.screen_width)
  if drain:
    await ansi_move_2(user, drain)
  
async def ansi_up(user, val=1, drain=False): 
  assert val >= 0
  user.new_row = max(user.new_row-val, 1)
  if drain:
    await ansi_move_2(user, drain)

async def ansi_down(user, val=1, drain=False): 
  assert val >= 0
  user.new_row = min(user.new_row+val, user.screen_height)
  if drain:
    await ansi_move_2(user, drain)

async def ansi_move_deferred(user, row=None, col=None, drain=False): # we have the drain option because if we're moving the cursor in(to) an input field, the user will want to see where he's about to type.
  user.new_row = row if row else user.new_row
  user.new_col = col if col else user.new_col
  user.new_row = max(1, min(user.new_row, user.screen_height or 25))
  user.new_col = max(1, min(user.new_col, user.screen_width or 80))
  if drain:
    await ansi_move_2(user, drain)

async def ansi_move_2(user, drain=False):
  async with user.write_lock:
    await _ansi_move_2_locked(user, drain)

async def _ansi_move_2_locked(user, drain=False):
  # After writing to the last column, cursor position is ambiguous between terminal
  # types (deferred vs immediate wrap). Force absolute positioning to be safe.
  if user._wrap_ambiguous:
    user._wrap_ambiguous = False
    if user.cur_row != user.new_row or user.cur_col != user.new_col:
      user.cur_row = min(user.new_row, user.screen_height)
      user.cur_col = min(user.new_col, user.screen_width)
      user.writer.write(f"\x1b[{user.cur_row};{user.cur_col}H")
      if drain:
        await user.writer.drain()
      return
    # Position matches — but still ambiguous, so send absolute anyway
    user.writer.write(f"\x1b[{user.cur_row};{user.cur_col}H")
    if drain:
      await user.writer.drain()
    return

  if user.cur_row != user.new_row and user.cur_col != user.new_col:
    user.cur_row = min(user.new_row, user.screen_height)
    user.cur_col = min(user.new_col, user.screen_width)
    user.writer.write(f"\x1b[{user.cur_row};{user.cur_col}H")
  elif user.cur_row == user.new_row and user.cur_col != user.new_col:
    if user.new_col > user.cur_col: # go right
      val = user.new_col - user.cur_col
      if val == 1:
        user.writer.write("\x1b[C")
      else:
        user.writer.write(f"\x1b[{val}C")
    else: # go left
      val = user.cur_col - user.new_col
      if val == 1:
        user.writer.write(back)
      elif val <= 3 or user.cur_col <= 4:
        user.writer.write(back * min(val, user.cur_col - 1))
      else:
        user.writer.write(f"\x1b[{val}D")
  elif user.cur_row != user.new_row and user.cur_col == user.new_col:
    if user.new_row < user.cur_row: # go up
      val = user.cur_row - user.new_row
      if val == 1:
        user.writer.write("\x1b[A")
      else:
        user.writer.write(f"\x1b[{val}A")
    else: # go down
      val = user.new_row - user.cur_row
      if val <= 3:
        user.writer.write(lf * min(val, user.screen_height - user.cur_row))
      else:
        user.writer.write(f"\x1b[{val}B")
  else: # no change
    return
  user.cur_row = user.new_row
  user.cur_col = user.new_col
  if drain:
    await user.writer.drain()

def ansi_color(user, fg=None, bg=None, fg_br=None, bg_br=None, drain=False):
  """Set pending color state. Colors are sent on the next send() call.
  Call with no args to reset to default (white on black).
  drain=True writes the color codes to the buffer immediately (via ansi_color_2)."""
  if fg is None and bg is None and fg_br is None and bg_br is None:
    user.new_fg = white
    user.new_bg = black
    user.new_fg_br = False
    user.new_bg_br = False
  else:
    user.new_fg = user.cur_fg if fg is None else fg
    user.new_bg = user.cur_bg if bg is None else bg
    user.new_fg_br = user.cur_fg_br if fg_br is None else fg_br
    user.new_bg_br = user.cur_bg_br if bg_br is None else bg_br
  if drain:
    _ansi_color_write(user)

def _ansi_color_write(user):
  """Write color escape codes to the buffer (synchronous). Called by ansi_color(drain=True) and ansi_color_2."""
  # note: syncterm blinks instead of bright background
  codes = []
  if (user.new_fg == white and user.new_bg == black and user.new_fg_br == False and user.new_bg_br == False) and (user.cur_fg != white or user.cur_bg != black or user.cur_fg_br != False or user.cur_bg_br != False):
    user.writer.write("\x1b[m")
    user.cur_fg = white
    user.cur_bg = black
    user.cur_fg_br = False
    user.cur_bg_br = False
  else:
    if user.new_fg_br != user.cur_fg_br:
      if user.new_fg_br:
        codes.append("1")
      else:
        codes.append("22")
      user.cur_fg_br = user.new_fg_br
    if user.new_bg_br != user.cur_bg_br:
      if user.new_bg_br:
        codes.append("5")
        user.cur_bg_br = True
      else:
        codes.append("25")
      user.cur_bg_br = user.new_bg_br
    if user.new_fg != user.cur_fg:
      codes.append(str(user.new_fg+30))
      user.cur_fg = user.new_fg
    if user.new_bg != user.cur_bg:
      codes.append(str(user.new_bg+40))
      user.cur_bg = user.new_bg
    if codes:
      user.writer.write(f"\x1b[{';'.join(codes)}m")

async def ansi_color_2(user, drain=False):
  async with user.write_lock:
    _ansi_color_write(user)
    if drain:
      await user.writer.drain()

async def ansi_cls(user, fg=None, bg=None, fg_br=None, bg_br=None):
  async with user.write_lock:
    ansi_color(user, fg=fg, fg_br=fg_br, bg=bg, bg_br=bg_br, drain=True)
    user.writer.write("\x1b[2J\x1b[H")
    emu_clear(user)
    user.cur_row = user.new_row = 1
    user.cur_col = user.new_col = 1
    user._wrap_ambiguous = False
    await user.writer.drain()
    # Let any registered post-cls hook (e.g. ambient stars) repaint itself
    hook = getattr(user, '_post_cls_hook', None)
    if hook is not None:
      try:
        await hook(user)
      except Exception:
        pass

async def ansi_del_to_end(user, drain=False):
  async with user.write_lock:
    user.writer.write("\x1b[J")
    user.screen[user.cur_row] = user.screen[user.cur_row][:user.cur_col]
    if drain:
      await user.writer.drain()

async def ansi_set_region(user, top_row=None, bottom_row=None, drain=False):
  async with user.write_lock:
    if user.scroll_region_top != top_row or user.scroll_region_bottom != bottom_row:
      if bottom_row is None:
        if top_row is None:
          user.writer.write("\x1b[r")
        else:
          user.writer.write(f"\x1b{top_row}r")
      else:
        user.writer.write(f"\x1b[{top_row};{bottom_row}r")
      user.scroll_region_top = top_row
      user.scroll_region_bottom = bottom_row
      if drain:
        await user.writer.drain()

async def ansi_set_region_strict(user, value=True, drain=False):
  async with user.write_lock:
    if value != user.scroll_region_strict:
      user.scroll_region_strict = value
      if value:
        user.writer.write(f"\x1b[?6h")
      else:
        user.writer.write(f"\x1b[?7h")
      if drain:
        await user.writer.drain()

# ---------------------------------------------------------------------------
# Screen save/restore stack — used for overlay activities (e.g. /chat) that
# take over the screen and need to restore the underlying activity afterward.
# ---------------------------------------------------------------------------

def _snapshot_screen(user):
  """Capture full screen state for later restore."""
  screen_copy = None
  if user.screen:
    screen_copy = [
      [Char(c.char, c.fg, c.fg_br, c.bg, c.bg_br) for c in row]
      for row in user.screen
    ]
  return {
    'screen': screen_copy,
    'width': user.screen_width,
    'height': user.screen_height,
    'cur_row': user.cur_row,
    'cur_col': user.cur_col,
    'new_row': user.new_row,
    'new_col': user.new_col,
    'cur_fg': user.cur_fg, 'cur_fg_br': user.cur_fg_br,
    'cur_bg': user.cur_bg, 'cur_bg_br': user.cur_bg_br,
    'cur_wrap': getattr(user, 'cur_wrap', True),
    'mouse_reporting': getattr(user, 'mouse_reporting', False),
    'stars_active': list(getattr(user, '_stars_active', None) or []),
  }

async def push_screen(user):
  """Save the current screen onto user.screen_stack so it can be restored
  later by pop_screen. Use this before an overlay activity (e.g. /chat) takes
  over the terminal."""
  if not hasattr(user, 'screen_stack') or user.screen_stack is None:
    user.screen_stack = []
  user.screen_stack.append(_snapshot_screen(user))

async def pop_screen(user):
  """Restore the most recently push_screen'd screen state. Repaints every
  cell from the snapshot, then restores cursor position, color, wrap, and
  mouse reporting state. No-op if the stack is empty."""
  stack = getattr(user, 'screen_stack', None)
  if not stack:
    return
  snap = stack.pop()

  await ansi_cls(user)
  prev_wrap = getattr(user, 'cur_wrap', True)
  ansi_wrap(user, False)

  if snap['screen']:
    height = len(snap['screen'])
    width = len(snap['screen'][0]) if height else 0
    for r_idx in range(height):
      row = snap['screen'][r_idx]
      c_idx = 0
      while c_idx < width:
        ch = row[c_idx]
        # Skip default cells (already cleared)
        if ch.char == ' ' and ch.fg == 7 and not ch.fg_br and ch.bg == 0 and not ch.bg_br:
          c_idx += 1
          continue
        # Find a run of cells with identical color attrs
        run_start = c_idx
        run_chars = [ch.char]
        c_idx += 1
        while c_idx < width:
          n = row[c_idx]
          if (n.fg == ch.fg and n.fg_br == ch.fg_br
              and n.bg == ch.bg and n.bg_br == ch.bg_br):
            # Stop the run if the next cell is a default-blank — let the
            # outer loop's skip handle it (saves a redundant write).
            if (n.char == ' ' and n.fg == 7 and not n.fg_br
                and n.bg == 0 and not n.bg_br):
              break
            run_chars.append(n.char)
            c_idx += 1
          else:
            break
        # Skip writing the very last cell of the very last row to avoid
        # the terminal scrolling on auto-wrap.
        if r_idx == height - 1 and run_start + len(run_chars) >= width:
          run_chars = run_chars[:-1]
          if not run_chars:
            continue
        ansi_color(user, fg=ch.fg, fg_br=ch.fg_br, bg=ch.bg, bg_br=ch.bg_br)
        await ansi_move_deferred(user, row=r_idx + 1, col=run_start + 1, drain=False)
        await send(user, "".join(run_chars), drain=False)

  # Restore wrap, color, mouse, cursor
  ansi_wrap(user, snap['cur_wrap'])
  ansi_color(user, fg=snap['cur_fg'], fg_br=snap['cur_fg_br'],
             bg=snap['cur_bg'], bg_br=snap['cur_bg_br'])

  if snap['mouse_reporting'] and not user.mouse_reporting:
    user.writer.write("\x1b[?1000h\x1b[?1002h")
    user.mouse_reporting = True
  elif not snap['mouse_reporting'] and user.mouse_reporting:
    user.writer.write("\x1b[?1000l\x1b[?1002l")
    user.mouse_reporting = False

  await ansi_move(user, snap['cur_row'] or 1, snap['cur_col'] or 1, drain=True)

  # Restore the stars active list so the background animation keeps tracking
  # the stars that were visible before the overlay.
  if hasattr(user, '_stars_active') and user._stars_active is not None:
    user._stars_active[:] = snap.get('stars_active', [])


class _PopupInterrupt(Exception):
  """Raised when a popup arrives and needs to interrupt the current read."""
  pass

async def _read_or_popup(user, timeout=None):
  """Read one char from user, but wake up immediately if a popup is queued.
  Returns the char, or raises _PopupInterrupt if a popup arrived."""
  read_task = asyncio.ensure_future(user.reader.read(1))
  notify_task = asyncio.ensure_future(user.popup_notify.wait())
  try:
    if timeout is not None:
      done, pending = await asyncio.wait(
        [read_task, notify_task], timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
    else:
      done, pending = await asyncio.wait(
        [read_task, notify_task], return_when=asyncio.FIRST_COMPLETED)
    for t in pending:
      t.cancel()
      try:
        await t
      except (asyncio.CancelledError, Exception):
        pass
    if notify_task in done:
      user.popup_notify.clear()
      # Cancel the read if it didn't complete
      if read_task not in done:
        raise _PopupInterrupt()
      # Both completed — return the char, popup will be handled next loop
      return read_task.result()
    if read_task in done:
      return read_task.result()
    # Timeout — neither completed
    raise asyncio.TimeoutError()
  except asyncio.CancelledError:
    read_task.cancel()
    notify_task.cancel()
    raise

async def _get_input_key(user):
  while True:
    if user.cur_input_code:
      try:
        char = await _read_or_popup(user, timeout=0.05)
      except _PopupInterrupt:
        raise
      except asyncio.TimeoutError:
        code = user.cur_input_code
        user.cur_input_code = ""
        if code == "\x1b":
          return "esc"
        if code == "\x1b[M":
          # Timed out waiting for mouse bytes — it's actually ctrl_pgup
          return ctrl_pgup
        continue  # incomplete sequence, try again
    else:
      char = await _read_or_popup(user)
    if not char:
      raise Disconnected()
    if char in "\x00\x1b":
      user.cur_input_code = char
      continue
    if ord(char) < 32:
      user.cur_input_code = ""
    combined = user.cur_input_code + char
    r = check(combined)
    if r:
      user.cur_input_code = ""
      return r
    if check_partial(combined):
      user.cur_input_code = combined
    else:
      user.cur_input_code = ""
      if len(combined)==1:
        return combined

# Popup display mode:
#   True  — popups stack on top of each other and on top of chat invitations
#           (newer ones interrupt older ones, dismissed in reverse order)
#   False — popups queue and only one shows at a time; chat invitations wait
#           for the current popup to be dismissed
# Set to False to revert to the original queue-only behavior.
POPUP_STACK = True

async def _drain_popup_queue(user):
  """Show any queued popups and handle chat invitations.
  Called from the user's own input loop to avoid reader conflicts."""
  if user.in_door:
    return

  # Handle chat invitation if pending. In queue mode, suppress while another
  # popup is showing; in stack mode, always show (it stacks on top).
  inv = getattr(user, '_chat_invitation', None)
  if inv and (POPUP_STACK or not user._in_popup):
    from oneonone import _handle_invitation, run_invitee_overlay
    # Snapshot the underlying activity's screen and cursor BEFORE the
    # invitation prompt overwrites the bottom row, so a later pop_screen
    # restores the cursor to where the activity actually had it.
    await push_screen(user)
    try:
      accepted = await _handle_invitation(user)
      if accepted:
        # Run the invitee's chat session inline as an overlay.
        await run_invitee_overlay(user)
    finally:
      await pop_screen(user)
    return

  if not user.popup_queue:
    return
  if not POPUP_STACK and user._in_popup:
    return

  if not POPUP_STACK:
    user._in_popup = True
  try:
    from input_fields import show_message_box
    while user.popup_queue:
      kwargs = user.popup_queue.pop(0)
      # In stack mode, queued popups become stacked popups, so the
      # "Abort All (n)" hint is meaningless — suppress it.
      qc = 0 if POPUP_STACK else len(user.popup_queue)
      r = await show_message_box(user, queued_count=qc, **kwargs)
      if r == "abort":
        user.popup_queue.clear()
        break
  finally:
    if not POPUP_STACK:
      user._in_popup = False

async def get_input_key(user, window_size=0.02, char_threshold=2, batch_pause=0.03):
  while True:
    # Check for queued popups before waiting for input
    await _drain_popup_queue(user)

    try:
      if user.batch_mode:
        # Already in batch mode - use timeout
        try:
          key = await asyncio.wait_for(_get_input_key(user), timeout=batch_pause)
          user.input_timestamps.append(time.perf_counter())
          return key
        except asyncio.TimeoutError:
          user.batch_mode = False
          # Timeout - exit batch mode and wait normally for next key
          continue
      else:
        # Normal mode - check if we should enter batch mode
        key = await _get_input_key(user)
    except _PopupInterrupt:
      # Read was interrupted by a popup — drain and retry
      user.cur_input_code = ""  # reset any partial escape sequence
      continue
    now = time.perf_counter()
    user.input_timestamps.append(now)
    if len(user.input_timestamps) == char_threshold:
      oldest = user.input_timestamps[0]
      if now - oldest < window_size:
        user.batch_mode = True
    return key
