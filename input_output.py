# todo: change fg, bg, fg_br, bg_br to fg, fg_br, bg, bg_br

import time

from definitions import *
from keyboard_codes import *

def emu_scroll(user): # todo: add scroll region paramaters?
  del user.screen[0]
  user.screen.append([Char() for _ in range(user.screen_width)])

def emu_clear(user):
  for x in range(len(user.screen)):
    user.screen[x] = [Char() for col in range(user.screen_width)]
  user.cur_col = user.cur_row = 1

async def send(user, message, word_wrap=False, drain=False):
  if message or drain:
    await ansi_move_2(user)
    await ansi_color_2(user)
  if message:
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
  user.writer.write(f"\x1b[{row};{col}H")
  user.cur_row = user.new_row = row
  user.cur_col = user.new_col = col
  user._wrap_ambiguous = False
  if drain:
    await user.writer.drain()

async def ansi_hide_cursor(user, drain=False):
  if getattr(user, 'cur_show_cursor', True):
    user.cur_show_cursor = False
    user.writer.write("\x1b[?25l")
    if drain:
      await user.writer.drain()

async def ansi_show_cursor(user, drain=False):
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
  _ansi_color_write(user)
  if drain:
    await user.writer.drain()

async def ansi_cls(user, fg=None, bg=None, fg_br=None, bg_br=None):
  ansi_color(user, fg=fg, fg_br=fg_br, bg=bg, bg_br=bg_br, drain=True)
  user.writer.write("\x1b[2J\x1b[H")
  emu_clear(user)
  user.cur_row = user.new_row = 1
  user.cur_col = user.new_col = 1
  user._wrap_ambiguous = False
  await user.writer.drain()

async def ansi_del_to_end(user, drain=False):
  user.writer.write("\x1b[J")
  user.screen[user.cur_row] = user.screen[user.cur_row][:user.cur_col]
  if drain:
    await user.writer.drain()

async def ansi_set_region(user, top_row=None, bottom_row=None, drain=False):
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
  if value != user.scroll_region_strict:
    user.scroll_region_strict = value
    if value:
      user.writer.write(f"\x1b[?6h")
    else:
      user.writer.write(f"\x1b[?7h")
    if drain:
      await user.writer.drain()

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

class ChatRedirect(Exception):
  """Raised when a user accepts a chat invitation and needs to be redirected."""
  pass

async def _drain_popup_queue(user):
  """Show any queued popups and handle chat invitations.
  Called from the user's own input loop to avoid reader conflicts."""
  # Check for chat redirect (user accepted invitation, needs to go to oneonone)
  if getattr(user, '_chat_redirect', None):
    user._chat_redirect = None
    raise ChatRedirect()

  # Handle chat invitation if pending
  inv = getattr(user, '_chat_invitation', None)
  if inv and not user._in_popup:
    from oneonone import _handle_invitation
    accepted = await _handle_invitation(user)
    if accepted:
      # The invitation handler said yes — now redirect
      raise ChatRedirect()

  if not user.popup_queue or user._in_popup or user.in_door:
    return
  user._in_popup = True
  try:
    from input_fields import show_message_box
    while user.popup_queue:
      kwargs = user.popup_queue.pop(0)
      r = await show_message_box(user, queued_count=len(user.popup_queue), **kwargs)
      if r == "abort":
        user.popup_queue.clear()
        break
  finally:
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
