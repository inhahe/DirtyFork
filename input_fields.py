from copy import deepcopy
import asyncio
import re

from input_output import *
from config import get_config
from definitions import *

config = get_config()

contentre = re.compile(r"[^\n ]+| |\n")


# Block-based quote/margin system
#
# API:
#   Block(text="...", level=0) — a block of text at a quote nesting level.
#   InputField.create(content=[Block("original", level=0), Block("quoted", level=1), ...])
#   content="plain string" still works (backward compatible, single Block at level 0).
#   field.get_blocks() returns the content back as a list of Block objects.
#
# Internals:
#   Content is stored as a list of Line objects (text + level).
#   _compute_display_rows() maps logical lines to display rows (word wrap, margins).
#   Cursor position is (cursor_line, cursor_col) in logical coordinates.
#
# Key behaviors:
#   Enter on empty quoted line -> exits one nesting level (level decreases by 1).
#   Enter on non-empty quoted line -> new line at same level.
#   Backspace at start of quoted line (right after margin prefix) -> reduces that line's level by 1.
#   Home key -> goes to first editable position (col 0 in logical coords).
#   Up/Down arrows -> respect margin widths when landing on quoted lines.
#   Click -> can't land in margin prefix area.
#   Word wrap -> continuation lines inherit the same margin prefix.
#   Typing -> characters inherit the current line's quote level.

class Block:
  """A block of text at a given quote/margin nesting level."""
  def __init__(self, text="", level=0):
    self.text = text    # the text content of this block
    self.level = level  # nesting level (0 = user's text, 1 = "> ", 2 = ">> ", etc.)


# ---------------------------------------------------------------------------
# Word/Space token model used by Line and the word-wrap engine.
# A line's text is conceptually a sequence of Word and Space tokens. Editing
# code still mutates line.text (the canonical source of truth); tokens are
# computed from text on demand and cached on text identity.
# ---------------------------------------------------------------------------

class Word:
  __slots__ = ('text',)
  def __init__(self, text):
    self.text = text  # never empty, never contains spaces

  def __len__(self):
    return len(self.text)

  def __repr__(self):
    return f"Word({self.text!r})"


class Space:
  __slots__ = ('count',)
  def __init__(self, count):
    self.count = count  # number of consecutive space chars (>=1)

  def __len__(self):
    return self.count

  def __repr__(self):
    return f"Space({self.count})"


class Cell:
  """One screen cell in the wrap-mode grid. Maps a (grid_row, grid_col)
  position to the source token + offset that produced it. Margin and fill
  cells have token=None."""
  __slots__ = ('char', 'token', 'token_offset', 'line_index', 'col_in_line')
  def __init__(self, char=' ', token=None, token_offset=0, line_index=-1, col_in_line=-1):
    self.char = char
    self.token = token
    self.token_offset = token_offset
    self.line_index = line_index
    self.col_in_line = col_in_line


def _tokenize(text):
  """Split a plain text string into a list of Word and Space tokens.
  Preserves all characters and order; ''.join(tok-text for tok in result) == text."""
  tokens = []
  i = 0
  n = len(text)
  while i < n:
    if text[i] == ' ':
      j = i + 1
      while j < n and text[j] == ' ':
        j += 1
      tokens.append(Space(j - i))
      i = j
    else:
      j = i + 1
      while j < n and text[j] != ' ':
        j += 1
      tokens.append(Word(text[i:j]))
      i = j
  return tokens


def _word_wrap_lines(text, width):
  """Simple word wrap for display-only text. Returns a list of lines.
  Shared logic with InputField's word wrap but without the token/index machinery."""
  lines = []
  for paragraph in text.split("\n"):
    if not paragraph:
      lines.append("")
      continue
    words = paragraph.split(" ")
    current_line = ""
    for word in words:
      if not current_line:
        # First word on line — may need to break long words
        while len(word) > width:
          lines.append(word[:width])
          word = word[width:]
        current_line = word
      elif len(current_line) + 1 + len(word) <= width:
        current_line += " " + word
      else:
        lines.append(current_line)
        current_line = ""
        while len(word) > width:
          lines.append(word[:width])
          word = word[width:]
        current_line = word
    lines.append(current_line)
  return lines


async def show_message_box(user, text, row=null, col=null, width=null, max_width=null, height=null,
                           fg=white, fg_br=False, bg=black, bg_br=False,
                           outline_fg=green, outline_fg_br=False, outline_bg=black, outline_bg_br=False,
                           outline_double=False, title=null, word_wrap=True, queued_count=0,
                           return_key=False):
  """Show a modal, scrollable message box that restores the screen behind it when dismissed.
  Up/Down/PgUp/PgDn to scroll, any other key to dismiss.
  Uses user.screen to restore the background afterward.
  width: exact inner width. If null, auto-sizes to fit content.
  max_width: maximum inner width when auto-sizing (triggers word wrap). Defaults to screen_width - 4.
  queued_count: if > 0, shows 'A: Abort All (n)' and returns 'abort' if pressed.
  Returns 'abort' or None."""

  # Determine max_width
  if max_width is null:
    if word_wrap:
      max_width = min(60, user.screen_width - 4)
    else:
      max_width = user.screen_width - 4  # no wrapping — allow full width

  def _split_lines(text, w):
    """Split text into lines. Word-wraps if word_wrap is True, otherwise just splits on newlines."""
    if word_wrap:
      return _word_wrap_lines(text, w)
    else:
      # No word wrap — just split on newlines, truncation handled at display time
      return text.split("\n")

  if width is null:
    # Auto-size: first split at max_width, then shrink to the longest line
    wrapped = _split_lines(text, max_width)
    if title and title is not null:
      title_len = len(str(title)) + 7  # " title " + close button [■]
    else:
      title_len = 0
    longest = max((len(line) for line in wrapped), default=0)
    min_prompt_width = 16  # enough for " Press any key " + 1 spare before br_c
    inner_width = max(longest, title_len, min_prompt_width)
    inner_width = min(inner_width, max_width)
    # Re-wrap at the final width in case shrinking changed things
    if word_wrap and inner_width < max_width:
      wrapped = _split_lines(text, inner_width)
      longest = max((len(line) for line in wrapped), default=0)
      inner_width = max(longest, title_len, min_prompt_width)
      inner_width = min(inner_width, max_width)
  else:
    inner_width = width
    wrapped = _split_lines(text, inner_width)

  if row is null:
    row = 2  # near top of screen, 1-based
  if col is null:
    col = max(1, (user.screen_width - inner_width - 2) // 2 + 1)  # centered

  if height is null:
    height = min(max(len(wrapped), 1), user.screen_height - row - 2)
  height = max(1, height)

  scrollable = len(wrapped) > height
  total_lines = len(wrapped)
  max_offset = max(0, total_lines - height) if scrollable else 0
  scroll_offset = 0
  h_scroll = 0
  max_line_width = max((len(line) for line in wrapped), default=0)
  h_scrollable = (not word_wrap) and max_line_width > inner_width
  max_h_offset = max(0, max_line_width - inner_width) if h_scrollable else 0
  # Horizontal scroll step from user config (default 8)
  user_conf = getattr(user, 'conf', null)
  h_step = 8
  if user_conf and user_conf is not null and user_conf.scroll_step:
    try:
      h_step = int(user_conf.scroll_step)
    except (ValueError, TypeError):
      pass

  # Box-drawing characters
  if outline_double:
    tl, horiz, tr, vert, bl, br_c = (bytes([c]).decode('cp437') for c in (201, 205, 187, 186, 200, 188))
  else:
    tl, horiz, tr, vert, bl, br_c = (bytes([c]).decode('cp437') for c in (218, 196, 191, 179, 192, 217))

  # Scrollbar characters (CP437)
  arrow_up = bytes([30]).decode('cp437')    # ▲
  arrow_down = bytes([31]).decode('cp437')  # ▼
  scroll_thumb = bytes([219]).decode('cp437')  # █
  scroll_track = bytes([176]).decode('cp437')  # ░
  close_char = bytes([254]).decode('cp437')    # ■

  # Click target positions (set during _draw_box)
  close_btn_col = 0   # screen col of the close button
  abort_col_start = 0 # screen col range of "Abort All" text
  abort_col_end = 0
  abort_row = 0

  # Save cursor position before the popup
  saved_cur_row = user.cur_row
  saved_cur_col = user.cur_col
  saved_new_row = user.new_row
  saved_new_col = user.new_col

  # Save the screen area (1-based coords, outline adds 1 on each side)
  save_top = row - 1
  save_left = col - 1
  save_bottom = row + height
  save_right = col + inner_width
  saved = []
  for r in range(save_top, save_bottom + 1):
    row_data = []
    for c in range(save_left, save_right + 1):
      if 1 <= r <= user.screen_height and 1 <= c <= user.screen_width:
        if user.screen and r-1 < len(user.screen) and c-1 < len(user.screen[r-1]):
          ch = user.screen[r-1][c-1]
          row_data.append(Char(ch.char, ch.fg, ch.fg_br, ch.bg, ch.bg_br))
        else:
          row_data.append(Char())
      else:
        row_data.append(Char())
    saved.append(row_data)

  need_nowrap = (save_right >= user.screen_width)

  # Build the horizontal prompt text (shown on top border when h_scrollable)
  if h_scrollable:
    _h_parts = []
    if scrollable:
      _h_parts.append("Up/Down")
    _h_parts.append("Left/Right")
    _h_parts.append("any key to close")
    _h_prompt = ", ".join(_h_parts)
  else:
    _h_prompt = ""

  async def _draw_box():
    nonlocal _h_prompt
    if need_nowrap:
      ansi_wrap(user, False)

    ansi_color(user, fg=outline_fg, fg_br=outline_fg_br, bg=outline_bg, bg_br=outline_bg_br)

    # Top border with close button [■] in top-right, and prompt if h_scrollable
    close_str = "[" + close_char + "]"
    close_btn_col = save_left + inner_width - 2  # 1-based screen col of '['
    await ansi_move_deferred(user, row=save_top, col=save_left, drain=False)
    title_str = str(title)[:inner_width - 5] if title and title is not null else ""

    if h_scrollable and _h_prompt:
      # tl + ─ + space + title + space + ─*fill + space + prompt + space + [■] + tr
      used = len(title_str) + len(_h_prompt) + 7 + len(close_str)
      fill_len = inner_width + 2 - used
      if fill_len < 0:
        # Not enough room — truncate prompt
        _h_prompt = _h_prompt[:len(_h_prompt) + fill_len]
        fill_len = 0
      if title_str:
        top_line = tl + horiz + " " + title_str + " " + horiz * max(0, fill_len) + " " + _h_prompt + " " + close_str + tr
      else:
        top_line = tl + horiz * max(0, fill_len + len(title_str) + 3) + " " + _h_prompt + " " + close_str + tr
    elif title_str:
      fill_len = inner_width - len(title_str) - 3 - len(close_str)
      top_line = tl + horiz + " " + title_str + " " + horiz * max(0, fill_len) + close_str + tr
    else:
      fill_len = inner_width - len(close_str)
      top_line = tl + horiz * max(0, fill_len) + close_str + tr
    await send(user, top_line, drain=False)

    # Compute scrollbar thumb position and size
    # The track is the area between the arrows: rows 1..height-2 (0-based), so track_height = height - 2
    # Thumb is proportionally sized so it never skips a row when scrolling by 1
    if scrollable:
      max_offset = total_lines - height
      track_height = height - 2  # excluding the arrow rows at top and bottom
      # Thumb height: proportional to viewport/total, minimum 1
      # Ensure (track_height - thumb_height) >= max_offset so thumb never skips
      thumb_height = max(1, track_height - max_offset)
      # If max_offset > track_height - 1, thumb is 1 and some skipping is unavoidable
      thumb_height = max(1, min(thumb_height, track_height))
      available_positions = track_height - thumb_height
      if available_positions > 0 and max_offset > 0:
        thumb_start = round(scroll_offset / max_offset * available_positions)
      else:
        thumb_start = 0
      # thumb occupies track rows thumb_start .. thumb_start + thumb_height - 1
    else:
      thumb_start = -1
      thumb_height = 0

    # Side borders + content
    for i in range(height):
      line_idx = scroll_offset + i
      await ansi_move_deferred(user, row=row + i, col=save_left, drain=False)

      # Left border
      ansi_color(user, fg=outline_fg, fg_br=outline_fg_br, bg=outline_bg, bg_br=outline_bg_br)
      await send(user, vert, drain=False)

      # Content — apply horizontal scroll for non-word-wrap mode
      ansi_color(user, fg=fg, fg_br=fg_br, bg=bg, bg_br=bg_br)
      if line_idx < total_lines:
        full_line = wrapped[line_idx]
        visible = full_line[h_scroll:h_scroll + inner_width]
        await send(user, visible + " " * (inner_width - len(visible)), drain=False)
      else:
        await send(user, " " * inner_width, drain=False)

      # Right border — with scrollbar only if scrollable
      ansi_color(user, fg=outline_fg, fg_br=outline_fg_br, bg=outline_bg, bg_br=outline_bg_br)
      if scrollable:
        if i == 0:
          await send(user, arrow_up if scroll_offset > 0 else vert, drain=False)
        elif i == height - 1:
          await send(user, arrow_down if scroll_offset < max_offset else vert, drain=False)
        else:
          track_row = i - 1  # 0-based position within the track
          if thumb_start <= track_row < thumb_start + thumb_height:
            await send(user, scroll_thumb, drain=False)
          else:
            await send(user, scroll_track, drain=False)
      else:
        await send(user, vert, drain=False)

    # Bottom border — with horizontal scrollbar if h_scrollable
    await ansi_move_deferred(user, row=save_bottom, col=save_left, drain=False)
    ansi_color(user, fg=outline_fg, fg_br=outline_fg_br, bg=outline_bg, bg_br=outline_bg_br)
    if h_scrollable:
      max_h_offset = max_line_width - inner_width
      h_track_width = inner_width - 2  # excluding arrow chars at left and right
      # Thumb proportional to visible/total width, minimum 1
      h_thumb_width = max(1, round(inner_width / max_line_width * h_track_width))
      h_thumb_width = min(h_thumb_width, h_track_width)
      h_avail = h_track_width - h_thumb_width
      h_thumb_start = round(h_scroll / max_h_offset * h_avail) if max_h_offset > 0 and h_avail > 0 else 0

      arrow_left = bytes([17]).decode('cp437')   # ◄
      arrow_right = bytes([16]).decode('cp437')  # ►

      await send(user, bl, drain=False)
      await send(user, arrow_left if h_scroll > 0 else horiz, drain=False)
      for ti in range(h_track_width):
        if h_thumb_start <= ti < h_thumb_start + h_thumb_width:
          await send(user, scroll_thumb, drain=False)
        else:
          await send(user, scroll_track, drain=False)
      await send(user, arrow_right if h_scroll < max_h_offset else horiz, drain=False)
      await send(user, br_c, drain=False)
    else:
      await send(user, bl + horiz * inner_width + br_c, drain=False)

    # Prompt
    ansi_color(user, fg=outline_fg, fg_br=True, bg=outline_bg, bg_br=outline_bg_br)
    if scrollable or h_scrollable:
      parts = []
      if scrollable:
        parts.append("Up/Down")
      if h_scrollable:
        parts.append("Left/Right")
      parts.append("any other key to close")
      prompt_text = " " + ", ".join(parts) + " "
    else:
      prompt_text = " Press any key "
    abort_text = ""
    abort_prefix = ""
    abort_suffix = ""
    if queued_count > 0:
      abort_text = f"Abort All ({queued_count})"
      abort_prefix = prompt_text.rstrip() + "  "
      abort_suffix = "bort All ({}) ".format(queued_count)
      prompt_text = abort_prefix + abort_text + " "
    prompt_row = save_bottom
    if h_scrollable:
      # Prompt is embedded in top border by _draw_box — no separate draw
      prompt_row = save_top
    else:
      await ansi_move_deferred(user, row=prompt_row, col=save_left + 2, drain=False)
      prompt_col = save_left + 2
      if abort_text:
        await send(user, abort_prefix, drain=False)
        ansi_color(user, fg=fg, fg_br=fg_br, bg=outline_bg, bg_br=outline_bg_br)
        await send(user, "A", drain=False)
        ansi_color(user, fg=outline_fg, fg_br=True, bg=outline_bg, bg_br=outline_bg_br)
        await send(user, abort_suffix, drain=False)
      else:
        await send(user, prompt_text, drain=False)
    # Track abort click region
    if abort_text:
      abort_offset = prompt_text.rfind(abort_text)
      abort_col_start = prompt_col + abort_offset
      abort_col_end = abort_col_start + len(abort_text) - 1
      abort_row = prompt_row

    # Position cursor: inside the box top-left if scrollable, otherwise hidden
    if scrollable:
      await ansi_move_deferred(user, row=row, col=col, drain=False)

    if need_nowrap:
      ansi_wrap(user, True)

    await user.writer.drain()

  # Enable mouse reporting for clickable elements, hide cursor
  saved_mouse = user.mouse_reporting
  if not saved_mouse:
    user.writer.write("\x1b[?1000h\x1b[?1002h")
    user.mouse_reporting = True
  await ansi_hide_cursor(user, drain=True)

  # Initial draw
  await _draw_box()

  # Input loop — scroll on up/down/left/right/pgup/pgdn, dismiss on anything else
  while True:
    key = await get_input_key(user)
    handled = False
    if key == up:
      if scrollable and scroll_offset > 0:
        scroll_offset -= 1
        await _draw_box()
        handled = True
    elif key == down:
      if scrollable and scroll_offset < total_lines - height:
        scroll_offset += 1
        await _draw_box()
        handled = True
    elif key == left:
      if h_scrollable and h_scroll > 0:
        h_scroll = max(0, h_scroll - h_step)
        await _draw_box()
        handled = True
    elif key == right:
      if h_scrollable:
        max_h_off = max_line_width - inner_width
        if h_scroll < max_h_off:
          h_scroll = min(max_h_off, h_scroll + h_step)  # snaps to end on last step
          await _draw_box()
          handled = True
    elif key == pgup:
      if scrollable:
        scroll_offset = max(0, scroll_offset - height)
        await _draw_box()
        handled = True
    elif key == pgdn:
      if scrollable:
        scroll_offset = min(total_lines - height, scroll_offset + height)
        await _draw_box()
        handled = True
    elif key == home:
      if h_scrollable or scrollable:
        if h_scrollable:
          h_scroll = 0
        if scrollable:
          scroll_offset = 0
        await _draw_box()
        handled = True
    elif key == end:
      if h_scrollable or scrollable:
        if h_scrollable:
          h_scroll = max(0, max_line_width - inner_width)
        if scrollable:
          scroll_offset = max(0, total_lines - height)
        await _draw_box()
        handled = True
    # Mouse click / drag
    if not handled and key == click:
      btn = getattr(key, 'button', None)
      is_motion = getattr(key, 'motion', False)
      if btn == left:
        cr_click, cc_click = key.row, key.col
        # Close button [■] on top border
        if not is_motion and cr_click == save_top and close_btn_col <= cc_click <= close_btn_col + 2:
          result = None
          break
        # Abort All text on prompt row
        if not is_motion and queued_count > 0 and abort_text and cr_click == abort_row and abort_col_start <= cc_click <= abort_col_end:
          result = "abort"
          break
        # Vertical scrollbar — click or drag
        if scrollable and cc_click == save_right:
          scroll_top_row = save_top + 1  # first content row (arrow up)
          scroll_bot_row = save_top + height  # last content row (arrow down)
          if not is_motion and cr_click == scroll_top_row and scroll_offset > 0:
            # Click on up arrow
            scroll_offset = max(0, scroll_offset - 1)
            await _draw_box()
          elif not is_motion and cr_click == scroll_bot_row and scroll_offset < max_offset:
            # Click on down arrow
            scroll_offset = min(max_offset, scroll_offset + 1)
            await _draw_box()
          elif cr_click > scroll_top_row and cr_click < scroll_bot_row:
            # Click or drag on track — map position to scroll offset
            track_click = cr_click - scroll_top_row - 1  # 0-based track position
            track_height_val = height - 2
            if track_height_val > 0 and max_offset > 0:
              scroll_offset = round(track_click / max(1, track_height_val - 1) * max_offset)
              scroll_offset = max(0, min(scroll_offset, max_offset))
              await _draw_box()
        # Horizontal scrollbar — click or drag
        if h_scrollable and cr_click == save_bottom:
          h_arrow_left_col = save_left + 1
          h_arrow_right_col = save_left + 2 + (inner_width - 2)
          h_track_left = h_arrow_left_col + 1
          h_track_right = h_arrow_right_col - 1
          if not is_motion and cc_click == h_arrow_left_col and h_scroll > 0:
            h_scroll = max(0, h_scroll - h_step)
            await _draw_box()
          elif not is_motion and cc_click == h_arrow_right_col and h_scroll < max_h_offset:
            h_scroll = min(max_h_offset, h_scroll + h_step)
            await _draw_box()
          elif h_track_left <= cc_click <= h_track_right:
            track_click = cc_click - h_track_left
            h_track_width_val = inner_width - 2
            if h_track_width_val > 0 and max_h_offset > 0:
              raw = round(track_click / max(1, h_track_width_val - 1) * max_h_offset)
              h_scroll = round(raw / h_step) * h_step  # snap to scroll step
              h_scroll = max(0, min(h_scroll, max_h_offset))
              await _draw_box()
      handled = True  # consume all mouse events

    if not handled:
      # Up/Down/Left/Right that didn't scroll are consumed (don't dismiss)
      if key in (up, down, left, right, pgup, pgdn, home, end):
        continue
      # Abort All
      if queued_count > 0 and isinstance(key, str) and key.lower() == "a":
        result = "abort"
      elif return_key:
        result = key
      else:
        result = None
      break

  # Restore mouse reporting state, show cursor again
  if not saved_mouse:
    user.writer.write("\x1b[?1002l\x1b[?1000l")
    user.mouse_reporting = False
  await ansi_show_cursor(user)

  # Restore the screen area from saved data
  if need_nowrap:
    ansi_wrap(user, False)
  for ri, r in enumerate(range(save_top, save_bottom + 1)):
    for ci, c in enumerate(range(save_left, save_right + 1)):
      if 1 <= r <= user.screen_height and 1 <= c <= user.screen_width:
        ch = saved[ri][ci]
        await ansi_move_deferred(user, row=r, col=c, drain=False)
        ansi_color(user, fg=ch.fg, fg_br=ch.fg_br, bg=ch.bg, bg_br=ch.bg_br)
        await send(user, ch.char, drain=False)

  # Restore cursor to where it was before the popup
  user.new_row = saved_cur_row
  user.new_col = saved_cur_col
  await ansi_move_2(user)
  await user.writer.drain()
  if need_nowrap:
    ansi_wrap(user, True)

  return result


class SelectField:
  """Inline cycling selector. Shows the current option with arrow indicators.
  Left/Right cycle through options. Tab/Enter return to container."""

  @classmethod
  async def create(cls, parent, user, options, value="", conf=null,
                   fg=null, fg_br=null, bg=null, bg_br=null,
                   fill=null, fill_fg=null, fill_bg=null,
                   fill_fg_br=null, fill_bg_br=null,
                   arrow_fg=null, arrow_fg_br=null):
    self = cls()
    self.user = user
    self.parent = parent
    self.options = list(options)
    self.outline = False
    self.allow_edit = True
    self.no_cursor_margin = True
    self.insert_mode = False

    self.row_offset = user.cur_row
    self.col_offset = user.cur_col

    # Find initial selection
    self._index = 0
    val_lower = str(value).lower()
    for i, opt in enumerate(self.options):
      if str(opt).lower() == val_lower:
        self._index = i
        break

    if conf is null:
      conf = config.input_fields.input_field

    def _color(val, default=white):
      if val and val in colors:
        return colors[val]
      if isinstance(val, int):
        return val
      return default

    self.fg = _color(conf.content.fg, white) if fg is null else fg
    self.fg_br = (conf.content.fg_br or False) if fg_br is null else fg_br
    _fill_present = bool(conf.blank.char if fill is null else fill)
    _fill_bg = _color(conf.blank.bg, black) if fill_bg is null else fill_bg
    if bg is not null:
      self.bg = bg
    elif _fill_present:
      self.bg = _fill_bg
    else:
      self.bg = _color(conf.content.bg, black)
    self.bg_br = (conf.content.bg_br or False) if bg_br is null else bg_br

    self.fill = conf.blank.char if fill is null else fill
    self.fill = self.fill or " "
    if type(self.fill) is int:
      self.fill = bytes([self.fill]).decode('cp437')
    self.fill_fg = _color(conf.blank.fg, white) if fill_fg is null else fill_fg
    self.fill_fg_br = (conf.blank.fg_br or False) if fill_fg_br is null else fill_fg_br
    self.fill_bg = _color(conf.blank.bg, black) if fill_bg is null else fill_bg
    self.fill_bg_br = (conf.blank.bg_br or False) if fill_bg_br is null else fill_bg_br

    self.arrow_fg = arrow_fg if arrow_fg is not null else self.fg
    self.arrow_fg_br = arrow_fg_br if arrow_fg_br is not null else True

    # Width: enough for longest option + arrows + padding
    max_opt_len = max((len(str(o)) for o in self.options), default=1)
    self.width = max_opt_len + 4  # "< " + option + " >"
    self.height = 1

    # Compat with InputFields container
    self.row = 0
    self.col = 0
    self.cursor_line = 0
    self.cursor_col = 0

    return self

  def get_text(self):
    return str(self.options[self._index])

  content = property(lambda self: self.get_text())

  def _contains_screen_pos(self, screen_row, screen_col):
    return (screen_row == self.row_offset and
            self.col_offset <= screen_col < self.col_offset + self.width)

  def _place_cursor_at_screen_pos(self, screen_row, screen_col):
    pass  # no internal cursor positioning

  async def draw_outline(self, active=False):
    pass  # no outline

  async def draw_field(self, start_at=None, end_row=null):
    opt = str(self.options[self._index])
    max_opt_len = self.width - 4
    display = opt.ljust(max_opt_len)

    await ansi_move(self.user, self.row_offset, self.col_offset)

    # Left arrow
    ansi_color(self.user, fg=self.arrow_fg, fg_br=self.arrow_fg_br, bg=self.bg, bg_br=self.bg_br)
    lt = bytes([17]).decode('cp437')  # CP437 left-pointing triangle
    await send(self.user, lt + " ", drain=False)

    # Option text
    ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
    await send(self.user, display, drain=False)

    # Right arrow
    ansi_color(self.user, fg=self.arrow_fg, fg_br=self.arrow_fg_br, bg=self.bg, bg_br=self.bg_br)
    rt = bytes([16]).decode('cp437')  # CP437 right-pointing triangle
    await send(self.user, " " + rt, drain=True)

  async def run(self):
    while True:
      key = await get_input_key(self.user)

      if key == cr:
        return RetVals(key=cr, content=self.get_text(), row=self.row, col=self.col,
                       insert_mode=False)
      if key == tab:
        return RetVals(key=tab, content=self.get_text(), row=self.row, col=self.col,
                       insert_mode=False)
      if key == shift_tab:
        return RetVals(key=shift_tab, content=self.get_text(), row=self.row, col=self.col,
                       insert_mode=False)

      if key == left:
        self._index = (self._index - 1) % len(self.options)
        await self.draw_field()
        continue
      if key == right or key == " ":
        self._index = (self._index + 1) % len(self.options)
        await self.draw_field()
        continue

      if key == up:
        if self.parent:
          return RetVals(key=up, content=self.get_text(), row=self.row, col=self.col,
                         insert_mode=False)
      if key == down:
        if self.parent:
          return RetVals(key=down, content=self.get_text(), row=self.row, col=self.col,
                         insert_mode=False)

      if key == click:
        btn = getattr(key, 'button', None)
        if btn == left:
          click_row, click_col = key.row, key.col
          if self._contains_screen_pos(click_row, click_col):
            # Click on left half = prev, right half = next
            mid = self.col_offset + self.width // 2
            if click_col < mid:
              self._index = (self._index - 1) % len(self.options)
            else:
              self._index = (self._index + 1) % len(self.options)
            await self.draw_field()
          elif self.parent:
            return RetVals(key=click, button=btn, click_row=click_row, click_col=click_col,
                           content=self.get_text(), row=self.row, col=self.col,
                           insert_mode=False)


class ListField:
  """Vertical list editor. Shows items one per line with a highlighted cursor.
  Enter adds a new item (inline input), Delete/Backspace removes the highlighted item.
  Up/Down navigate within the list. Tab returns to container."""

  @classmethod
  async def create(cls, parent, user, items=None, height=5, width=30,
                   validate=None, conf=null,
                   fg=null, fg_br=null, bg=null, bg_br=null,
                   sel_fg=null, sel_fg_br=null, sel_bg=null, sel_bg_br=null,
                   outline=True, outline_fg=null, outline_fg_br=null,
                   outline_bg=null, outline_bg_br=null,
                   outline_active_fg=null, outline_active_fg_br=null,
                   outline_active_bg=null, outline_active_bg_br=null,
                   outline_double=null, title=null):
    self = cls()
    self.user = user
    self.parent = parent
    self.items = list(items) if items else []
    self.validate = validate  # async fn(item_text) -> (bool, error_msg)
    self.allow_edit = True
    self.no_cursor_margin = True
    self.insert_mode = False
    self._cursor = 0
    self._scroll = 0
    self._adding = False
    self.title = title

    self.row_offset = user.cur_row
    self.col_offset = user.cur_col

    if conf is null:
      conf = config.input_fields.input_field

    def _color(val, default=white):
      if val and val in colors:
        return colors[val]
      if isinstance(val, int):
        return val
      return default

    self.fg = _color(conf.content.fg, white) if fg is null else fg
    self.fg_br = (conf.content.fg_br or False) if fg_br is null else fg_br
    _fill_present = bool(conf.blank.char)
    _fill_bg = _color(conf.blank.bg, black)
    if bg is not null:
      self.bg = bg
    elif _fill_present:
      self.bg = _fill_bg
    else:
      self.bg = _color(conf.content.bg, black)
    self.bg_br = (conf.content.bg_br or False) if bg_br is null else bg_br

    # Selected/highlighted item colors
    self.sel_fg = sel_fg if sel_fg is not null else self.bg
    self.sel_fg_br = sel_fg_br if sel_fg_br is not null else self.bg_br
    self.sel_bg = sel_bg if sel_bg is not null else self.fg
    self.sel_bg_br = sel_bg_br if sel_bg_br is not null else self.fg_br

    self.width = width
    self.height = height

    # Outline
    conf_outline = conf.outline if outline is True else outline
    # conf_outline might be a bare bool (True) rather than a config section with colors
    has_outline_conf = hasattr(conf_outline, 'fg') and not isinstance(conf_outline, bool)
    self.outline = bool(outline)
    self.outline_double = False
    if outline_double is not null:
      self.outline_double = outline_double
    elif self.outline and has_outline_conf and hasattr(conf_outline, 'double_lined'):
      self.outline_double = bool(conf_outline.double_lined)
    self.outline_fg = _color(conf_outline.fg, green) if (self.outline and has_outline_conf and outline_fg is null) else (outline_fg if outline_fg is not null else green)
    self.outline_fg_br = (conf_outline.fg_br if (self.outline and has_outline_conf) else False) if outline_fg_br is null else outline_fg_br
    self.outline_bg = _color(conf_outline.bg, black) if (self.outline and has_outline_conf and outline_bg is null) else (outline_bg if outline_bg is not null else black)
    self.outline_bg_br = (conf_outline.bg_br if (self.outline and has_outline_conf) else False) if outline_bg_br is null else outline_bg_br
    self.outline_active_fg = _color(conf_outline.active.fg, green) if (self.outline and has_outline_conf and outline_active_fg is null) else (outline_active_fg if outline_active_fg is not null else green)
    self.outline_active_fg_br = (conf_outline.active.fg_br if (self.outline and has_outline_conf) else False) if outline_active_fg_br is null else outline_active_fg_br
    self.outline_active_bg = _color(conf_outline.active.bg, black) if (self.outline and has_outline_conf and outline_active_bg is null) else (outline_active_bg if outline_active_bg is not null else black)
    self.outline_active_bg_br = (conf_outline.active.bg_br if (self.outline and has_outline_conf) else False) if outline_active_bg_br is null else outline_active_bg_br

    if self.outline:
      self.row_offset += 1
      self.col_offset += 1

    # Compat with InputFields container
    self.row = 0
    self.col = 0
    self.cursor_line = 0
    self.cursor_col = 0

    return self

  def get_text(self):
    return ", ".join(self.items)

  content = property(lambda self: self.get_text())

  def _contains_screen_pos(self, screen_row, screen_col):
    top = self.row_offset - (1 if self.outline else 0)
    bottom = self.row_offset + self.height - 1 + (1 if self.outline else 0)
    left_edge = self.col_offset - (1 if self.outline else 0)
    right_edge = self.col_offset + self.width - 1 + (1 if self.outline else 0)
    return top <= screen_row <= bottom and left_edge <= screen_col <= right_edge

  def _place_cursor_at_screen_pos(self, screen_row, screen_col):
    vis_row = screen_row - self.row_offset
    if 0 <= vis_row < self.height:
      idx = self._scroll + vis_row
      if idx < len(self.items):
        self._cursor = idx

  def _ensure_cursor_visible(self):
    if self.items:
      self._cursor = max(0, min(self._cursor, len(self.items) - 1))
    else:
      self._cursor = 0
    if self._cursor < self._scroll:
      self._scroll = self._cursor
    elif self._cursor >= self._scroll + self.height:
      self._scroll = self._cursor - self.height + 1

  async def draw_outline(self, active=False):
    if not self.outline:
      return
    if active:
      ofg, ofg_br = self.outline_active_fg, self.outline_active_fg_br
      obg, obg_br = self.outline_active_bg, self.outline_active_bg_br
    else:
      ofg, ofg_br = self.outline_fg, self.outline_fg_br
      obg, obg_br = self.outline_bg, self.outline_bg_br

    if self.outline_double:
      tl, horiz, tr, vert, bl, br_char = (bytes([c]).decode('cp437') for c in (201, 205, 187, 186, 200, 188))
    else:
      tl, horiz, tr, vert, bl, br_char = (bytes([c]).decode('cp437') for c in (218, 196, 191, 179, 192, 217))

    outline_row = self.row_offset - 1
    outline_col = self.col_offset - 1

    need_nowrap = (outline_col - 1 + self.width + 2) >= self.user.screen_width
    if need_nowrap:
      ansi_wrap(self.user, False)

    ansi_color(self.user, fg=ofg, fg_br=ofg_br, bg=obg, bg_br=obg_br)

    # Top border (with optional title)
    await ansi_move(self.user, outline_row, outline_col)
    if self.title and self.title is not null:
      title_text = str(self.title)[:self.width - 2]
      remaining = self.width - len(title_text)
      left_bar = remaining // 2
      right_bar = remaining - left_bar
      await send(self.user, tl + horiz * left_bar + title_text + horiz * right_bar + tr, drain=False)
    else:
      await send(self.user, tl + horiz * self.width + tr, drain=False)

    for r in range(self.height):
      await ansi_move(self.user, outline_row + 1 + r, outline_col)
      await send(self.user, vert, drain=False)
      await ansi_move(self.user, outline_row + 1 + r, outline_col + self.width + 1)
      await send(self.user, vert, drain=False)

    await ansi_move(self.user, outline_row + self.height + 1, outline_col)
    hint = " Ins:Add Del:Rem "
    if len(hint) <= self.width:
      remaining = self.width - len(hint)
      left_bar = remaining // 2
      right_bar = remaining - left_bar
      await send(self.user, bl + horiz * left_bar + hint + horiz * right_bar + br_char, drain=False)
    else:
      await send(self.user, bl + horiz * self.width + br_char, drain=False)

    if need_nowrap:
      ansi_wrap(self.user, True)

    await self.user.writer.drain()

  async def draw_field(self, start_at=None, end_row=null):
    self._ensure_cursor_visible()
    for vis_row in range(self.height):
      idx = self._scroll + vis_row
      await ansi_move(self.user, self.row_offset + vis_row, self.col_offset)
      if idx < len(self.items):
        item_text = str(self.items[idx])[:self.width]
        padded = item_text.ljust(self.width)
        if idx == self._cursor:
          ansi_color(self.user, fg=self.sel_fg, fg_br=self.sel_fg_br, bg=self.sel_bg, bg_br=self.sel_bg_br)
        else:
          ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
        await send(self.user, padded, drain=False)
      else:
        ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
        await send(self.user, " " * self.width, drain=False)
    await self.user.writer.drain()

  async def _do_add(self):
    """Show inline input at bottom of the list field for adding a new item."""
    # Use the row below the outline (or below the field if no outline)
    input_row = self.row_offset + self.height + (1 if self.outline else 0)
    if input_row > self.user.screen_height:
      input_row = self.user.screen_height

    await ansi_move(self.user, input_row, self.col_offset)
    ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=False)
    await send(self.user, "Add: ", drain=True)

    result = await InputField.create(
      parent=null, user=self.user,
      conf=config.input_fields.input_field,
      width=self.width - 5, max_length=50, content=""
    )

    new_item = result.content.strip() if result and hasattr(result, 'content') else ""

    # Clear the add line
    await ansi_move(self.user, input_row, self.col_offset)
    ansi_color(self.user, fg=self.fg, fg_br=False, bg=self.bg, bg_br=False)
    await send(self.user, " " * self.width, drain=True)

    if not new_item:
      return

    # Check duplicate
    if new_item.lower() in (i.lower() for i in self.items):
      await self._show_error("Already in list.")
      return

    # Validate
    if self.validate:
      ok, err = await self.validate(new_item)
      if not ok:
        await self._show_error(err or "Invalid.")
        return

    self.items.append(new_item)
    self._cursor = len(self.items) - 1
    self._ensure_cursor_visible()
    await self.draw_field()

  async def _show_error(self, msg):
    """Flash an error message below the field."""
    err_row = self.row_offset + self.height + (1 if self.outline else 0)
    if err_row > self.user.screen_height:
      err_row = self.user.screen_height
    await ansi_move(self.user, err_row, self.col_offset)
    ansi_color(self.user, fg=red, fg_br=True, bg=self.bg, bg_br=False)
    await send(self.user, msg[:self.width].ljust(self.width), drain=True)
    await asyncio.sleep(1.5)
    await ansi_move(self.user, err_row, self.col_offset)
    ansi_color(self.user, fg=self.fg, fg_br=False, bg=self.bg, bg_br=False)
    await send(self.user, " " * self.width, drain=True)

  async def run(self):
    while True:
      key = await get_input_key(self.user)

      if key == tab:
        return RetVals(key=tab, content=self.get_text(), row=self.row, col=self.col,
                       insert_mode=False)
      if key == shift_tab:
        return RetVals(key=shift_tab, content=self.get_text(), row=self.row, col=self.col,
                       insert_mode=False)
      if key == cr:
        return RetVals(key=cr, content=self.get_text(), row=self.row, col=self.col,
                       insert_mode=False)

      if key == up:
        if self.items and self._cursor > 0:
          self._cursor -= 1
          self._ensure_cursor_visible()
          await self.draw_field()
        elif not self.items and self.parent:
          return RetVals(key=up, content=self.get_text(), row=self.row, col=self.col,
                         insert_mode=False)
        continue

      if key == down:
        if self.items and self._cursor < len(self.items) - 1:
          self._cursor += 1
          self._ensure_cursor_visible()
          await self.draw_field()
        elif not self.items and self.parent:
          return RetVals(key=down, content=self.get_text(), row=self.row, col=self.col,
                         insert_mode=False)
        continue

      if key == left:
        if self.parent:
          return RetVals(key=left, content=self.get_text(), row=self.row, col=self.col,
                         insert_mode=False)

      if key == right:
        if self.parent:
          return RetVals(key=right, content=self.get_text(), row=self.row, col=self.col,
                         insert_mode=False)

      if key == insert:
        await self._do_add()
        continue

      if key == delete or key == back:
        if self.items:
          del self.items[self._cursor]
          if self._cursor >= len(self.items) and self.items:
            self._cursor = len(self.items) - 1
          self._ensure_cursor_visible()
          await self.draw_field()
        continue

      if key == click:
        btn = getattr(key, 'button', None)
        if btn == left:
          click_row, click_col = key.row, key.col
          if self._contains_screen_pos(click_row, click_col):
            self._place_cursor_at_screen_pos(click_row, click_col)
            self._ensure_cursor_visible()
            await self.draw_field()
          elif self.parent:
            return RetVals(key=click, button=btn, click_row=click_row, click_col=click_col,
                           content=self.get_text(), row=self.row, col=self.col,
                           insert_mode=False)
        continue


class InputFields:
  BUTTONS_START = -100  # button indices are -100, -101, -102, etc.

  def __init__(self, user):
    self.fields = []
    self.user = user
    self._buttons = []  # list of (name, field) tuples

  async def add_field(self, **kwargs):
    field = await InputField.create(parent=self, user=self.user, allow_edit=True, **kwargs)
    bottom = field.row_offset + field.height - 1 + (1 if field.outline else 0)
    if bottom > self.user.screen_height:
      raise ValueError(
        f"InputField does not fit on screen: field bottom row {bottom} exceeds "
        f"screen height {self.user.screen_height}. "
        f"Reduce the number of fields, use pagination, or increase screen size."
      )
    self.fields.append(field)
    return field

  async def add_button(self, name, **kwargs):
    """Add a named button (e.g. 'submit', 'login', 'cancel').
    Auto-sizes width to fit the content text if no explicit width given."""
    if 'width' not in kwargs:
      text = kwargs.get('content', '')
      if not text:
        text = str(config.input_fields.submit.text or name)
      kwargs['width'] = len(text)
    # Buttons don't need the cursor margin column
    kwargs.setdefault('no_cursor_margin', True)
    field = await InputField.create(
      parent=self, user=self.user, allow_edit=False,
      conf=config.input_fields.submit, **kwargs
    )
    bottom = field.row_offset + field.height - 1 + (1 if field.outline else 0)
    if bottom > self.user.screen_height:
      raise ValueError(
        f"Button '{name}' does not fit on screen: bottom row {bottom} exceeds "
        f"screen height {self.user.screen_height}."
      )
    # create() already draws the outline and field, so don't draw again here
    self._buttons.append((name, field))
    return field

  async def add_select(self, options, value="", **kwargs):
    """Add a SelectField (inline cycling selector) to the form."""
    field = await SelectField.create(parent=self, user=self.user, options=options, value=value, **kwargs)
    bottom = field.row_offset + field.height - 1
    if bottom > self.user.screen_height:
      raise ValueError(f"SelectField does not fit on screen: bottom row {bottom} exceeds screen height {self.user.screen_height}.")
    self.fields.append(field)
    return field

  async def add_list(self, items=None, **kwargs):
    """Add a ListField (vertical list editor) to the form."""
    field = await ListField.create(parent=self, user=self.user, items=items, **kwargs)
    bottom = field.row_offset + field.height - 1 + (1 if field.outline else 0)
    if bottom > self.user.screen_height:
      raise ValueError(f"ListField does not fit on screen: bottom row {bottom} exceeds screen height {self.user.screen_height}.")
    self.fields.append(field)
    return field

  async def add_submit_button(self, **kwargs):
    """Convenience: add a button named 'submit'."""
    return await self.add_button("submit", **kwargs)

  def _button_index(self, i):
    """Convert a button list index (0, 1, 2...) to a navigation index (-100, -101, -102...)."""
    return self.BUTTONS_START - i

  def _button_list_index(self, nav_index):
    """Convert a navigation index back to a button list index."""
    return self.BUTTONS_START - nav_index

  def _is_button_index(self, idx):
    return idx <= self.BUTTONS_START and idx > self.BUTTONS_START - len(self._buttons)

  def _get_field_or_button(self, idx):
    if self._is_button_index(idx):
      return self._buttons[self._button_list_index(idx)][1]
    return self.fields[idx]

  def _find_field_at(self, screen_row, screen_col):
    """Given a 1-based screen coordinate, return the index of the field/button that
    contains it, or null if none."""
    for i, field in enumerate(self.fields):
      if field._contains_screen_pos(screen_row, screen_col):
        return i
    for i, (name, field) in enumerate(self._buttons):
      if field._contains_screen_pos(screen_row, screen_col):
        return self._button_index(i)
    return null

  def _next_index(self, idx):
    """Advance to the next field/button, wrapping around."""
    if self._is_button_index(idx):
      bi = self._button_list_index(idx)
      if bi + 1 < len(self._buttons):
        return self._button_index(bi + 1)
      return 0  # wrap to first field
    elif idx + 1 < len(self.fields):
      return idx + 1
    elif self._buttons:
      return self._button_index(0)  # first button
    return 0  # wrap

  def _prev_index(self, idx):
    """Go to the previous field/button, wrapping around."""
    if self._is_button_index(idx):
      bi = self._button_list_index(idx)
      if bi > 0:
        return self._button_index(bi - 1)
      return len(self.fields) - 1  # last field
    elif idx > 0:
      return idx - 1
    elif self._buttons:
      return self._button_index(len(self._buttons) - 1)  # last button
    return len(self.fields) - 1  # wrap

  def _make_result(self, button_name):
    return RetVals(
      key=cr,
      button=button_name,
      fields=[RetVals(content=f.get_text(), row=f.row, col=f.col) for f in self.fields]
    )

  async def run(self, start_index=0):
    """Run the input fields form.
    start_index: which field to activate first (0-based index into self.fields)."""
    # Enable mouse click reporting (normal tracking mode: ESC[?1000h)
    self.user.writer.write("\x1b[?1000h\x1b[?1002h")
    self.user.mouse_reporting = True
    await self.user.writer.drain()

    try:
      # Draw all fields and buttons in their initial (inactive) state
      for field in self.fields:
        if field.outline:
          await field.draw_outline(active=False)
        await field.draw_field()
      for name, btn in self._buttons:
        if btn.outline:
          await btn.draw_outline(active=False)
        await btn.draw_field()

      current_index = start_index
      last_index = null
      while True:
        current_field = self._get_field_or_button(current_index)

        if current_index != last_index:
          await current_field.draw_outline(active=True)
          if last_index is not null:
            prev = self._get_field_or_button(last_index)
            await prev.draw_outline(active=False)
          # Just position the cursor on the field — no need to redraw content
          await ansi_move_deferred(self.user,
                          row=current_field.row_offset + current_field.row,
                          col=current_field.col_offset + current_field.col,
                          drain=True)

        last_index = current_index
        r = await current_field.run()

        if r.key == click:
          # Only handle left button press, ignore release and other buttons
          btn = getattr(r, 'button', None)
          if btn == left:
            clicked = self._find_field_at(r.click_row, r.click_col)
            if clicked is not null:
              if self._is_button_index(clicked):
                bi = self._button_list_index(clicked)
                return self._make_result(self._buttons[bi][0])
              else:
                current_index = clicked
                self.fields[clicked]._place_cursor_at_screen_pos(r.click_row, r.click_col)
        elif r.key == cr:
          if self._is_button_index(current_index):
            bi = self._button_list_index(current_index)
            return self._make_result(self._buttons[bi][0])
          # Enter on a field advances to next
          current_index = self._next_index(current_index)
        elif r.key == tab:
          current_index = self._next_index(current_index)
        elif r.key == shift_tab:
          current_index = self._prev_index(current_index)
        elif r.key == left or r.key == up:
          current_index = self._prev_index(current_index)
        elif r.key == right or r.key == down:
          current_index = self._next_index(current_index)
    finally:
      # Disable mouse click reporting
      self.user.writer.write("\x1b[?1002l\x1b[?1000l")
      self.user.mouse_reporting = False
      await self.user.writer.drain()


class Line:
  """One logical line of content. Stores a list of Word/Space tokens as the
  canonical model. Text representation is derived lazily and cached.

  All edit operations (insert_char, delete_char, etc.) manipulate the token
  list directly, merging adjacent same-type tokens and splitting on type
  boundaries as needed. The cached text is invalidated on every mutation.
  The total length is cached and maintained incrementally so len(line) is O(1)."""
  __slots__ = ('_tokens', 'level', '_cached_text', '_length')

  def __init__(self, text="", level=0):
    self._tokens = _tokenize(text)
    self.level = level
    self._cached_text = text
    self._length = len(text)

  # ---- Text representation (derived) ----

  @property
  def text(self):
    """Derived plain-text representation, cached. Reading this is cheap;
    writing it retokenizes the entire line."""
    if self._cached_text is None:
      parts = []
      for tok in self._tokens:
        if isinstance(tok, Word):
          parts.append(tok.text)
        else:
          parts.append(' ' * tok.count)
      self._cached_text = ''.join(parts)
    return self._cached_text

  @text.setter
  def text(self, new_text):
    self._tokens = _tokenize(new_text)
    self._cached_text = new_text
    self._length = len(new_text)

  def get_tokens(self):
    return self._tokens

  def __len__(self):
    return self._length

  # ---- Token-based edit operations ----

  def _invalidate_text(self):
    self._cached_text = None

  def _merge_adjacent(self, idx):
    """If tokens at idx and idx+1 are the same type, merge them. Then check
    idx-1 and idx for the same. Used after a deletion to keep the invariant
    that adjacent tokens are different types."""
    # Forward merge (idx and idx+1)
    if 0 <= idx < len(self._tokens) - 1:
      a, b = self._tokens[idx], self._tokens[idx + 1]
      if isinstance(a, Word) and isinstance(b, Word):
        a.text += b.text
        del self._tokens[idx + 1]
      elif isinstance(a, Space) and isinstance(b, Space):
        a.count += b.count
        del self._tokens[idx + 1]
    # Backward merge (idx-1 and idx)
    if 0 < idx < len(self._tokens):
      a, b = self._tokens[idx - 1], self._tokens[idx]
      if isinstance(a, Word) and isinstance(b, Word):
        a.text += b.text
        del self._tokens[idx]
      elif isinstance(a, Space) and isinstance(b, Space):
        a.count += b.count
        del self._tokens[idx]

  def _find_token(self, col):
    """Find (index, offset, token) for the given character column. If col is
    past the end, returns (len(tokens), 0, None)."""
    pos = 0
    for i, tok in enumerate(self._tokens):
      tlen = len(tok)
      if col < pos + tlen:
        return i, col - pos, tok
      pos += tlen
    return len(self._tokens), 0, None

  def insert_char(self, col, ch):
    """Insert a single character at the given column. Splits and merges
    tokens as needed to maintain the invariant that no two adjacent tokens
    are the same type."""
    self._invalidate_text()
    self._length += 1
    is_space = (ch == ' ')
    pos = 0
    for i, tok in enumerate(self._tokens):
      tlen = len(tok)
      if col <= pos + tlen:
        offset = col - pos
        if is_space and isinstance(tok, Space):
          tok.count += 1
          return
        if not is_space and isinstance(tok, Word):
          tok.text = tok.text[:offset] + ch + tok.text[offset:]
          return
        # Different type from the token we landed in.
        if offset == 0:
          # At the START of this token — try extending the previous one
          if i > 0:
            prev = self._tokens[i - 1]
            if is_space and isinstance(prev, Space):
              prev.count += 1
              return
            if not is_space and isinstance(prev, Word):
              prev.text += ch
              return
          # Insert a new token before this one
          self._tokens.insert(i, Space(1) if is_space else Word(ch))
          return
        if offset == tlen:
          # At the END of this token — try extending the next one
          if i + 1 < len(self._tokens):
            nxt = self._tokens[i + 1]
            if is_space and isinstance(nxt, Space):
              nxt.count += 1
              return
            if not is_space and isinstance(nxt, Word):
              nxt.text = ch + nxt.text
              return
          self._tokens.insert(i + 1, Space(1) if is_space else Word(ch))
          return
        # Inside a token of the opposite type — split it
        if isinstance(tok, Word):
          left = Word(tok.text[:offset])
          right = Word(tok.text[offset:])
          self._tokens[i] = left
          self._tokens.insert(i + 1, Space(1))
          self._tokens.insert(i + 2, right)
        else:
          self._tokens[i] = Space(offset)
          self._tokens.insert(i + 1, Word(ch))
          self._tokens.insert(i + 2, Space(tlen - offset))
        return
      pos += tlen
    # col is at or past the end — append
    if self._tokens:
      last = self._tokens[-1]
      if is_space and isinstance(last, Space):
        last.count += 1
        return
      if not is_space and isinstance(last, Word):
        last.text += ch
        return
    self._tokens.append(Space(1) if is_space else Word(ch))

  def delete_char(self, col):
    """Delete a single character at the given column. Removes empty tokens
    and merges any newly-adjacent same-type tokens."""
    if col < 0 or col >= self._length:
      return
    self._invalidate_text()
    self._length -= 1
    pos = 0
    for i, tok in enumerate(self._tokens):
      tlen = len(tok)
      if col < pos + tlen:
        offset = col - pos
        if isinstance(tok, Word):
          tok.text = tok.text[:offset] + tok.text[offset + 1:]
          if not tok.text:
            del self._tokens[i]
            self._merge_adjacent(i - 1 if i > 0 else 0)
        else:
          tok.count -= 1
          if tok.count == 0:
            del self._tokens[i]
            self._merge_adjacent(i - 1 if i > 0 else 0)
        return
      pos += tlen

  def insert_text(self, col, text):
    """Insert a multi-character string at the given column. Cheaply
    implemented as: derive text, splice, retokenize."""
    if not text:
      return
    cur = self.text
    new = cur[:col] + text + cur[col:]
    self.text = new  # uses setter, retokenizes

  def split_at(self, col):
    """Split this line at the given column. After this call, this line
    contains everything up to col; returns the text after col as a string
    (caller is responsible for creating the new Line)."""
    cur = self.text
    after = cur[col:]
    self.text = cur[:col]
    return after

  def append_text(self, text):
    """Append text to the end of this line."""
    if not text:
      return
    self.text = self.text + text


class DisplayRow:
  """One row on screen. A logical line may span multiple display rows.
  start_col/end_col are positions within the logical line's text. The
  trim_trailing field marks how many characters at the end of the visible
  slice are trailing spaces consumed by a wrap (rendered as fill, not text)."""
  __slots__ = ('line_index', 'start_col', 'end_col', 'margin_prefix', 'trim_trailing')
  def __init__(self, line_index, start_col, end_col, margin_prefix="", trim_trailing=0):
    self.line_index = line_index
    self.start_col = start_col
    self.end_col = end_col
    self.margin_prefix = margin_prefix
    self.trim_trailing = trim_trailing


def _build_grid_for_field(field):
  """Build a 2D grid of Cell objects representing the wrapped layout of all
  lines in `field`. Each cell maps a (grid_row, grid_col) screen position
  to its source token + offset in the line's text. Margin and fill cells
  have token=None and col_in_line=-1.

  Also builds field.line_char_to_grid: per logical line, a list of
  (grid_row, grid_col) tuples indexed by col_in_line. Includes one extra
  entry at index len(line) for the end-of-line cursor position. Used by
  cursor lookup to convert (line, col) → screen position in O(1).

  Side-effects on `field`:
    field.grid: list[list[Cell]]
    field.line_grid_ranges: list[(first_grid_row, last_grid_row)] per logical line
    field.line_char_to_grid: list[list[(grid_row, grid_col)]] per logical line

  Wrap mode only — caller must verify."""
  total_width = field.width if field.no_cursor_margin else field.width - 1
  grid = []
  line_grid_ranges = []
  line_char_to_grid = []
  fill_char = field.fill or ' '

  for li, line in enumerate(field.lines):
    prefix = field._margin_prefix(line.level)
    mw = len(prefix)
    line_usable = total_width - mw
    if line_usable <= 0:
      line_usable = 1

    line_first_row = len(grid)
    char_to_grid = [None] * (len(line) + 1)  # +1 for end-of-line cursor pos

    def new_row():
      row = []
      for c in prefix:
        row.append(Cell(char=c, token=None, line_index=li))
      return row

    def finish_row(row):
      while len(row) < total_width:
        row.append(Cell(char=fill_char, token=None, line_index=li))
      grid.append(row)

    cur_row = new_row()
    line_col = 0
    tokens = list(line.get_tokens())  # local copy so we can splice for hard-break

    if not tokens:
      # Empty line — end-of-line cursor at start of the (only) grid row's content area
      char_to_grid[0] = (len(grid), mw)
      finish_row(cur_row)
      line_grid_ranges.append((line_first_row, len(grid) - 1))
      line_char_to_grid.append(char_to_grid)
      continue

    i = 0
    while i < len(tokens):
      tok = tokens[i]
      tlen = len(tok)
      remaining_in_row = total_width - len(cur_row)

      if isinstance(tok, Word):
        if tlen <= remaining_in_row:
          for k in range(tlen):
            char_to_grid[line_col + k] = (len(grid), len(cur_row))
            cur_row.append(Cell(char=tok.text[k], token=tok, token_offset=k,
                                line_index=li, col_in_line=line_col + k))
          line_col += tlen
          i += 1
        elif len(cur_row) == mw:
          # Empty row (just margin) — hard-break the word
          chunk = remaining_in_row
          for k in range(chunk):
            char_to_grid[line_col + k] = (len(grid), len(cur_row))
            cur_row.append(Cell(char=tok.text[k], token=tok, token_offset=k,
                                line_index=li, col_in_line=line_col + k))
          line_col += chunk
          finish_row(cur_row)
          cur_row = new_row()
          tokens[i] = Word(tok.text[chunk:])
          # stay on i
        else:
          # Wrap before this word. If the row ends with space cells, consume one.
          if cur_row and isinstance(cur_row[-1].token, Space):
            popped = cur_row.pop()
            # Re-record the consumed char's grid position as the cell that
            # was just vacated by the pop — i.e. just past the last visible
            # content cell. This way the cursor at that col_in_line lands
            # right after the last visible char on the previous row, not at
            # the screen's right edge.
            char_to_grid[popped.col_in_line] = (len(grid), len(cur_row))
          finish_row(cur_row)
          cur_row = new_row()
          # don't advance i — re-process the word on the new row
      else:
        # Space token
        if tlen <= remaining_in_row:
          for k in range(tlen):
            char_to_grid[line_col + k] = (len(grid), len(cur_row))
            cur_row.append(Cell(char=' ', token=tok, token_offset=k,
                                line_index=li, col_in_line=line_col + k))
          line_col += tlen
          i += 1
        else:
          # Spaces straddle the row boundary
          fit = remaining_in_row
          for k in range(fit):
            char_to_grid[line_col + k] = (len(grid), len(cur_row))
            cur_row.append(Cell(char=' ', token=tok, token_offset=k,
                                line_index=li, col_in_line=line_col + k))
          line_col += fit
          # The space at line_col is consumed by the wrap
          char_to_grid[line_col] = (len(grid), total_width)
          finish_row(cur_row)
          cur_row = new_row()
          line_col += 1
          spaces_remaining = tlen - fit - 1
          if spaces_remaining > 0:
            for k in range(spaces_remaining):
              char_to_grid[line_col + k] = (len(grid), len(cur_row))
              cur_row.append(Cell(char=' ', token=tok, token_offset=fit + 1 + k,
                                  line_index=li, col_in_line=line_col + k))
            line_col += spaces_remaining
          i += 1

    # Record end-of-line cursor position (one past the last char)
    if char_to_grid[len(line) - 1] is not None and len(line) > 0:
      last_r, last_c = char_to_grid[len(line) - 1]
      eol_r, eol_c = last_r, last_c + 1
      # If the last char was at the rightmost grid col, the EOL position
      # is just past it (cursor margin column).
      char_to_grid[len(line)] = (eol_r, eol_c)
    elif len(line) == 0:
      char_to_grid[0] = (len(grid), mw)
    # else: last char wasn't placed (consumed) — fall back to row end
    if char_to_grid[len(line)] is None:
      char_to_grid[len(line)] = (len(grid), len(cur_row))

    # Emit final row for this line (always at least one row even if empty)
    finish_row(cur_row)
    line_grid_ranges.append((line_first_row, len(grid) - 1))
    line_char_to_grid.append(char_to_grid)

  field.grid = grid
  field.line_grid_ranges = line_grid_ranges
  field.line_char_to_grid = line_char_to_grid


class InputField:
  def __init__(self):
    pass

  # ---- Construction ----

  @classmethod
  async def create(cls, parent=null, user=null, conf=null, height=null, width=null,
                   width_from_end=null, height_from_end=null, max_length=null,
                   max_lines=null, fg=null, fg_br=null, bg=null, bg_br=null,
                   fill=null, fill_fg_br=null, fill_fg=null, fill_bg=null,
                   fill_bg_br=null, outline=null, outline_double=null, outline_fg=null,
                   outline_fg_br=null, outline_bg=null, outline_bg_br=null,
                   outline_active_fg=null, outline_active_fg_br=null,
                   outline_active_bg=null, outline_active_bg_br=null,
                   insert_mode=null, word_wrap=null, content="", allow_edit=null,
                   margin_char=null, no_cursor_margin=False, mask_char=null):
    self = cls()
    self.user = user if user is not null else parent.user
    self.parent = parent

    # Screen position where the field content starts (1-based)
    self.row_offset = self.user.cur_row
    self.col_offset = self.user.cur_col

    # Cursor: logical position within self.lines
    self.cursor_line = 0
    self.cursor_col = 0

    # Scroll state
    self.scroll_offset = 0
    self.h_scroll = 0

    # Compatibility aliases used by InputFields container
    self.row = 0
    self.col = 0
    self.content_row_offset = 0

    # The column the cursor tries to maintain when moving up/down
    self._updown_col = 0

    # Wrap-mode cell grid (parallel structure built by _compute_display_rows)
    self.grid = []
    self.line_grid_ranges = []
    self.line_char_to_grid = []

    # Resolve config vs explicit parameters
    if conf is null:
      conf = config.input_fields.input_field

    def _color(val, default=white):
      if val and val in colors:
        return colors[val]
      if isinstance(val, int):
        return val
      return default

    # Outline
    conf_outline = conf.outline if outline is null else outline
    self.outline = bool(conf_outline)
    self.outline_double = conf_outline.double_lined if self.outline and hasattr(conf_outline, 'double_lined') else False
    if outline_double is not null:
      self.outline_double = outline_double
    self.outline_fg = _color(conf_outline.fg, green) if (self.outline and outline_fg is null) else (outline_fg if outline_fg is not null else green)
    self.outline_fg_br = (conf_outline.fg_br if self.outline else False) if outline_fg_br is null else outline_fg_br
    self.outline_bg = _color(conf_outline.bg, black) if (self.outline and outline_bg is null) else (outline_bg if outline_bg is not null else black)
    self.outline_bg_br = (conf_outline.bg_br if self.outline else False) if outline_bg_br is null else outline_bg_br
    self.outline_active_fg = _color(conf_outline.active.fg, green) if (self.outline and outline_active_fg is null) else (outline_active_fg if outline_active_fg is not null else green)
    self.outline_active_fg_br = (conf_outline.active.fg_br if self.outline else False) if outline_active_fg_br is null else outline_active_fg_br
    self.outline_active_bg = _color(conf_outline.active.bg, black) if (self.outline and outline_active_bg is null) else (outline_active_bg if outline_active_bg is not null else black)
    self.outline_active_bg_br = (conf_outline.active.bg_br if self.outline else False) if outline_active_bg_br is null else outline_active_bg_br

    if self.outline:
      self.row_offset += 1
      self.col_offset += 1

    # Dimensions
    self.height = height if height is not null else (conf.height or 1)
    self.width = width if width is not null else (conf.width or 40)
    self.height_from_end = conf.height_from_end if height_from_end is null else height_from_end
    self.width_from_end = conf.width_from_end if width_from_end is null else width_from_end

    if self.height_from_end and self.height_from_end is not null and height is null:
      self.height = self.user.screen_height - self.row_offset + 1 - int(self.height_from_end)
    if (not self.width or self.width is null) and self.width_from_end is not null:
      self.width = self.user.screen_width - self.col_offset + 1 - self.width_from_end

    _is_multiline = (word_wrap if word_wrap is not null else (conf.word_wrap or False)) or self.height > 1
    default_max = 100000 if _is_multiline else 1000
    self.max_length = max_length if max_length is not null else (conf.max_length or default_max)
    self.max_lines = conf.max_lines if max_lines is null else max_lines

    # Colors
    self.fg = _color(conf.content.fg, white) if fg is null else fg
    self.fg_br = (conf.content.fg_br or False) if fg_br is null else fg_br
    _fill_present = bool(conf.blank.char if fill is null else fill)
    _fill_bg = _color(conf.blank.bg, black) if fill_bg is null else fill_bg
    if bg is not null:
      self.bg = bg
    elif _fill_present:
      self.bg = _fill_bg
    else:
      self.bg = _color(conf.content.bg, black)
    self.bg_br = (conf.content.bg_br or False) if bg_br is null else bg_br

    # Fill character and colors
    self.fill = conf.blank.char if fill is null else fill
    self.fill = self.fill or " "
    if type(self.fill) is int:
      self.fill = bytes([self.fill]).decode('cp437')
    self.fill_fg = _color(conf.blank.fg, white) if fill_fg is null else fill_fg
    self.fill_fg_br = (conf.blank.fg_br or False) if fill_fg_br is null else fill_fg_br
    self.fill_bg = _color(conf.blank.bg, black) if fill_bg is null else fill_bg
    self.fill_bg_br = (conf.blank.bg_br or False) if fill_bg_br is null else fill_bg_br

    # Behavior
    self.word_wrap = (conf.word_wrap or False) if word_wrap is null else word_wrap
    self.insert_mode = (conf.insert_mode or False) if insert_mode is null else insert_mode
    self.allow_edit = (conf.allow_edit if conf.allow_edit is not null else True) if allow_edit is null else allow_edit
    conf_margin = conf.margin_char if conf and conf.margin_char else ">"
    self.margin_char = conf_margin if margin_char is null else margin_char
    self.no_cursor_margin = no_cursor_margin
    self.mask_char = mask_char if mask_char is not null else None

    # Warn if masked field can scroll (user can't see scrolling with masked input)
    if self.mask_char and self.max_length > self.width - (0 if self.no_cursor_margin else 1):
      import logging
      logging.getLogger("dirtyfork").warning(
        "Masked field has max_length (%d) > visible width (%d) — scrolling will be invisible to the user",
        self.max_length, self.width - (0 if self.no_cursor_margin else 1))

    # Horizontal scroll step (single-line fields always scroll by 1 for smoother UX)
    if self.height == 1:
      self.scroll_step = 1
    else:
      user_conf = getattr(self.user, 'conf', null)
      if user_conf and user_conf is not null and user_conf.scroll_step:
        try:
          self.scroll_step = int(user_conf.scroll_step)
        except (ValueError, TypeError):
          self.scroll_step = 8
      else:
        self.scroll_step = 8

    # Parse initial content into self.lines
    if not content and conf.text:
      content = str(conf.text)
    self.lines = []
    if isinstance(content, list):
      self._parse_blocks(content)
    elif content:
      self._parse_blocks([Block(text=content, level=0)])
    if not self.lines:
      self.lines = [Line("", 0)]

    # Compute display layout
    self.display_rows = []
    self._compute_display_rows()

    # Draw and possibly run
    if parent is null:
      if self.outline:
        await self.draw_outline(active=True)
      if self.col_offset + self.width - 1 == self.user.screen_width:
        ansi_wrap(self.user, False)
      await self.draw_field()
      return await self.run()

    return self

  # ---- Content parsing ----

  def _parse_blocks(self, blocks):
    """Parse a list of Block objects into self.lines."""
    self.lines = []
    for block in blocks:
      # Split block text on newlines to create one Line per paragraph
      parts = block.text.split("\n")
      for i, part in enumerate(parts):
        self.lines.append(Line(part, block.level))

  def _max_display_level(self):
    """Max quote level that can be displayed given the field width.
    Reserves at least min_edit_width chars (or half the usable width) for editing."""
    usable = self.width - (0 if self.no_cursor_margin else 1)
    cfg_min = int(config.min_edit_width) if config.min_edit_width else 10
    min_edit = max(cfg_min, usable // 2)
    # margin for level N = N + 1 chars, so max level = usable - min_edit - 1
    return max(1, usable - min_edit - 1)

  def _margin_prefix(self, level):
    """Return the margin prefix string for a given quote level (capped for display)."""
    if level <= 0:
      return ""
    display_level = min(level, self._max_display_level())
    return (self.margin_char * display_level) + " "

  def _margin_width(self, level):
    """Return the character width of the margin prefix for a given level (capped for display)."""
    if level <= 0:
      return 0
    display_level = min(level, self._max_display_level())
    return display_level + 1

  # ---- Display row computation ----

  def _compute_display_rows(self):
    """Recompute the layout from self.lines. In wrap mode this builds the
    cell grid; in non-wrap mode it builds the simpler display_rows list."""
    if self.word_wrap:
      self.display_rows = []
      _build_grid_for_field(self)
      return

    rows = []
    for li, line in enumerate(self.lines):
      prefix = self._margin_prefix(line.level)
      rows.append(DisplayRow(li, 0, len(line.text), prefix))
    if not rows:
      rows.append(DisplayRow(0, 0, 0, ""))
    self.display_rows = rows
    self.grid = []
    self.line_grid_ranges = []
    self.line_char_to_grid = []

  def _display_row_for_cursor(self):
    """Find the display row index (= grid row index in wrap mode) that contains
    (cursor_line, cursor_col)."""
    if self.word_wrap and self.line_char_to_grid:
      char_to_grid = self.line_char_to_grid[self.cursor_line]
      if 0 <= self.cursor_col < len(char_to_grid) and char_to_grid[self.cursor_col] is not None:
        return char_to_grid[self.cursor_col][0]
      # Fallback: last grid row of this line
      if self.cursor_line < len(self.line_grid_ranges):
        return self.line_grid_ranges[self.cursor_line][1]
      return 0

    for i, dr in enumerate(self.display_rows):
      if dr.line_index != self.cursor_line:
        continue
      # Check if cursor_col falls within this display row's range
      if dr.start_col <= self.cursor_col <= dr.end_col:
        return i
      # Special case: cursor at end_col of a row that equals start_col of next row
      # (only when at end of text on this display row)
      if self.cursor_col == dr.end_col and i + 1 < len(self.display_rows):
        next_dr = self.display_rows[i + 1]
        if next_dr.line_index == self.cursor_line and next_dr.start_col == self.cursor_col:
          # Cursor is at the boundary; prefer the next row
          continue
      if self.cursor_col == dr.end_col:
        return i
    # Fallback: find last display row for this line
    last = 0
    for i, dr in enumerate(self.display_rows):
      if dr.line_index == self.cursor_line:
        last = i
    return last

  def _set_updown_col(self):
    """Set _updown_col as the offset of the cursor within its display row's
    content area (i.e. screen column from the left edge of content, ignoring
    margin). Must be called after the layout is up to date."""
    if self.word_wrap and self.line_char_to_grid:
      char_to_grid = self.line_char_to_grid[self.cursor_line]
      if 0 <= self.cursor_col < len(char_to_grid) and char_to_grid[self.cursor_col] is not None:
        gr, gc = char_to_grid[self.cursor_col]
      elif char_to_grid and char_to_grid[-1] is not None:
        gr, gc = char_to_grid[-1]
      else:
        gr, gc = 0, 0
      mw = len(self._margin_prefix(self.lines[self.cursor_line].level))
      self._updown_col = max(0, gc - mw)
      return
    dri = self._display_row_for_cursor()
    self._updown_col = self.cursor_col - self.display_rows[dri].start_col

  def _first_display_row_for_line(self, line_index):
    """Find the first display row index for a given logical line."""
    for i, dr in enumerate(self.display_rows):
      if dr.line_index == line_index:
        return i
    return 0

  # ---- Cursor / screen coordinate conversion ----

  def _cursor_to_screen(self):
    """Convert cursor position to screen (row, col). Returns (screen_row, screen_col)."""
    if self.word_wrap and self.line_char_to_grid:
      char_to_grid = self.line_char_to_grid[self.cursor_line]
      if 0 <= self.cursor_col < len(char_to_grid) and char_to_grid[self.cursor_col] is not None:
        gr, gc = char_to_grid[self.cursor_col]
      else:
        # Fallback: end of line position
        gr, gc = (char_to_grid[-1] if char_to_grid and char_to_grid[-1] is not None
                  else (self.line_grid_ranges[self.cursor_line][1], 0))
      screen_row = self.row_offset + gr - self.scroll_offset
      screen_col = self.col_offset + gc
      return screen_row, screen_col

    dri = self._display_row_for_cursor()
    dr = self.display_rows[dri]
    screen_row = self.row_offset + dri - self.scroll_offset
    mw = len(dr.margin_prefix)
    screen_col = self.col_offset + mw + self.cursor_col - self.h_scroll
    return screen_row, screen_col

  def _sync_compat_cursor(self):
    """Update self.row/self.col/self.content_row_offset for InputFields container compatibility."""
    dri = self._display_row_for_cursor()
    total_rows = len(self.grid) if self.word_wrap else len(self.display_rows)
    if total_rows > 0:
      self.scroll_offset = max(0, min(self.scroll_offset, total_rows - 1))
    self.content_row_offset = self.scroll_offset
    self.row = dri - self.scroll_offset
    sr, sc = self._cursor_to_screen()
    self.col = sc - self.col_offset

  def _ensure_cursor_visible(self):
    """Scroll if cursor's display row is off screen."""
    dri = self._display_row_for_cursor()
    if dri < self.scroll_offset:
      self.scroll_offset = dri
    elif dri >= self.scroll_offset + self.height:
      self.scroll_offset = dri - self.height + 1
    self._sync_compat_cursor()

  async def _position_cursor(self, drain=True):
    """Move the terminal cursor to the current logical cursor position."""
    sr, sc = self._cursor_to_screen()
    await ansi_move(self.user, sr, sc)
    if self.insert_mode:
      await self._show_insert_cursor(drain=drain)
    elif drain:
      await self.user.writer.drain()

  # ---- Drawing ----

  async def _draw_line(self, dri):
    """Draw one display row to screen."""
    if self.word_wrap:
      await self._draw_grid_row(dri)
      return
    screen_row = self.row_offset + dri - self.scroll_offset
    if screen_row < self.row_offset or screen_row >= self.row_offset + self.height:
      return  # off screen
    dr = self.display_rows[dri]
    line = self.lines[dr.line_index]
    mw = len(dr.margin_prefix)
    usable = self.width if self.no_cursor_margin else self.width - 1

    need_nowrap = (self.col_offset + self.width - 1 >= self.user.screen_width)
    if need_nowrap:
      ansi_wrap(self.user, False)

    await ansi_move(self.user, screen_row, self.col_offset)

    if self.word_wrap:
      # Draw margin prefix
      if dr.margin_prefix:
        ansi_color(self.user, fg=self.outline_fg, fg_br=self.outline_fg_br, bg=self.bg, bg_br=self.bg_br)
        await send(self.user, dr.margin_prefix, drain=False)
      # Draw text content for this display row's slice
      text_slice = line.text[dr.start_col:dr.end_col]
      if text_slice:
        ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
        await send(self.user, self.mask_char * len(text_slice) if self.mask_char else text_slice, drain=False)
      # Fill remainder
      drawn = mw + len(text_slice)
      fill_count = usable - drawn
      if fill_count > 0:
        ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br, bg=self.fill_bg, bg_br=self.fill_bg_br)
        await send(self.user, self.fill * fill_count, drain=False)
      # Cursor margin column
      if not self.no_cursor_margin:
        remaining = self.width - max(drawn, usable)
        if remaining > 0:
          ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br, bg=self.fill_bg, bg_br=self.fill_bg_br)
          await send(self.user, self.fill * remaining, drain=False)
    else:
      # No word wrap: apply horizontal scroll
      # Draw margin prefix (only if visible after h_scroll)
      h = self.h_scroll
      if dr.margin_prefix and h < mw:
        visible_prefix = dr.margin_prefix[h:]
        ansi_color(self.user, fg=self.outline_fg, fg_br=self.outline_fg_br, bg=self.bg, bg_br=self.bg_br)
        await send(self.user, visible_prefix[:usable], drain=False)
        drawn = len(visible_prefix[:usable])
      else:
        drawn = 0
      # Draw text content
      if drawn < usable:
        text_start = max(0, h - mw)
        text_vis = line.text[text_start:text_start + usable - drawn]
        if h < mw:
          pass  # already started drawing from prefix
        if text_vis:
          ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
          await send(self.user, self.mask_char * len(text_vis) if self.mask_char else text_vis, drain=False)
          drawn += len(text_vis)
      # Fill
      fill_count = usable - drawn
      if fill_count > 0:
        ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br, bg=self.fill_bg, bg_br=self.fill_bg_br)
        await send(self.user, self.fill * fill_count, drain=False)
      if not self.no_cursor_margin:
        remaining = self.width - max(drawn, usable)
        if remaining > 0:
          ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br, bg=self.fill_bg, bg_br=self.fill_bg_br)
          await send(self.user, self.fill * remaining, drain=False)

    if need_nowrap:
      ansi_wrap(self.user, True)

  def _row_to_line(self, grid_row_idx):
    """Find the logical line index that owns this grid row."""
    for li, (first, last) in enumerate(self.line_grid_ranges):
      if first <= grid_row_idx <= last:
        return li
    return None

  async def _draw_grid_row(self, grid_row_idx):
    """Draw one row of the wrap-mode cell grid. Cells are classified as
    margin (col < margin width), content (token != None), or fill (token
    == None and col >= margin width). Consecutive cells of the same kind
    are batched into a single send so the lock contention with the stars
    background task stays low."""
    if grid_row_idx >= len(self.grid):
      return
    row_cells = self.grid[grid_row_idx]
    screen_row = self.row_offset + grid_row_idx - self.scroll_offset
    if screen_row < self.row_offset or screen_row >= self.row_offset + self.height:
      return  # off screen

    li = self._row_to_line(grid_row_idx)
    mw = len(self._margin_prefix(self.lines[li].level)) if li is not None else 0

    need_nowrap = (self.col_offset + self.width - 1 >= self.user.screen_width)
    if need_nowrap:
      ansi_wrap(self.user, False)

    await ansi_move(self.user, screen_row, self.col_offset)

    # Walk cells, group runs of same kind
    prev_kind = None
    prev_chars = []

    async def flush():
      nonlocal prev_chars
      if not prev_chars:
        return
      if prev_kind == 'margin':
        ansi_color(self.user, fg=self.outline_fg, fg_br=self.outline_fg_br,
                   bg=self.bg, bg_br=self.bg_br)
      elif prev_kind == 'content':
        ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
      else:
        ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br,
                   bg=self.fill_bg, bg_br=self.fill_bg_br)
      await send(self.user, ''.join(prev_chars), drain=False)
      prev_chars = []

    for col_idx, cell in enumerate(row_cells):
      if col_idx < mw:
        kind = 'margin'
      elif cell.token is not None:
        kind = 'content'
      else:
        kind = 'fill'
      char = cell.char
      if kind == 'content' and self.mask_char:
        char = self.mask_char
      if kind != prev_kind:
        await flush()
        prev_kind = kind
      prev_chars.append(char)
    await flush()

    # Cursor margin column (extra fill cell at the right)
    if not self.no_cursor_margin:
      usable = self.width - 1
      drawn = len(row_cells)
      remaining = self.width - max(drawn, usable)
      if remaining > 0:
        ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br,
                   bg=self.fill_bg, bg_br=self.fill_bg_br)
        await send(self.user, self.fill * remaining, drain=False)

    if need_nowrap:
      ansi_wrap(self.user, True)

  async def _draw_line_tail(self, dri, from_col):
    """Draw the visible portion of one display row's text starting from
    `from_col` (a column within line.text), then fill the rest of the row
    with fill chars. Used by single-char edits to avoid a full field
    redraw. Non-word-wrap mode only — caller must verify."""
    screen_row = self.row_offset + dri - self.scroll_offset
    if screen_row < self.row_offset or screen_row >= self.row_offset + self.height:
      return  # off screen
    dr = self.display_rows[dri]
    line = self.lines[dr.line_index]
    mw = len(dr.margin_prefix)
    usable = self.width if self.no_cursor_margin else self.width - 1

    need_nowrap = (self.col_offset + self.width - 1 >= self.user.screen_width)
    if need_nowrap:
      ansi_wrap(self.user, False)

    h = self.h_scroll
    text_start = max(from_col, h)
    # Position within the field where the text starts
    field_offset = mw + (text_start - h)
    if field_offset >= usable:
      # Nothing visible to draw — just fill the row's tail
      visible_text = ""
      remaining_in_field = max(0, usable - field_offset)
    else:
      remaining_in_field = usable - field_offset
      visible_text = line.text[text_start:text_start + remaining_in_field]
      if self.mask_char:
        visible_text = self.mask_char * len(visible_text)

    screen_col = self.col_offset + field_offset
    await ansi_move(self.user, screen_row, screen_col)

    if visible_text:
      ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
      await send(self.user, visible_text, drain=False)

    # Fill the remaining width up to the right edge of the usable area.
    fill_count = remaining_in_field - len(visible_text)
    if fill_count > 0:
      ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br,
                 bg=self.fill_bg, bg_br=self.fill_bg_br)
      await send(self.user, self.fill * fill_count, drain=False)

    if need_nowrap:
      ansi_wrap(self.user, True)

  def _snapshot_display_rows(self):
    """Capture a lightweight snapshot of the current VISIBLE layout for
    later comparison by the fast path. In wrap mode, snapshots the cell
    chars for each visible screen row (grid[scroll_offset..+height]),
    so the diff works correctly even when scroll_offset changes. In
    non-wrap mode, snapshots display_rows."""
    if self.word_wrap:
      result = []
      for si in range(self.height):
        gi = self.scroll_offset + si
        if gi < len(self.grid):
          result.append(tuple(c.char for c in self.grid[gi]))
        else:
          result.append(None)  # empty screen row (below content)
      return result
    return [(dr.line_index, dr.start_col, dr.end_col, dr.margin_prefix)
            for dr in self.display_rows]

  async def _draw_grid_row_diff(self, grid_row_idx, old_row_chars):
    """Draw only the cells that differ between `old_row_chars` (a tuple of
    chars from a previous snapshot) and the current grid row. Unchanged
    cells are skipped so ambient stars aren't disturbed."""
    if grid_row_idx >= len(self.grid):
      return
    row = self.grid[grid_row_idx]
    screen_row = self.row_offset + grid_row_idx - self.scroll_offset
    if screen_row < self.row_offset or screen_row >= self.row_offset + self.height:
      return

    li = self._row_to_line(grid_row_idx)
    mw = len(self._margin_prefix(self.lines[li].level)) if li is not None else 0

    need_nowrap = (self.col_offset + self.width - 1 >= self.user.screen_width)
    if need_nowrap:
      ansi_wrap(self.user, False)

    old_len = len(old_row_chars) if old_row_chars else 0
    new_len = len(row)
    max_len = max(old_len, new_len)

    col = 0
    while col < max_len:
      new_char = row[col].char if col < new_len else self.fill
      old_char = old_row_chars[col] if col < old_len else None
      if new_char == old_char:
        col += 1
        continue
      # Start of a changed run — collect consecutive changed cells of same kind
      run_start = col
      run_chars = []
      run_kind = None
      while col < max_len:
        nc = row[col].char if col < new_len else self.fill
        oc = old_row_chars[col] if col < old_len else None
        if nc == oc:
          break
        cell = row[col] if col < new_len else None
        if col < mw:
          kind = 'margin'
        elif cell is not None and cell.token is not None:
          kind = 'content'
        else:
          kind = 'fill'
        ch = nc
        if kind == 'content' and self.mask_char:
          ch = self.mask_char
        if run_kind is not None and kind != run_kind:
          # Flush the current run before switching color
          if run_kind == 'margin':
            ansi_color(self.user, fg=self.outline_fg, fg_br=self.outline_fg_br,
                       bg=self.bg, bg_br=self.bg_br)
          elif run_kind == 'content':
            ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
          else:
            ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br,
                       bg=self.fill_bg, bg_br=self.fill_bg_br)
          await ansi_move(self.user, screen_row, self.col_offset + run_start)
          await send(self.user, ''.join(run_chars), drain=False)
          run_start = col
          run_chars = []
        run_kind = kind
        run_chars.append(ch)
        col += 1
      if run_chars:
        if run_kind == 'margin':
          ansi_color(self.user, fg=self.outline_fg, fg_br=self.outline_fg_br,
                     bg=self.bg, bg_br=self.bg_br)
        elif run_kind == 'content':
          ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
        else:
          ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br,
                     bg=self.fill_bg, bg_br=self.fill_bg_br)
        await ansi_move(self.user, screen_row, self.col_offset + run_start)
        await send(self.user, ''.join(run_chars), drain=False)

    if need_nowrap:
      ansi_wrap(self.user, True)

  async def _redraw_changed_rows(self, old_snapshot):
    """Redraw cells that differ from `old_snapshot`. In wrap mode, compares
    cell-by-cell within each row so only the actually-changed cells are
    written (preserving ambient stars in unchanged cells). In non-wrap mode,
    redraws whole rows from the first changed row onward."""
    new_snapshot = self._snapshot_display_rows()
    new_len = len(new_snapshot)
    old_len = len(old_snapshot)
    visible_start = self.scroll_offset
    visible_end_new = min(self.scroll_offset + self.height, new_len)

    if self.word_wrap:
      # Cell-level diff: walk each visible screen row, compare old snapshot
      # (which is also screen-relative) vs current grid content.
      for si in range(self.height):
        old_row = old_snapshot[si] if si < len(old_snapshot) else None
        gi = self.scroll_offset + si
        if gi < len(self.grid):
          new_row = new_snapshot[si] if si < len(new_snapshot) else None
          if old_row == new_row:
            continue  # screen row unchanged — skip entirely
          await self._draw_grid_row_diff(gi, old_row)
        else:
          # Screen row is below all content — blank it if it wasn't before
          if old_row is not None:
            screen_row = self.row_offset + si
            await ansi_move(self.user, screen_row, self.col_offset)
            ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br,
                       bg=self.fill_bg, bg_br=self.fill_bg_br)
            await send(self.user, self.fill * self.width, drain=False)
      return

    # Non-wrap: find first changed row, redraw from there
    first_changed = min(new_len, old_len)
    for i in range(min(new_len, old_len)):
      if new_snapshot[i] != old_snapshot[i]:
        first_changed = i
        break
    if new_len != old_len and first_changed >= min(new_len, old_len):
      first_changed = min(new_len, old_len)
    if first_changed >= max(new_len, old_len):
      return
    for i in range(max(first_changed, self.scroll_offset), visible_end_new):
      await self._draw_line(i)
    if old_len > new_len:
      blank_start = max(new_len - self.scroll_offset, 0)
      blank_end = min(old_len - self.scroll_offset, self.height)
      for vr in range(blank_start, blank_end):
        screen_row = self.row_offset + vr
        await ansi_move(self.user, screen_row, self.col_offset)
        ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br,
                   bg=self.fill_bg, bg_br=self.fill_bg_br)
        await send(self.user, self.fill * self.width, drain=False)

  async def _draw_visible(self):
    """Redraw all visible display rows and position cursor."""
    total_rows = len(self.grid) if self.word_wrap else len(self.display_rows)
    for i in range(self.scroll_offset, min(self.scroll_offset + self.height, total_rows)):
      await self._draw_line(i)
    # Fill any remaining screen rows below content
    for vr in range(total_rows - self.scroll_offset, self.height):
      screen_row = self.row_offset + vr
      if screen_row >= self.row_offset + self.height:
        break
      need_nowrap = (self.col_offset + self.width - 1 >= self.user.screen_width)
      if need_nowrap:
        ansi_wrap(self.user, False)
      await ansi_move(self.user, screen_row, self.col_offset)
      usable = self.width if self.no_cursor_margin else self.width - 1
      ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br, bg=self.fill_bg, bg_br=self.fill_bg_br)
      await send(self.user, self.fill * usable, drain=False)
      if not self.no_cursor_margin:
        await send(self.user, self.fill, drain=False)
      if need_nowrap:
        ansi_wrap(self.user, True)
    await self._position_cursor(drain=True)

  async def draw_field(self, start_at=top, end_row=null):
    """Public draw method for compatibility with InputFields container."""
    self._ensure_cursor_visible()
    await self._draw_visible()

  async def draw_outline(self, active=False):
    """Draw the box outline around the field."""
    if not self.outline:
      return
    if active:
      ofg, ofg_br = self.outline_active_fg, self.outline_active_fg_br
      obg, obg_br = self.outline_active_bg, self.outline_active_bg_br
    else:
      ofg, ofg_br = self.outline_fg, self.outline_fg_br
      obg, obg_br = self.outline_bg, self.outline_bg_br

    if self.outline_double:
      tl, horiz, tr, vert, bl, br_char = (bytes([c]).decode('cp437') for c in (201, 205, 187, 186, 200, 188))
    else:
      tl, horiz, tr, vert, bl, br_char = (bytes([c]).decode('cp437') for c in (218, 196, 191, 179, 192, 217))

    outline_row = self.row_offset - 1
    outline_col = self.col_offset - 1

    need_nowrap = (outline_col - 1 + self.width + 2) >= self.user.screen_width
    if need_nowrap:
      ansi_wrap(self.user, False)

    ansi_color(self.user, fg=ofg, fg_br=ofg_br, bg=obg, bg_br=obg_br)

    # Top border
    await ansi_move(self.user, outline_row, outline_col)
    await send(self.user, tl + horiz * self.width + tr, drain=False)

    # Side borders
    for r in range(self.height):
      await ansi_move(self.user, outline_row + 1 + r, outline_col)
      await send(self.user, vert, drain=False)
      await ansi_move(self.user, outline_row + 1 + r, outline_col + self.width + 1)
      await send(self.user, vert, drain=False)

    # Bottom border
    await ansi_move(self.user, outline_row + self.height + 1, outline_col)
    await send(self.user, bl + horiz * self.width + br_char, drain=False)

    # Restore cursor
    await self._position_cursor(drain=True)

    if need_nowrap:
      ansi_wrap(self.user, True)

  async def _show_insert_cursor(self, drain=True):
    """Show the insert-mode cursor: character at cursor with inverted colors."""
    sr, sc = self._cursor_to_screen()
    await ansi_move(self.user, sr, sc)
    line = self.lines[self.cursor_line]
    if self.cursor_col < len(line.text):
      ch = self.mask_char if self.mask_char else line.text[self.cursor_col]
      ansi_color(self.user, fg=self.bg, fg_br=self.bg_br, bg=self.fg, bg_br=self.fg_br)
      if sc >= self.user.screen_width:
        ansi_wrap(self.user, False)
      await send(self.user, ch, drain=False)
      await ansi_move(self.user, sr, sc)
      ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
    else:
      ansi_color(self.user, fg=self.fill_bg, fg_br=self.fill_bg_br, bg=self.fill_fg, bg_br=self.fill_fg_br)
      if sc >= self.user.screen_width:
        ansi_wrap(self.user, False)
      await send(self.user, self.fill, drain=False)
      await ansi_move(self.user, sr, sc)
      ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
    if drain:
      await self.user.writer.drain()

  async def _hide_insert_cursor(self):
    """Restore normal display of the character at the current cursor position."""
    if not self.insert_mode:
      return
    sr, sc = self._cursor_to_screen()
    await ansi_move(self.user, sr, sc)
    line = self.lines[self.cursor_line]
    if self.cursor_col < len(line.text):
      ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
      await send(self.user, self.mask_char if self.mask_char else line.text[self.cursor_col], drain=False)
    else:
      ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br, bg=self.fill_bg, bg_br=self.fill_bg_br)
      await send(self.user, self.fill, drain=False)
    await ansi_move(self.user, sr, sc)

  # ---- Public content API ----

  def get_text(self):
    """Reconstruct text content from self.lines."""
    return "\n".join(line.text for line in self.lines)

  def get_blocks(self):
    """Return content as a list of Block objects. Adjacent lines at the same level are merged."""
    if not self.lines:
      return [Block("", 0)]
    blocks = []
    current_text = self.lines[0].text
    current_level = self.lines[0].level
    for line in self.lines[1:]:
      if line.level == current_level:
        current_text += "\n" + line.text
      else:
        blocks.append(Block(text=current_text, level=current_level))
        current_text = line.text
        current_level = line.level
    blocks.append(Block(text=current_text, level=current_level))
    return blocks

  def _total_char_count(self):
    """Total character count across all lines (newlines count as 1 each)."""
    total = sum(len(line.text) for line in self.lines)
    total += len(self.lines) - 1  # newlines between lines
    return total

  # ---- Hit testing ----

  def _contains_screen_pos(self, screen_row, screen_col):
    """Check if a 1-based screen position falls within this field's area (including outline)."""
    top_edge = self.row_offset - (1 if self.outline else 0)
    bottom = self.row_offset + self.height - 1 + (1 if self.outline else 0)
    left_edge = self.col_offset - (1 if self.outline else 0)
    right_edge = self.col_offset + self.width - 1 + (1 if self.outline else 0)
    return top_edge <= screen_row <= bottom and left_edge <= screen_col <= right_edge

  def _place_cursor_at_screen_pos(self, screen_row, screen_col):
    """Move cursor to position corresponding to a 1-based screen click."""
    vis_row = screen_row - self.row_offset
    vis_row = max(0, min(vis_row, self.height - 1))

    if self.word_wrap and self.grid:
      gr = self.scroll_offset + vis_row
      gr = max(0, min(gr, len(self.grid) - 1))
      row = self.grid[gr]
      gc = screen_col - self.col_offset
      gc = max(0, min(gc, len(row) - 1))
      cell = row[gc]
      if cell.col_in_line >= 0:
        self.cursor_line = cell.line_index
        self.cursor_col = cell.col_in_line
      else:
        # Click on margin or fill — find the nearest content cell on this row
        target_li = self._row_to_line(gr)
        mw = len(self._margin_prefix(self.lines[target_li].level)) if target_li is not None else 0
        # Find rightmost content cell at or before the click
        for c_idx in range(min(gc, len(row) - 1), mw - 1, -1):
          c = row[c_idx]
          if c.col_in_line >= 0:
            self.cursor_line = c.line_index
            self.cursor_col = c.col_in_line + (1 if c_idx < gc else 0)
            break
        else:
          self.cursor_line = target_li if target_li is not None else 0
          self.cursor_col = 0
      self._set_updown_col()
      self._ensure_cursor_visible()
      return

    dri = self.scroll_offset + vis_row
    dri = max(0, min(dri, len(self.display_rows) - 1))
    dr = self.display_rows[dri]
    line = self.lines[dr.line_index]
    mw = len(dr.margin_prefix)

    rel_col = screen_col - self.col_offset - mw + self.h_scroll
    text_col = dr.start_col + max(0, rel_col)
    text_col = max(0, min(text_col, len(line.text)))
    text_col = min(text_col, dr.end_col)

    self.cursor_line = dr.line_index
    self.cursor_col = text_col
    self._set_updown_col()
    self._ensure_cursor_visible()

  # ---- Main run loop ----

  async def run(self):
    result = await self._run_loop()
    await self._cleanup_field()
    return result

  async def _cleanup_field(self):
    """Clean up after editing. Standalone fields erase themselves; container fields do nothing."""
    if self.parent:
      return
    ansi_color(self.user, fg=white, bg=black, fg_br=False, bg_br=False)
    if self.outline:
      outline_row = self.row_offset - 1
      outline_col = self.col_offset - 1
      await ansi_move(self.user, outline_row, outline_col)
      await send(self.user, " " * (self.width + 2), drain=False)
      for r in range(self.height):
        await ansi_move(self.user, outline_row + 1 + r, outline_col)
        await send(self.user, " ", drain=False)
        await ansi_move(self.user, outline_row + 1 + r, outline_col + self.width + 1)
        await send(self.user, " ", drain=False)
      await ansi_move(self.user, outline_row + self.height + 1, outline_col)
      await send(self.user, " " * (self.width + 2), drain=False)
    for r in range(self.height):
      await ansi_move(self.user, self.row_offset + r, self.col_offset)
      await send(self.user, " " * self.width, drain=False)
    await ansi_move(self.user, self.row_offset, self.col_offset)
    await send(self.user, cr + lf, drain=True)

  def _make_retvals(self, key):
    """Build a RetVals for returning to caller/container."""
    return RetVals(key=key, content=self.get_text(), row=self.row, col=self.col,
                   insert_mode=self.insert_mode)

  async def _run_loop(self):
    self._pending_key = None
    while True:
      if self._pending_key is not None:
        key = self._pending_key
        self._pending_key = None
      else:
        key = await get_input_key(self.user)

      # -- Enter --
      if key == cr:
        r = await self._handle_enter()
        if r:
          return r
        continue

      # -- Tab / Shift+Tab --
      if key == tab:
        if self.parent:
          return self._make_retvals(tab)
        continue
      if key == shift_tab:
        if self.parent:
          return self._make_retvals(shift_tab)
        continue

      # -- Arrow keys --
      if key == left:
        r = await self._handle_left()
        if r:
          return r
        continue
      if key == right:
        r = await self._handle_right()
        if r:
          return r
        continue
      if key == up:
        r = await self._handle_up()
        if r:
          return r
        continue
      if key == down:
        r = await self._handle_down()
        if r:
          return r
        continue

      # -- Home / End --
      if key == home:
        await self._handle_home()
        continue
      if key == end:
        await self._handle_end()
        continue

      # -- Ctrl+Home / Ctrl+End: jump to top / bottom of all text --
      if key == ctrl_home:
        await self._handle_ctrl_home()
        continue
      if key == ctrl_end:
        await self._handle_ctrl_end()
        continue

      # -- PageUp / PageDown --
      if key == pgup:
        await self._handle_pgup()
        continue
      if key == pgdn:
        await self._handle_pgdn()
        continue

      # -- Delete / Backspace --
      if key == delete:
        if self.allow_edit:
          await self._handle_delete()
        continue
      if key == back:
        if self.allow_edit:
          await self._handle_backspace()
        continue

      # -- Insert mode toggle --
      if key == insert:
        self.insert_mode = not self.insert_mode
        if self.insert_mode:
          await self._show_insert_cursor(drain=True)
        else:
          await self._hide_insert_cursor()
          await self.user.writer.drain()
        continue

      # -- Mouse click --
      if key == click:
        btn = getattr(key, 'button', None)
        if btn != left:
          continue
        click_row, click_col = key.row, key.col
        if self._contains_screen_pos(click_row, click_col):
          if self.insert_mode:
            await self._hide_insert_cursor()
          self._place_cursor_at_screen_pos(click_row, click_col)
          await self._position_cursor(drain=True)
        elif self.parent:
          return RetVals(key=click, button=btn, click_row=click_row, click_col=click_col,
                         content=self.get_text(), row=self.row, col=self.col,
                         insert_mode=self.insert_mode)
        continue

      # -- Printable character --
      if isinstance(key, str) and len(key) == 1 and ord(key) >= 32:
        if self.allow_edit:
          await self._handle_char(key, drain=not self.user.batch_mode)
          if self.user.batch_mode:
            batch = []
            while self.user.batch_mode:
              next_key = await get_input_key(self.user)
              if isinstance(next_key, str) and len(next_key) == 1 and ord(next_key) >= 32:
                batch.append(next_key)
              else:
                if batch:
                  await self._handle_batch(batch)
                  batch = []
                self._pending_key = next_key
                break
            if batch:
              await self._handle_batch(batch)
          continue
        # Read-only: return the key to the caller
        return self._make_retvals(key)

  # ---- Key handlers ----

  async def _handle_enter(self):
    if self.allow_edit:
      if self.height == 1:
        return self._make_retvals(cr)

      if self.max_length and self._total_char_count() >= self.max_length:
        return None

      line = self.lines[self.cursor_line]

      # Enter on empty quoted line: decrease level
      if line.level > 0 and not line.text:
        old_snapshot = self._snapshot_display_rows() if self.word_wrap else None
        saved_scroll_offset = self.scroll_offset
        line.level -= 1
        self._compute_display_rows()
        self._ensure_cursor_visible()
        if self.word_wrap and old_snapshot is not None:
          await self._redraw_changed_rows(old_snapshot)
          await self._position_cursor(drain=True)
        else:
          await self._draw_visible()
        return None

      # Check max_lines
      if self.max_lines and len(self.lines) >= self.max_lines:
        return None

      # Split line at cursor: this line keeps the prefix; the suffix becomes a new line
      split_col = self.cursor_col  # save for potential undo
      new_level = line.level
      old_snapshot = self._snapshot_display_rows() if self.word_wrap else None
      saved_scroll_offset = self.scroll_offset
      after_text = line.split_at(self.cursor_col)
      self.lines.insert(self.cursor_line + 1, Line(after_text, new_level))

      # Move cursor to start of new line
      self.cursor_line += 1
      self.cursor_col = 0
      self._updown_col = 0

      self._compute_display_rows()

      # Check max_lines with word wrap (reflow might exceed limit)
      if self.max_lines and len(self.lines) > self.max_lines:
        # Undo: rejoin the two lines
        self.cursor_line -= 1
        self.lines[self.cursor_line].append_text(after_text)
        del self.lines[self.cursor_line + 1]
        self.cursor_col = split_col
        self._compute_display_rows()
        self._ensure_cursor_visible()
        return None

      self._ensure_cursor_visible()
      if self.word_wrap and old_snapshot is not None:
        await self._redraw_changed_rows(old_snapshot)
        await self._position_cursor(drain=True)
      else:
        await self._draw_visible()
      return None
    else:
      return self._make_retvals(cr)

  async def _handle_left(self):
    if not self.allow_edit and self.parent:
      return self._make_retvals(left)

    if self.cursor_col > 0:
      if self.insert_mode:
        await self._hide_insert_cursor()
      old_h = self.h_scroll
      self.cursor_col -= 1
      self._set_updown_col()
      self._ensure_cursor_visible()
      self._ensure_h_scroll()
      if self.h_scroll != old_h:
        await self._draw_visible()
      await self._position_cursor(drain=True)
    elif self.cursor_line > 0:
      if self.insert_mode:
        await self._hide_insert_cursor()
      self.cursor_line -= 1
      self.cursor_col = len(self.lines[self.cursor_line].text)
      self._set_updown_col()
      self._ensure_cursor_visible()
      self._ensure_h_scroll()
      await self._redraw_or_reposition()
    else:
      if self.height == 1 and self.parent:
        return self._make_retvals(left)
    return None

  async def _handle_right(self):
    if not self.allow_edit and self.parent:
      return self._make_retvals(right)

    line = self.lines[self.cursor_line]
    if self.cursor_col < len(line.text):
      if self.insert_mode:
        await self._hide_insert_cursor()
      old_h = self.h_scroll
      self.cursor_col += 1
      self._set_updown_col()
      self._ensure_cursor_visible()
      self._ensure_h_scroll()
      if self.h_scroll != old_h:
        await self._draw_visible()
      await self._position_cursor(drain=True)
    elif self.cursor_line + 1 < len(self.lines):
      if self.insert_mode:
        await self._hide_insert_cursor()
      self.cursor_line += 1
      self.cursor_col = 0
      self._updown_col = 0
      self._ensure_cursor_visible()
      self._ensure_h_scroll()
      await self._redraw_or_reposition()
    else:
      if self.height == 1 and self.parent:
        return self._make_retvals(right)
    return None

  def _grid_move_to_row(self, target_gr):
    """Place the cursor at the cell on `target_gr` whose column-within-content
    is closest to `self._updown_col`. Used by grid-mode up/down/pgup/pgdn.
    Updates self.cursor_line and self.cursor_col. Caller is responsible for
    redraw/reposition."""
    if not (0 <= target_gr < len(self.grid)):
      return
    target_li = self._row_to_line(target_gr)
    if target_li is None:
      return
    mw = len(self._margin_prefix(self.lines[target_li].level))
    target_gc = mw + self._updown_col
    row = self.grid[target_gr]
    if target_gc >= len(row):
      target_gc = len(row) - 1
    cell = row[target_gc]
    if cell.col_in_line >= 0:
      self.cursor_line = target_li
      self.cursor_col = cell.col_in_line
      return
    # Fill cell — fall back to the position right after the rightmost
    # content cell on this row.
    for gc in range(target_gc - 1, mw - 1, -1):
      c = row[gc]
      if c.col_in_line >= 0:
        self.cursor_line = target_li
        self.cursor_col = c.col_in_line + 1
        return
    # No content on this row at all — cursor at the line's start
    self.cursor_line = target_li
    self.cursor_col = 0

  async def _handle_up(self):
    if not self.allow_edit and self.parent:
      return self._make_retvals(up)

    if self.word_wrap and self.line_char_to_grid:
      cur_gr = self._display_row_for_cursor()
      if cur_gr > 0:
        if self.insert_mode:
          await self._hide_insert_cursor()
        self._grid_move_to_row(cur_gr - 1)
        await self._redraw_or_reposition()
      else:
        if self.height == 1 and self.parent:
          return self._make_retvals(up)
      return None

    dri = self._display_row_for_cursor()
    if dri > 0:
      if self.insert_mode:
        await self._hide_insert_cursor()
      prev_dr = self.display_rows[dri - 1]
      self.cursor_line = prev_dr.line_index
      # Try to maintain the column
      target_col = prev_dr.start_col + self._updown_col
      max_col = min(prev_dr.end_col, len(self.lines[self.cursor_line]))
      self.cursor_col = min(target_col, max_col)
      self.cursor_col = max(prev_dr.start_col, self.cursor_col)
      await self._redraw_or_reposition()
    else:
      if self.height == 1 and self.parent:
        return self._make_retvals(up)
    return None

  async def _handle_down(self):
    if not self.allow_edit and self.parent:
      return self._make_retvals(down)

    if self.word_wrap and self.line_char_to_grid:
      cur_gr = self._display_row_for_cursor()
      if cur_gr + 1 < len(self.grid):
        if self.insert_mode:
          await self._hide_insert_cursor()
        self._grid_move_to_row(cur_gr + 1)
        await self._redraw_or_reposition()
      else:
        if self.height == 1 and self.parent:
          return self._make_retvals(down)
      return None

    dri = self._display_row_for_cursor()
    if dri + 1 < len(self.display_rows):
      if self.insert_mode:
        await self._hide_insert_cursor()
      next_dr = self.display_rows[dri + 1]
      self.cursor_line = next_dr.line_index
      target_col = next_dr.start_col + self._updown_col
      max_col = min(next_dr.end_col, len(self.lines[self.cursor_line]))
      self.cursor_col = min(target_col, max_col)
      self.cursor_col = max(next_dr.start_col, self.cursor_col)
      await self._redraw_or_reposition()
    else:
      if self.height == 1 and self.parent:
        return self._make_retvals(down)
    return None

  async def _handle_home(self):
    if self.insert_mode:
      await self._hide_insert_cursor()
    if self.word_wrap and self.line_char_to_grid:
      # Go to first content cell on the current grid row
      gr = self._display_row_for_cursor()
      target_li = self._row_to_line(gr)
      mw = len(self._margin_prefix(self.lines[target_li].level)) if target_li is not None else 0
      row = self.grid[gr]
      if mw < len(row):
        cell = row[mw]
        if cell.col_in_line >= 0:
          self.cursor_line = target_li
          self.cursor_col = cell.col_in_line
        else:
          # Empty row — cursor at line start
          self.cursor_line = target_li
          self.cursor_col = 0
      self._updown_col = 0
      self._ensure_cursor_visible()
      await self._position_cursor(drain=True)
      return
    dri = self._display_row_for_cursor()
    dr = self.display_rows[dri]
    self.cursor_col = dr.start_col
    self._updown_col = self.cursor_col - dr.start_col
    if not self.word_wrap and self.h_scroll != 0:
      self.h_scroll = 0
      self._ensure_cursor_visible()
      await self._draw_visible()
    else:
      self._ensure_cursor_visible()
      await self._position_cursor(drain=True)

  async def _handle_end(self):
    if self.insert_mode:
      await self._hide_insert_cursor()
    line = self.lines[self.cursor_line]
    if self.word_wrap and self.line_char_to_grid:
      # Find rightmost content cell on the current grid row
      gr = self._display_row_for_cursor()
      target_li = self._row_to_line(gr)
      mw = len(self._margin_prefix(self.lines[target_li].level)) if target_li is not None else 0
      row = self.grid[gr]
      end_col = 0
      for c_idx in range(len(row) - 1, mw - 1, -1):
        c = row[c_idx]
        if c.col_in_line >= 0:
          end_col = c.col_in_line + 1
          break
      else:
        end_col = 0
      self.cursor_line = target_li
      self.cursor_col = min(end_col, len(line))
      self._set_updown_col()
      self._ensure_cursor_visible()
      await self._position_cursor(drain=True)
      return
    self.cursor_col = len(line.text)
    self._updown_col = self.cursor_col
    self._ensure_h_scroll()
    self._ensure_cursor_visible()
    await self._draw_visible()

  async def _handle_ctrl_home(self):
    """Jump to the very top of the field (line 0, col 0)."""
    if self.insert_mode:
      await self._hide_insert_cursor()
    old_offset = self.scroll_offset
    self.cursor_line = 0
    self.cursor_col = 0
    self._updown_col = 0
    self.h_scroll = 0
    self._ensure_cursor_visible()
    if self.scroll_offset != old_offset:
      await self._draw_visible()
    else:
      await self._position_cursor(drain=True)

  async def _handle_ctrl_end(self):
    """Jump to the very bottom of the field (last line, end of last line)."""
    if self.insert_mode:
      await self._hide_insert_cursor()
    old_offset = self.scroll_offset
    self.cursor_line = len(self.lines) - 1
    self.cursor_col = len(self.lines[self.cursor_line])
    self._set_updown_col()
    self._ensure_h_scroll()
    self._ensure_cursor_visible()
    if self.scroll_offset != old_offset:
      await self._draw_visible()
    else:
      await self._position_cursor(drain=True)

  async def _handle_pgup(self):
    """Move cursor up by one screen height; scroll the field by the same amount."""
    if self.insert_mode:
      await self._hide_insert_cursor()
    old_offset = self.scroll_offset

    if self.word_wrap and self.line_char_to_grid:
      cur_gr = self._display_row_for_cursor()
      target_gr = max(0, cur_gr - self.height)
      self._grid_move_to_row(target_gr)
    else:
      dri = self._display_row_for_cursor()
      new_dri = max(0, dri - self.height)
      new_dr = self.display_rows[new_dri]
      self.cursor_line = new_dr.line_index
      target_col = new_dr.start_col + self._updown_col
      max_col = min(new_dr.end_col, len(self.lines[self.cursor_line]))
      self.cursor_col = max(new_dr.start_col, min(target_col, max_col))

    self._ensure_cursor_visible()
    if self.scroll_offset != old_offset:
      await self._draw_visible()
    else:
      await self._position_cursor(drain=True)

  async def _handle_pgdn(self):
    """Move cursor down by one screen height; scroll the field by the same amount."""
    if self.insert_mode:
      await self._hide_insert_cursor()
    old_offset = self.scroll_offset

    if self.word_wrap and self.line_char_to_grid:
      cur_gr = self._display_row_for_cursor()
      target_gr = min(len(self.grid) - 1, cur_gr + self.height)
      self._grid_move_to_row(target_gr)
    else:
      dri = self._display_row_for_cursor()
      new_dri = min(len(self.display_rows) - 1, dri + self.height)
      new_dr = self.display_rows[new_dri]
      self.cursor_line = new_dr.line_index
      target_col = new_dr.start_col + self._updown_col
      max_col = min(new_dr.end_col, len(self.lines[self.cursor_line]))
      self.cursor_col = max(new_dr.start_col, min(target_col, max_col))

    self._ensure_cursor_visible()
    if self.scroll_offset != old_offset:
      await self._draw_visible()
    else:
      await self._position_cursor(drain=True)

  async def _handle_delete(self):
    line = self.lines[self.cursor_line]
    if self.cursor_col < len(line.text):
      # Delete char at cursor
      saved_h_scroll = self.h_scroll
      saved_scroll_offset = self.scroll_offset
      saved_display_rows_len = len(self.display_rows)
      old_snapshot = self._snapshot_display_rows() if self.word_wrap else None
      line.delete_char(self.cursor_col)
      self._compute_display_rows()
      self._ensure_cursor_visible()
      # Fast path (non-wrap): write only the changed tail of this row
      if (not self.word_wrap
          and self.h_scroll == saved_h_scroll
          and self.scroll_offset == saved_scroll_offset
          and len(self.display_rows) == saved_display_rows_len):
        dri = self._display_row_for_cursor()
        await self._draw_line_tail(dri, self.cursor_col)
        await self._position_cursor(drain=True)
        return
      # Fast path (word-wrap): redraw only display rows whose content changed
      if self.word_wrap:
        await self._redraw_changed_rows(old_snapshot)
        await self._position_cursor(drain=True)
        return
      await self._draw_visible()
    elif self.cursor_line + 1 < len(self.lines):
      # Join with next line
      next_line = self.lines[self.cursor_line + 1]
      line.append_text(next_line.text)
      del self.lines[self.cursor_line + 1]
      self._compute_display_rows()
      self._ensure_cursor_visible()
      await self._draw_visible()

  async def _handle_backspace(self):
    line = self.lines[self.cursor_line]

    # At col 0, on a quoted line: decrease level
    if self.cursor_col == 0 and line.level > 0:
      line.level -= 1
      self._compute_display_rows()
      self._ensure_cursor_visible()
      await self._draw_visible()
      return

    if self.cursor_col > 0:
      # Delete char before cursor
      saved_h_scroll = self.h_scroll
      saved_scroll_offset = self.scroll_offset
      saved_display_rows_len = len(self.display_rows)
      old_snapshot = self._snapshot_display_rows() if self.word_wrap else None
      self.cursor_col -= 1
      line.delete_char(self.cursor_col)
      self._compute_display_rows()
      self._set_updown_col()
      self._ensure_cursor_visible()
      self._ensure_h_scroll()
      # Fast path (non-wrap): same as delete-in-middle
      if (not self.word_wrap
          and self.h_scroll == saved_h_scroll
          and self.scroll_offset == saved_scroll_offset
          and len(self.display_rows) == saved_display_rows_len):
        dri = self._display_row_for_cursor()
        await self._draw_line_tail(dri, self.cursor_col)
        await self._position_cursor(drain=True)
        return
      # Fast path (word-wrap): redraw only display rows whose content changed
      if self.word_wrap:
        await self._redraw_changed_rows(old_snapshot)
        await self._position_cursor(drain=True)
        return
      await self._draw_visible()
    elif self.cursor_line > 0:
      # Join with previous line
      prev_line = self.lines[self.cursor_line - 1]
      join_col = len(prev_line)
      prev_line.append_text(line.text)
      del self.lines[self.cursor_line]
      self.cursor_line -= 1
      self.cursor_col = join_col
      self._compute_display_rows()
      self._set_updown_col()
      self._ensure_cursor_visible()
      self._ensure_h_scroll()
      await self._draw_visible()

  async def _handle_char(self, ch, drain=True):
    """Handle a single printable character."""
    if self.max_length and self._total_char_count() >= self.max_length and not self.insert_mode:
      return

    line = self.lines[self.cursor_line]

    # Capture state needed to decide if we can use the fast (minimal-write) path
    was_at_end = (self.cursor_col == len(line.text))
    was_overwrite = self.insert_mode and self.cursor_col < len(line.text)
    saved_h_scroll = self.h_scroll
    saved_scroll_offset = self.scroll_offset
    saved_display_rows_len = len(self.display_rows) if hasattr(self, 'display_rows') else 0
    old_snapshot = self._snapshot_display_rows() if (self.word_wrap and hasattr(self, 'display_rows')) else None

    if self.insert_mode and self.cursor_col < len(line):
      # Overwrite mode: delete the char at cursor, then insert the new one
      line.delete_char(self.cursor_col)
      line.insert_char(self.cursor_col, ch)
    else:
      # Insert
      line.insert_char(self.cursor_col, ch)

    self.cursor_col += 1

    saved_lines = deepcopy(self.lines) if (self.word_wrap and self.max_lines) else None

    self._compute_display_rows()
    self._set_updown_col()

    # Check max_lines (word wrap reflow might push over)
    if self.max_lines and len(self.display_rows) > 0:
      # Count actual logical lines that have display rows
      if self.word_wrap:
        max_dri = len(self.display_rows)
        # max_lines applies to logical lines, not display rows
        pass

    self._ensure_cursor_visible()
    self._ensure_h_scroll()

    # Fast path: minimal-write update instead of full field redraw.
    # Eligible if no word wrap, no scroll change, and the display row
    # count didn't change.
    fast_eligible = (
      not self.word_wrap
      and self.h_scroll == saved_h_scroll
      and self.scroll_offset == saved_scroll_offset
      and len(self.display_rows) == saved_display_rows_len
    )
    if fast_eligible:
      dri = self._display_row_for_cursor()
      if was_at_end or was_overwrite:
        # Single cell write: just put the new char at its position.
        sr, sc = self._cursor_to_screen()
        need_nowrap = (self.col_offset + self.width - 1 >= self.user.screen_width)
        if need_nowrap:
          ansi_wrap(self.user, False)
        await ansi_move(self.user, sr, sc - 1)
        ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
        await send(self.user, self.mask_char if self.mask_char else ch, drain=False)
        if need_nowrap:
          ansi_wrap(self.user, True)
      else:
        # Insert in middle: rewrite this line from the new char's column
        # onward, shifting the rest of the line right by one.
        await self._draw_line_tail(dri, self.cursor_col - 1)
      await self._position_cursor(drain=drain)
      return

    # Word-wrap fast path: redraw only display rows whose content actually
    # changed after the rewrap.
    if self.word_wrap and self.scroll_offset == saved_scroll_offset and old_snapshot is not None:
      await self._redraw_changed_rows(old_snapshot)
      await self._position_cursor(drain=drain)
      return

    await self._draw_visible()

  async def _handle_batch(self, chars):
    """Handle a batch of printable characters (e.g. from paste)."""
    if not chars:
      return
    batch_str = "".join(chars)
    line = self.lines[self.cursor_line]

    # Enforce max_length
    if self.max_length and not self.insert_mode:
      available = self.max_length - self._total_char_count()
      if available <= 0:
        return
      batch_str = batch_str[:available]

    if self.insert_mode:
      # Overwrite — replace len(batch_str) chars starting at cursor
      cur = line.text
      line.text = cur[:self.cursor_col] + batch_str + cur[self.cursor_col + len(batch_str):]
    else:
      line.insert_text(self.cursor_col, batch_str)

    self.cursor_col += len(batch_str)

    self._compute_display_rows()
    self._set_updown_col()
    self._ensure_cursor_visible()
    self._ensure_h_scroll()
    await self._draw_visible()

  # ---- Scroll helpers ----

  def _ensure_h_scroll(self):
    """Adjust horizontal scroll so cursor is visible (non-word-wrap mode)."""
    if self.word_wrap:
      self.h_scroll = 0
      return
    mw = self._margin_width(self.lines[self.cursor_line].level)
    usable = (self.width if self.no_cursor_margin else self.width - 1) - mw
    if usable <= 0:
      usable = 1
    # Cursor position relative to margin
    cpos = self.cursor_col
    if cpos < self.h_scroll:
      self.h_scroll = max(0, cpos - self.scroll_step)
      self.h_scroll = max(0, self.h_scroll)
    elif cpos > self.h_scroll + usable:
      self.h_scroll = cpos - usable
      # Snap to scroll_step, but don't scroll past cursor
      self.h_scroll = ((self.h_scroll + self.scroll_step - 1) // self.scroll_step) * self.scroll_step
      if self.h_scroll > cpos:
        self.h_scroll = max(0, cpos)

  async def _redraw_or_reposition(self):
    """After cursor movement, redraw if scrolled, otherwise just reposition.
    In wrap mode, uses cell-level diff so scroll only redraws changed cells."""
    old_offset = self.scroll_offset
    old_snapshot = self._snapshot_display_rows() if self.word_wrap else None
    self._ensure_cursor_visible()
    if self.scroll_offset != old_offset:
      if self.word_wrap and old_snapshot is not None:
        await self._redraw_changed_rows(old_snapshot)
        await self._position_cursor(drain=True)
      else:
        await self._draw_visible()
    else:
      await self._position_cursor(drain=True)
