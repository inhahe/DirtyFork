from copy import deepcopy
import re

from input_output import *
from config import get_config
from definitions import *

config = get_config()

contentre = re.compile(r"[^\n ]+| |\n")


def _get_margin_prefix(line, margin_char):
  """Return the margin prefix (e.g. '> ', '>> ', '>>> ') from a line, or ''."""
  prefix = ""
  i = 0
  while i < len(line) and line[i] == margin_char:
    prefix += margin_char
    i += 1
  if prefix and i < len(line) and line[i] == " ":
    prefix += " "
  return prefix


def _margin_depth(line, margin_char):
  """Return how many margin chars are at the start of a line."""
  count = 0
  for ch in line:
    if ch == margin_char:
      count += 1
    else:
      break
  return count


class InputFields:
  def __init__(self, user):
    self.fields = []
    self.user = user
    self._submit_button = null

  async def add_field(self, **kwargs):
    field = await InputField.create(parent=self, user=self.user, allow_edit=True, **kwargs)
    self.fields.append(field)
    return field

  async def add_submit_button(self, **kwargs):
    self._submit_button = await InputField.create(
      parent=self, user=self.user, allow_edit=False,
      conf=config.input_fields.submit, **kwargs
    )
    await self._submit_button.draw_outline(active=False)
    await self._submit_button.draw_field()
    return self._submit_button

  def _find_field_at(self, screen_row, screen_col):
    """Given a 1-based screen coordinate, return the index of the field that
    contains it, or submit if it's the submit button, or null if none."""
    for i, field in enumerate(self.fields):
      if field._contains_screen_pos(screen_row, screen_col):
        return i
    if self._submit_button and self._submit_button._contains_screen_pos(screen_row, screen_col):
      return submit
    return null

  async def run(self):
    current_index = 0
    last_index = null
    while True:
      if current_index == submit:
        current_field = self._submit_button
      else:
        current_field = self.fields[current_index]

      if current_index != last_index:
        await current_field.draw_outline(active=True)
        if last_index is not null:
          if last_index == submit:
            prev = self._submit_button
          else:
            prev = self.fields[last_index]
          await prev.draw_outline(active=False)

      r = await current_field.run()

      if r.key == click:
        # A click happened — find which field was clicked
        clicked = self._find_field_at(r.click_row, r.click_col)
        if clicked is not null:
          if clicked == submit:
            # Clicking the submit button submits
            return RetVals(
              key=cr,
              fields=[RetVals(content=f.get_text(), row=f.row, col=f.col) for f in self.fields]
            )
          else:
            current_index = clicked
            # Position the cursor within the clicked field at the click location
            clicked_field = self.fields[clicked]
            clicked_field._place_cursor_at_screen_pos(r.click_row, r.click_col)
        # If clicked outside all fields, ignore
      elif r.key in (cr, tab):
        if current_index == submit:
          # Submit was activated
          return RetVals(
            key=cr,
            fields=[RetVals(content=f.get_text(), row=f.row, col=f.col) for f in self.fields]
          )
        elif current_index == len(self.fields) - 1:
          if self._submit_button:
            current_index = submit
          else:
            current_index = 0
        else:
          current_index += 1
      elif r.key == left or r.key == up:
        if current_index == submit:
          current_index = len(self.fields) - 1
        elif current_index > 0:
          current_index -= 1
      elif r.key == right or r.key == down:
        if current_index == submit:
          current_index = 0
        elif current_index == len(self.fields) - 1:
          if self._submit_button:
            current_index = submit
          else:
            current_index = 0
        else:
          current_index += 1

      last_index = current_index


class InputField:
  def __init__(self):
    pass

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
                   margin_char=null):
    self = cls()
    self.user = user if user is not null else parent.user
    self.parent = parent

    # Screen position where the field content starts (1-based)
    self.row_offset = self.user.cur_row
    self.col_offset = self.user.cur_col

    # Cursor position within the visible area (0-based)
    self.row = 0
    self.col = 0

    # Scroll offsets into the virtual content (0-based)
    self.content_row_offset = 0
    self.content_col_offset = 0

    # Resolve config vs explicit parameters
    if conf is null:
      conf = config.input_fields.input_field

    def _color(val, default=white):
      if val and val in colors:
        return colors[val]
      if isinstance(val, int):
        return val
      return default

    # outline can be False/null (no outline) or a Config object (has outline with colors)
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

    self.height = height if height is not null else (conf.height or 1)
    self.width = width if width is not null else (conf.width or 40)
    self.height_from_end = conf.height_from_end if height_from_end is null else height_from_end
    self.width_from_end = conf.width_from_end if width_from_end is null else width_from_end

    if (not self.height or self.height is null) and self.height_from_end is not null:
      self.height = self.user.screen_height - self.row_offset + 1 - self.height_from_end
    if (not self.width or self.width is null) and self.width_from_end is not null:
      self.width = self.user.screen_width - self.col_offset + 1 - self.width_from_end

    self.max_length = max_length if max_length is not null else (conf.max_length or 1000)
    self.max_lines = conf.max_lines if max_lines is null else max_lines

    self.fg = _color(conf.content.fg, white) if fg is null else fg
    self.fg_br = (conf.content.fg_br or False) if fg_br is null else fg_br
    self.bg = _color(conf.content.bg, black) if bg is null else bg
    self.bg_br = (conf.content.bg_br or False) if bg_br is null else bg_br

    # Fill/blank character and colors - YAML has blank.char, blank.fg at same level as content
    self.fill = conf.blank.char if fill is null else fill
    self.fill = self.fill or " "
    if type(self.fill) is int:
      self.fill = chr(self.fill)

    self.fill_fg = _color(conf.blank.fg, white) if fill_fg is null else fill_fg
    self.fill_fg_br = (conf.blank.fg_br or False) if fill_fg_br is null else fill_fg_br
    self.fill_bg = _color(conf.blank.bg, black) if fill_bg is null else fill_bg
    self.fill_bg_br = (conf.blank.bg_br or False) if fill_bg_br is null else fill_bg_br

    self.word_wrap = (conf.word_wrap or False) if word_wrap is null else word_wrap
    self.insert_mode = (conf.insert_mode or False) if insert_mode is null else insert_mode
    self.allow_edit = (conf.allow_edit if conf.allow_edit is not null else True) if allow_edit is null else allow_edit
    self.margin_char = ">" if margin_char is null else margin_char

    # Tokenize initial content
    self.words = [Estr(w) for w in contentre.findall(content)] if content else []

    # content is a list of display lines (strings), word_indices is [row][col]
    self.content = []
    self.word_indices = []
    self.content_length = 0  # total character count

    # The column the cursor tries to maintain when moving up/down
    self.updown_end_col = 0

    # Compute initial layout
    self._rebuild_all()

    # Draw outline and field
    if self.outline:
      await self.draw_outline(active=bool(parent is null))

    if self.col_offset + self.width - 1 == self.user.screen_width:
      ansi_wrap(self.user, False)

    await self.draw_field()

    if parent is null:
      return await self.run()

    return self

  def get_text(self):
    """Reconstruct the text content from the words list."""
    return "".join(str(w) for w in self.words)

  def _contains_screen_pos(self, screen_row, screen_col):
    """Check if a 1-based screen position falls within this field's area (including outline)."""
    top = self.row_offset - (1 if self.outline else 0)
    bottom = self.row_offset + self.height - 1 + (1 if self.outline else 0)
    left_edge = self.col_offset - (1 if self.outline else 0)
    right_edge = self.col_offset + self.width - 1 + (1 if self.outline else 0)
    return top <= screen_row <= bottom and left_edge <= screen_col <= right_edge

  def _place_cursor_at_screen_pos(self, screen_row, screen_col):
    """Move the cursor to the position corresponding to a 1-based screen click.
    Clamps to valid content positions."""
    # Convert screen coords to field-relative 0-based coords
    rel_row = screen_row - self.row_offset
    rel_col = screen_col - self.col_offset
    # Clamp to visible area
    rel_row = max(0, min(rel_row, self.height - 1))
    rel_col = max(0, min(rel_col, self.width - 1))
    # Convert to content coords
    ar = self.content_row_offset + rel_row
    ac = self.content_col_offset + rel_col
    # Clamp to actual content
    if ar >= self._total_content_lines():
      ar = max(0, self._total_content_lines() - 1)
    line_len = self._content_line_length(ar)
    if ac > line_len:
      ac = line_len
    # Update cursor
    self.row = ar - self.content_row_offset
    self.col = ac - self.content_col_offset
    self.updown_end_col = self.col

  # ---- Layout computation ----

  def _rebuild_all(self):
    """Rebuild content and word_indices from self.words."""
    if self.word_wrap:
      self._compute_wrap(0)
    else:
      self._compute_nowrap(0)

  def _ensure_content_rows(self, needed_rows):
    """Ensure content and word_indices have at least needed_rows rows."""
    while len(self.content) < needed_rows:
      self.content.append("")
    while len(self.word_indices) < needed_rows:
      self.word_indices.append([invalid] * self.width)

  def _compute_wrap(self, starting_word_index=0):
    """Compute word wrap layout starting from starting_word_index.
    Sets .row, .col, .end_row, .end_col on each word token.
    Populates self.content (list of display-line strings) and
    self.word_indices (2D array of Eint(token_index, index_into_word=N)).
    """
    if starting_word_index == 0:
      cur_row = 0
      cur_col = 0
      self.content = [""]
      self.word_indices = [[invalid] * self.width]
      self.content_length = 0
    else:
      prev = self.words[starting_word_index - 1]
      cur_row = prev.end_row
      cur_col = prev.end_col + 1
      # Trim content/word_indices from the starting position
      self._ensure_content_rows(cur_row + 1)
      self.content[cur_row] = self.content[cur_row][:cur_col]
      for c in range(cur_col, self.width):
        if cur_row < len(self.word_indices):
          self.word_indices[cur_row][c] = invalid
      # Recalculate content_length from words before starting_word_index
      self.content_length = 0
      for idx in range(starting_word_index):
        w = self.words[idx]
        if str(w) != "\n":
          self.content_length += len(w)
        else:
          self.content_length += 1

    # Determine margin for the current line (for reply quoting)
    margin_width = 0
    if cur_row < len(self.content):
      margin_width = len(_get_margin_prefix(self.content[cur_row], self.margin_char))

    usable_width = self.width - 1  # text can't reach the rightmost column

    for idx in range(starting_word_index, len(self.words)):
      word = self.words[idx]
      wstr = str(word)
      wlen = len(wstr)

      if wstr == "\n":
        # Newline token
        word.row = cur_row
        word.col = cur_col
        word.end_row = cur_row
        word.end_col = cur_col - 1

        # Mark cursor-after position
        if cur_col < self.width:
          self._ensure_content_rows(cur_row + 1)
          self.word_indices[cur_row][cur_col] = Eint(idx, index_into_word=after)

        # Fill rest of line with invalid
        for c in range(cur_col + 1, self.width):
          if cur_row < len(self.word_indices):
            self.word_indices[cur_row][c] = invalid

        cur_row += 1
        cur_col = 0
        self._ensure_content_rows(cur_row + 1)
        if cur_row >= len(self.word_indices):
          self.word_indices.append([invalid] * self.width)
        self.content[cur_row] = "" if cur_row >= len(self.content) else ""

        # Check if next words form a margin prefix
        margin_width = 0
        # Look ahead to see if the next content on this new line starts with margin chars
        remaining = "".join(str(self.words[j]) for j in range(idx + 1, min(idx + 20, len(self.words))))
        margin_width = len(_get_margin_prefix(remaining, self.margin_char))

        self.content_length += 1
        continue

      if wstr == " ":
        # Space token
        if cur_col >= usable_width:
          # Space at wrap boundary - don't print it, just move to next line
          word.row = cur_row
          word.col = cur_col
          word.end_row = cur_row
          word.end_col = cur_col - 1

          cur_row += 1
          cur_col = margin_width  # respect margin on wrapped lines
          self._ensure_content_rows(cur_row + 1)
          if cur_row >= len(self.word_indices):
            self.word_indices.append([invalid] * self.width)
          if cur_row >= len(self.content):
            self.content.append("")
          # Add margin prefix to wrapped line
          if margin_width > 0 and len(self.content[cur_row]) < margin_width:
            prefix = self.content[cur_row - 1][:margin_width] if cur_row > 0 and len(self.content[cur_row - 1]) >= margin_width else ""
            if not prefix:
              prefix = (self.margin_char * (margin_width - 1) + " ")[:margin_width]
            self.content[cur_row] = prefix
        else:
          word.row = cur_row
          word.col = cur_col
          word.end_row = cur_row
          word.end_col = cur_col

          self._ensure_content_rows(cur_row + 1)
          if cur_row >= len(self.word_indices):
            self.word_indices.append([invalid] * self.width)
          self.word_indices[cur_row][cur_col] = Eint(idx, index_into_word=0)
          self.content[cur_row] = self.content[cur_row][:cur_col] + " "
          cur_col += 1

        self.content_length += 1
        continue

      # Regular word token
      if cur_col + wlen <= usable_width:
        # Word fits on current line
        word.row = cur_row
        word.col = cur_col
        word.end_row = cur_row
        word.end_col = cur_col + wlen - 1

        self._ensure_content_rows(cur_row + 1)
        if cur_row >= len(self.word_indices):
          self.word_indices.append([invalid] * self.width)
        self.content[cur_row] = self.content[cur_row][:cur_col] + wstr
        for ci in range(wlen):
          self.word_indices[cur_row][cur_col + ci] = Eint(idx, index_into_word=ci)
        cur_col += wlen

      elif cur_col > margin_width and wlen <= usable_width - margin_width:
        # Word doesn't fit here but would fit on the next line - wrap it
        # Mark after position on current line
        if cur_col < self.width:
          self.word_indices[cur_row][cur_col] = Eint(idx, index_into_word=after)
        for c in range(cur_col + 1, self.width):
          if cur_row < len(self.word_indices):
            self.word_indices[cur_row][c] = invalid

        cur_row += 1
        cur_col = margin_width
        self._ensure_content_rows(cur_row + 1)
        if cur_row >= len(self.word_indices):
          self.word_indices.append([invalid] * self.width)
        if cur_row >= len(self.content):
          self.content.append("")

        # Add margin prefix to wrapped line
        if margin_width > 0:
          prefix_src = ""
          for prev_r in range(cur_row - 1, -1, -1):
            if len(self.content[prev_r]) >= margin_width:
              prefix_src = self.content[prev_r][:margin_width]
              break
          if not prefix_src:
            prefix_src = (self.margin_char * (margin_width - 1) + " ")[:margin_width]
          self.content[cur_row] = prefix_src

        word.row = cur_row
        word.col = cur_col
        word.end_row = cur_row
        word.end_col = cur_col + wlen - 1

        self.content[cur_row] = self.content[cur_row][:cur_col] + wstr
        for ci in range(wlen):
          self.word_indices[cur_row][cur_col + ci] = Eint(idx, index_into_word=ci)
        cur_col += wlen

      else:
        # Word is too long - it must span multiple lines
        word.row = cur_row
        word.col = cur_col

        wi = 0
        while wi < wlen:
          if cur_col >= usable_width:
            cur_row += 1
            cur_col = margin_width
            self._ensure_content_rows(cur_row + 1)
            if cur_row >= len(self.word_indices):
              self.word_indices.append([invalid] * self.width)
            if cur_row >= len(self.content):
              self.content.append("")
            if margin_width > 0:
              prefix_src = ""
              for prev_r in range(cur_row - 1, -1, -1):
                if len(self.content[prev_r]) >= margin_width:
                  prefix_src = self.content[prev_r][:margin_width]
                  break
              if not prefix_src:
                prefix_src = (self.margin_char * (margin_width - 1) + " ")[:margin_width]
              self.content[cur_row] = prefix_src

          self._ensure_content_rows(cur_row + 1)
          if cur_row >= len(self.word_indices):
            self.word_indices.append([invalid] * self.width)
          self.word_indices[cur_row][cur_col] = Eint(idx, index_into_word=wi)
          self.content[cur_row] = self.content[cur_row][:cur_col] + wstr[wi]
          cur_col += 1
          wi += 1

        word.end_row = cur_row
        word.end_col = cur_col - 1

      self.content_length += wlen

    # Mark the position just past the last token
    self._ensure_content_rows(cur_row + 1)
    if cur_row >= len(self.word_indices):
      self.word_indices.append([invalid] * self.width)
    if cur_col < self.width:
      if len(self.words) > 0:
        self.word_indices[cur_row][cur_col] = Eint(len(self.words) - 1, index_into_word=after)
      else:
        self.word_indices[cur_row][cur_col] = Eint(0, index_into_word=after)

    # Fill remaining with invalid
    for c in range(cur_col + 1, self.width):
      self.word_indices[cur_row][c] = invalid
    for r in range(cur_row + 1, len(self.word_indices)):
      for c in range(self.width):
        self.word_indices[r][c] = invalid

    # Trim extra content rows
    self.content = self.content[:cur_row + 1]

  def _compute_nowrap(self, starting_word_index=0):
    """Compute layout without word wrap. Each explicit newline starts a new line.
    Words and spaces flow continuously on the same line until a newline.
    """
    if starting_word_index == 0:
      cur_row = 0
      cur_col = 0
      self.content = [""]
      self.word_indices = [[invalid] * self.width]
      self.content_length = 0
    else:
      prev = self.words[starting_word_index - 1]
      cur_row = prev.end_row
      cur_col = prev.end_col + 1
      self._ensure_content_rows(cur_row + 1)
      self.content[cur_row] = self.content[cur_row][:cur_col]
      self.content_length = 0
      for idx in range(starting_word_index):
        w = self.words[idx]
        if str(w) != "\n":
          self.content_length += len(w)
        else:
          self.content_length += 1

    for idx in range(starting_word_index, len(self.words)):
      word = self.words[idx]
      wstr = str(word)
      wlen = len(wstr)

      if wstr == "\n":
        word.row = cur_row
        word.col = cur_col
        word.end_row = cur_row
        word.end_col = cur_col - 1

        # Ensure word_indices row exists and is wide enough
        self._ensure_wi_col(cur_row, cur_col)
        self.word_indices[cur_row][cur_col] = Eint(idx, index_into_word=after)

        cur_row += 1
        cur_col = 0
        self._ensure_content_rows(cur_row + 1)
        if cur_row >= len(self.word_indices):
          self.word_indices.append([invalid] * self.width)
        self.content[cur_row] = ""
        self.content_length += 1
        continue

      word.row = cur_row
      word.col = cur_col
      word.end_row = cur_row
      word.end_col = cur_col + wlen - 1

      self._ensure_content_rows(cur_row + 1)
      self.content[cur_row] = self.content[cur_row][:cur_col] + wstr

      for ci in range(wlen):
        self._ensure_wi_col(cur_row, cur_col + ci)
        self.word_indices[cur_row][cur_col + ci] = Eint(idx, index_into_word=ci)

      cur_col += wlen
      self.content_length += wlen

    # Mark after position
    self._ensure_content_rows(cur_row + 1)
    self._ensure_wi_col(cur_row, cur_col)
    if len(self.words) > 0:
      self.word_indices[cur_row][cur_col] = Eint(len(self.words) - 1, index_into_word=after)

    self.content = self.content[:cur_row + 1]

  def _ensure_wi_col(self, row, col):
    """Ensure word_indices[row] exists and has at least col+1 entries."""
    while row >= len(self.word_indices):
      self.word_indices.append([invalid] * self.width)
    while col >= len(self.word_indices[row]):
      self.word_indices[row].append(invalid)

  # ---- Cursor position to word index ----

  def _cur_word_index(self):
    """Get the word index at the current cursor position (adjusted for scroll)."""
    ar = self.content_row_offset + self.row
    ac = self.content_col_offset + self.col
    if ar < len(self.word_indices) and ac < len(self.word_indices[ar]):
      return self.word_indices[ar][ac]
    return invalid

  def _adjusted_row(self):
    return self.content_row_offset + self.row

  def _adjusted_col(self):
    return self.content_col_offset + self.col

  # ---- Drawing ----

  async def draw_outline(self, active=False):
    if not self.outline:
      return
    if active:
      ofg = self.outline_active_fg
      ofg_br = self.outline_active_fg_br
      obg = self.outline_active_bg
      obg_br = self.outline_active_bg_br
    else:
      ofg = self.outline_fg
      ofg_br = self.outline_fg_br
      obg = self.outline_bg
      obg_br = self.outline_bg_br

    # Use Unicode box-drawing characters
    if self.outline_double:
      tl, horiz, tr, vert, bl, br_char = "\u2554", "\u2550", "\u2557", "\u2551", "\u255A", "\u255D"
    else:
      tl, horiz, tr, vert, bl, br_char = "\u250C", "\u2500", "\u2510", "\u2502", "\u2514", "\u2518"

    # row_offset and col_offset already account for the outline offset (+1 each)
    # so the outline is drawn at row_offset-1, col_offset-1
    outline_row = self.row_offset - 1
    outline_col = self.col_offset - 1

    need_nowrap = (outline_col - 1 + self.width + 2) >= self.user.screen_width
    if need_nowrap:
      ansi_wrap(self.user, False)

    ansi_color(self.user, fg=ofg, fg_br=ofg_br, bg=obg, bg_br=obg_br)

    # Top border
    await ansi_move(self.user, row=outline_row, col=outline_col, drain=False)
    await send(self.user, tl + horiz * self.width + tr, drain=False)

    # Side borders
    for r in range(self.height):
      await ansi_move(self.user, row=outline_row + 1 + r, col=outline_col, drain=False)
      await send(self.user, vert, drain=False)
      await ansi_move(self.user, row=outline_row + 1 + r, col=outline_col + self.width + 1, drain=False)
      await send(self.user, vert, drain=False)

    # Bottom border
    await ansi_move(self.user, row=outline_row + self.height + 1, col=outline_col, drain=False)
    await send(self.user, bl + horiz * self.width + br_char, drain=False)

    # Restore cursor position
    await ansi_move(self.user, row=self.row_offset + self.row, col=self.col_offset + self.col, drain=True)

    if need_nowrap:
      ansi_wrap(self.user, True)

  async def draw_field(self, start_at=top, end_row=null):
    """Redraw visible portion of the field.
    start_at: top (redraw all), before_cur (from word before cursor), cur (from cursor pos)
    end_row: content row to stop at (inclusive), null means bottom of visible area
    """
    if start_at == top:
      start_row = 0
      start_col = 0
    elif start_at == before_cur:
      i = self._cur_word_index()
      if i != invalid and i > 0:
        prev_word = self.words[i - 1]
        start_row = prev_word.row - self.content_row_offset
        start_col = prev_word.col - self.content_col_offset
      else:
        start_row = self.row
        start_col = 0
      start_row = max(0, start_row)
      start_col = max(0, start_col)
    elif start_at == cur:
      start_row = self.row
      start_col = self.col
    else:
      start_row = 0
      start_col = 0

    if end_row is null:
      vis_end_row = self.height - 1
    else:
      vis_end_row = min(end_row - self.content_row_offset, self.height - 1)

    vis_end_row = max(vis_end_row, start_row)

    need_nowrap = (self.col_offset + self.width - 1 >= self.user.screen_width)
    if need_nowrap:
      ansi_wrap(self.user, False)

    for vr in range(start_row, vis_end_row + 1):
      content_r = self.content_row_offset + vr
      sc = start_col if vr == start_row else 0

      await ansi_move(self.user, row=self.row_offset + vr, col=self.col_offset + sc, drain=False)

      if content_r < len(self.content):
        line = self.content[content_r]
        # Strip trailing \r from display
        display_line = line.replace("\r", "").replace("\n", "")
        visible_start = self.content_col_offset + sc
        visible_end = self.content_col_offset + self.width - 1  # text can't reach rightmost col
        text_segment = display_line[visible_start:visible_end]
      else:
        text_segment = ""

      if text_segment:
        ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
        await send(self.user, text_segment, drain=False)

      # Fill remainder with fill character
      fill_count = (self.width - 1) - sc - len(text_segment)
      if fill_count > 0:
        ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br, bg=self.fill_bg, bg_br=self.fill_bg_br)
        await send(self.user, self.fill * fill_count, drain=False)

      # The rightmost column itself (width-1 from start) - fill it too
      if sc + len(text_segment) + fill_count < self.width:
        remaining = self.width - sc - len(text_segment) - max(fill_count, 0)
        if remaining > 0:
          ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br, bg=self.fill_bg, bg_br=self.fill_bg_br)
          await send(self.user, self.fill * remaining, drain=False)

    # Restore cursor
    await ansi_move(self.user, row=self.row_offset + self.row, col=self.col_offset + self.col, drain=False)

    if self.insert_mode:
      await self.show_insert_cursor(drain=True)
    else:
      await send(self.user, "", drain=True)

  async def show_insert_cursor(self, drain=True):
    """Show the insert-mode cursor: the character at the cursor position with inverted colors."""
    ar = self._adjusted_row()
    ac = self._adjusted_col()

    if ar >= len(self.content) or ac >= len(self.content[ar].replace("\n", "").replace("\r", "")):
      # Past end of content on this line - show inverted fill character
      ansi_color(self.user, fg=self.fill_bg, fg_br=self.fill_bg_br, bg=self.fill_fg, bg_br=self.fill_fg_br)
      if self.col_offset + self.col + 1 >= self.user.screen_width:
        ansi_wrap(self.user, False)
      await send(self.user, self.fill, drain=False)
      await ansi_left(self.user, 1, drain=False)
      ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
      if drain:
        await send(self.user, "", drain=True)
    else:
      # Show the character under cursor with inverted colors
      ch = self.content[ar][ac]
      ansi_color(self.user, fg=self.bg, fg_br=self.bg_br, bg=self.fg, bg_br=self.fg_br)
      await send(self.user, ch, drain=False)
      await ansi_left(self.user, 1, drain=False)
      ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
      if drain:
        await send(self.user, "", drain=True)

  async def _hide_insert_cursor(self):
    """Restore normal display of the character at the current cursor position."""
    if not self.insert_mode:
      return
    ar = self._adjusted_row()
    ac = self._adjusted_col()
    if ar < len(self.content) and ac < len(self.content[ar].replace("\n", "").replace("\r", "")):
      ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
      await send(self.user, self.content[ar][ac], drain=False)
      await ansi_left(self.user, 1, drain=False)
    else:
      ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br, bg=self.fill_bg, bg_br=self.fill_bg_br)
      await send(self.user, self.fill, drain=False)
      await ansi_left(self.user, 1, drain=False)

  async def scroll_down(self):
    """Scroll the visible area down by one line."""
    if self.col_offset == 1 and self.width == self.user.screen_width:
      # Can use terminal scroll region
      if self.row_offset > 1 or self.height < self.user.screen_height:
        await ansi_set_region(self.user, self.row_offset, self.row_offset + self.height - 1, drain=False)
        await ansi_set_region_strict(self.user, True, drain=False)
      await ansi_move(self.user, row=self.row_offset + self.height - 1, col=self.col_offset, drain=False)
      await send(self.user, cr + lf, drain=False)
      # Draw the new bottom line
      content_r = self.content_row_offset + self.height - 1
      if content_r < len(self.content):
        line = self.content[content_r].replace("\n", "").replace("\r", "")
        vis = line[self.content_col_offset:self.content_col_offset + self.width - 1]
        ansi_color(self.user, fg=self.fg, fg_br=self.fg_br, bg=self.bg, bg_br=self.bg_br)
        await send(self.user, vis, drain=False)
        fill_count = self.width - 1 - len(vis)
        if fill_count > 0:
          ansi_color(self.user, fg=self.fill_fg, fg_br=self.fill_fg_br, bg=self.fill_bg, bg_br=self.fill_bg_br)
          await send(self.user, self.fill * fill_count, drain=False)
      await ansi_set_region(self.user, drain=False)
      await ansi_set_region_strict(self.user, False, drain=False)
      await ansi_move(self.user, row=self.row_offset + self.row, col=self.col_offset + self.col, drain=True)
    else:
      await self.draw_field(start_at=top)

  async def scroll_up(self):
    """Scroll the visible area up by one line."""
    # For simplicity, just redraw
    await self.draw_field(start_at=top)

  # ---- Word manipulation helpers ----

  def _insert_text_at_cursor(self, text):
    """Insert text (a single character or string) into words at the current cursor position.
    Returns the word index where the insertion happened.
    """
    ar = self._adjusted_row()
    ac = self._adjusted_col()
    i = self.word_indices[ar][ac]

    if i == invalid:
      # At end of content, append
      self.words.append(Estr(text))
      return len(self.words) - 1

    iiw = i.index_into_word

    if iiw == after:
      # Just past the end of the token - insert after it
      self.words.insert(int(i) + 1, Estr(text))
      return int(i) + 1
    elif iiw == 0:
      # At start of a token
      wstr = str(self.words[int(i)])
      if wstr == "\n":
        # Insert before newline
        self.words.insert(int(i), Estr(text))
        return int(i)
      elif text == " " or wstr == " ":
        self.words.insert(int(i), Estr(text))
        return int(i)
      else:
        # Prepend to existing word (if both are non-space, non-newline)
        self.words[int(i)] = Estr(text + wstr)
        return int(i)
    else:
      # In the middle of a token
      wstr = str(self.words[int(i)])
      before = wstr[:iiw]
      after_part = wstr[iiw:]
      if text == " " or text == "\n":
        # Split the word
        self.words[int(i)] = Estr(before)
        self.words.insert(int(i) + 1, Estr(text))
        self.words.insert(int(i) + 2, Estr(after_part))
        return int(i) + 1
      else:
        # Insert character into word
        self.words[int(i)] = Estr(before + text + after_part)
        return int(i)

  def _replace_char_at_cursor(self, ch):
    """Replace the character at the cursor with ch (for insert/overwrite mode)."""
    ar = self._adjusted_row()
    ac = self._adjusted_col()
    i = self.word_indices[ar][ac]

    if i == invalid:
      return

    iiw = i.index_into_word

    if iiw == after:
      # Past end - just insert
      self._insert_text_at_cursor(ch)
      return

    wstr = str(self.words[int(i)])
    if wstr == "\n":
      # Don't replace a newline with a character in overwrite mode; insert instead
      self._insert_text_at_cursor(ch)
      return

    self.words[int(i)] = Estr(wstr[:iiw] + ch + wstr[iiw + 1:])

  def _delete_at_cursor(self):
    """Delete the character at the current cursor position. Returns True if a deletion occurred."""
    ar = self._adjusted_row()
    ac = self._adjusted_col()

    if ar >= len(self.word_indices):
      return False
    if ac >= len(self.word_indices[ar]):
      return False

    i = self.word_indices[ar][ac]

    if i == invalid:
      return False

    iiw = i.index_into_word

    if iiw == after:
      # Just past the end of a token. Delete the next character (first char of next token).
      next_idx = int(i) + 1
      while next_idx < len(self.words) and str(self.words[next_idx]) == "":
        next_idx += 1
      if next_idx >= len(self.words):
        return False
      nw = str(self.words[next_idx])
      if nw == "\n":
        del self.words[next_idx]
      elif len(nw) == 1:
        del self.words[next_idx]
        # If deleting brought two word tokens together, merge them
        if next_idx > 0 and next_idx < len(self.words):
          prev = str(self.words[next_idx - 1])
          nxt = str(self.words[next_idx]) if next_idx < len(self.words) else ""
          if prev and nxt and prev not in (" ", "\n") and nxt not in (" ", "\n"):
            self.words[next_idx - 1] = Estr(prev + nxt)
            del self.words[next_idx]
      else:
        self.words[next_idx] = Estr(nw[1:])
      return True

    wstr = str(self.words[int(i)])

    if wstr == "\n":
      del self.words[int(i)]
      # Merge adjacent non-space tokens if needed
      if int(i) > 0 and int(i) < len(self.words):
        prev = str(self.words[int(i) - 1])
        nxt = str(self.words[int(i)])
        if prev not in (" ", "\n") and nxt not in (" ", "\n"):
          self.words[int(i) - 1] = Estr(prev + nxt)
          del self.words[int(i)]
      return True

    if len(wstr) == 1:
      del self.words[int(i)]
      # Merge adjacent non-space tokens if deletion brought them together
      if int(i) > 0 and int(i) < len(self.words):
        prev = str(self.words[int(i) - 1])
        nxt = str(self.words[int(i)])
        if prev not in (" ", "\n") and nxt not in (" ", "\n"):
          self.words[int(i) - 1] = Estr(prev + nxt)
          del self.words[int(i)]
      return True

    self.words[int(i)] = Estr(wstr[:iiw] + wstr[iiw + 1:])
    return True

  def _content_line_length(self, content_row):
    """Return the display length of a content row (excluding newline/cr)."""
    if content_row < len(self.content):
      return len(self.content[content_row].replace("\n", "").replace("\r", ""))
    return 0

  def _total_content_lines(self):
    return len(self.content)

  def _cursor_at_end(self):
    """Check if cursor is at the very end of all content."""
    ar = self._adjusted_row()
    ac = self._adjusted_col()
    i = self.word_indices[ar][ac] if ar < len(self.word_indices) and ac < len(self.word_indices[ar]) else invalid
    if i == invalid:
      return True
    if i.index_into_word == after and int(i) == len(self.words) - 1:
      return True
    return False

  # ---- Margin / reply handling ----

  def _get_current_margin_prefix(self):
    """Get the margin prefix for the content line at the cursor."""
    ar = self._adjusted_row()
    if ar < len(self.content):
      return _get_margin_prefix(self.content[ar], self.margin_char)
    return ""

  # ---- Main input loop ----

  async def run(self):
    while True:
      key = await get_input_key(self.user)

      if key == cr:
        if self.allow_edit:
          if self.height == 1:
            return RetVals(key=cr, content=self.get_text(), row=self.row, col=self.col,
                           insert_mode=self.insert_mode)

          if self.max_length and self.content_length >= self.max_length:
            continue

          if self.max_lines and self._total_content_lines() >= self.max_lines and not self.word_wrap:
            continue

          # Determine margin prefix to carry to the new line
          margin_prefix = self._get_current_margin_prefix()

          # Insert newline into words
          old_words = deepcopy(self.words) if (self.word_wrap and self.max_lines and
              self._total_content_lines() >= self.max_lines - 1) else null

          ar = self._adjusted_row()
          ac = self._adjusted_col()
          i = self.word_indices[ar][ac]

          if i == invalid or (len(self.words) == 0):
            self.words.append(Estr("\n"))
          elif i.index_into_word == after:
            self.words.insert(int(i) + 1, Estr("\n"))
            # If there's a margin to carry, insert the margin prefix tokens after the newline
            if margin_prefix:
              self.words.insert(int(i) + 2, Estr(margin_prefix))
          elif i.index_into_word == 0:
            idx = int(i)
            self.words.insert(idx, Estr("\n"))
            if margin_prefix:
              self.words.insert(idx + 1, Estr(margin_prefix))
          else:
            wstr = str(self.words[int(i)])
            before = wstr[:i.index_into_word]
            after_part = wstr[i.index_into_word:]
            self.words[int(i)] = Estr(before)
            insert_pos = int(i) + 1
            self.words.insert(insert_pos, Estr("\n"))
            insert_pos += 1
            if margin_prefix:
              self.words.insert(insert_pos, Estr(margin_prefix))
              insert_pos += 1
            self.words.insert(insert_pos, Estr(after_part))

          # Recompute layout
          self._rebuild_all()

          # Check max_lines constraint (for word wrap, adding a newline might cause reflow)
          if self.max_lines and self._total_content_lines() > self.max_lines:
            if old_words is not null:
              self.words = old_words
              self._rebuild_all()
              continue
            else:
              # Undo - this shouldn't normally happen in non-wrap mode since we checked above
              continue

          self.content_length += 1

          # Move cursor to next line, at column after margin prefix
          new_col = len(margin_prefix)

          if self.row + 1 >= self.height:
            self.content_row_offset += 1
            self.col = new_col
            self.content_col_offset = 0
            await self.scroll_down()
          else:
            self.row += 1
            self.col = new_col
            self.content_col_offset = 0
            await self.draw_field(start_at=cur)

          self.updown_end_col = self.col

        else:
          # Not editable - treat enter as submit
          return RetVals(key=cr, content=self.get_text(), row=self.row, col=self.col,
                         insert_mode=self.insert_mode)

      elif key == tab:
        if self.parent:
          return RetVals(key=tab, content=self.get_text(), row=self.row, col=self.col,
                         insert_mode=self.insert_mode)

      elif key == left:
        r = await self._move_left(drain=True)
        if r and r.escape:
          return RetVals(key=left, content=self.get_text(), row=self.row, col=self.col,
                         insert_mode=self.insert_mode)

      elif key == right:
        r = await self._move_right(drain=True)
        if r and r.escape:
          return RetVals(key=right, content=self.get_text(), row=self.row, col=self.col,
                         insert_mode=self.insert_mode)

      elif key == up:
        r = await self._move_up(drain=True)
        if r and r.escape:
          return RetVals(key=up, content=self.get_text(), row=self.row, col=self.col,
                         insert_mode=self.insert_mode)

      elif key == down:
        r = await self._move_down(drain=True)
        if r and r.escape:
          return RetVals(key=down, content=self.get_text(), row=self.row, col=self.col,
                         insert_mode=self.insert_mode)

      elif key == home:
        if self.insert_mode:
          await self._hide_insert_cursor()
        self.col = 0
        if self.content_col_offset != 0:
          self.content_col_offset = 0
          await self.draw_field(start_at=top)
        else:
          await ansi_move(self.user, row=self.row_offset + self.row, col=self.col_offset, drain=False)
          if self.insert_mode:
            await self.show_insert_cursor(drain=True)
          else:
            await send(self.user, "", drain=True)
        self.updown_end_col = self.col

      elif key == end:
        if self.insert_mode:
          await self._hide_insert_cursor()
        ar = self._adjusted_row()
        line_len = self._content_line_length(ar)
        # Cursor goes to the position just past the last character, but not past width-1
        target_col = min(line_len, self.width - 1)
        if not self.word_wrap and line_len > self.width - 1 + self.content_col_offset:
          # Need to scroll
          self.content_col_offset = line_len - (self.width - 2)
          self.col = self.width - 2
          await self.draw_field(start_at=top)
        else:
          target_content_col = line_len
          if target_content_col - self.content_col_offset >= self.width:
            self.content_col_offset = target_content_col - (self.width - 2)
            self.col = self.width - 2
            await self.draw_field(start_at=top)
          else:
            self.col = target_content_col - self.content_col_offset
            await ansi_move(self.user, row=self.row_offset + self.row,
                            col=self.col_offset + self.col, drain=False)
            if self.insert_mode:
              await self.show_insert_cursor(drain=True)
            else:
              await send(self.user, "", drain=True)
        self.updown_end_col = self.col

      elif key == delete:
        if self.allow_edit:
          await self._do_delete(drain=True)

      elif key == back:
        if self.allow_edit:
          await self._do_backspace(drain=True)

      elif key == insert:
        self.insert_mode = not self.insert_mode
        if self.insert_mode:
          # If cursor is at rightmost column (width-1) and there's text under it,
          # move one left so there's room to show the insert cursor
          if self.col >= self.width - 1:
            self.col = self.width - 2
          await self.show_insert_cursor(drain=True)
        else:
          # Restore normal display
          await self._hide_insert_cursor()
          await send(self.user, "", drain=True)

      elif key == click:
        # Mouse click. If inside this field, move cursor there.
        # If outside (and we have a parent), return to the container so it can route.
        click_row = key.row  # 1-based screen coords from keyboard_codes
        click_col = key.col
        if self._contains_screen_pos(click_row, click_col):
          # Click is inside this field — move cursor to that position
          if self.insert_mode:
            await self._hide_insert_cursor()
          self._place_cursor_at_screen_pos(click_row, click_col)
          await ansi_move(self.user, row=self.row_offset + self.row,
                          col=self.col_offset + self.col, drain=False)
          if self.insert_mode:
            await self.show_insert_cursor(drain=True)
          else:
            await send(self.user, "", drain=True)
        elif self.parent:
          # Click outside this field — return to container with click info
          return RetVals(key=click, click_row=click_row, click_col=click_col,
                         content=self.get_text(), row=self.row, col=self.col,
                         insert_mode=self.insert_mode)

      elif isinstance(key, str) and len(key) == 1 and ord(key) >= 32:
        if self.allow_edit:
          await self._do_char(key, drain=True)

  # ---- Movement helpers ----

  async def _move_left(self, drain=True):
    ar = self._adjusted_row()
    ac = self._adjusted_col()

    if ar == 0 and ac == 0:
      if self.parent:
        return RetVals(escape=True)
      return RetVals(escape=False)

    if self.insert_mode:
      await self._hide_insert_cursor()

    if ac == 0:
      # Move to end of previous line
      prev_row = ar - 1
      prev_len = self._content_line_length(prev_row)
      target_col = prev_len  # just past end of content on prev line

      if self.row == 0:
        self.content_row_offset -= 1
        self.col = min(target_col, self.width - 1)
        if target_col > self.width - 1:
          self.content_col_offset = target_col - self.col
        else:
          self.content_col_offset = 0
        await self.draw_field(start_at=top)
      else:
        self.row -= 1
        self.col = min(target_col, self.width - 1)
        if target_col > self.width - 1:
          self.content_col_offset = target_col - self.col
          await self.draw_field(start_at=top)
        else:
          self.content_col_offset = 0
          await ansi_move(self.user, row=self.row_offset + self.row,
                          col=self.col_offset + self.col, drain=False)
          if self.insert_mode:
            await self.show_insert_cursor(drain=drain)
          elif drain:
            await send(self.user, "", drain=True)
    else:
      self.col -= 1
      if self.col < 0:
        # Need to scroll left
        self.content_col_offset = max(0, self.content_col_offset - 8)
        self.col = ac - 1 - self.content_col_offset
        self.col = max(0, self.col)
        await self.draw_field(start_at=top)
      else:
        await ansi_move(self.user, row=self.row_offset + self.row,
                        col=self.col_offset + self.col, drain=False)
        if self.insert_mode:
          await self.show_insert_cursor(drain=drain)
        elif drain:
          await send(self.user, "", drain=True)

    self.updown_end_col = self.col
    return RetVals(escape=False)

  async def _move_right(self, drain=True):
    ar = self._adjusted_row()
    ac = self._adjusted_col()

    # Check if we're at the very end of content
    if self._cursor_at_end():
      if self.parent:
        return RetVals(escape=True)
      return RetVals(escape=False)

    if self.insert_mode:
      await self._hide_insert_cursor()

    line_len = self._content_line_length(ar)

    if ac >= line_len:
      # Move to beginning of next line
      if ar + 1 >= self._total_content_lines():
        if self.parent:
          return RetVals(escape=True)
        return RetVals(escape=False)

      self.content_col_offset = 0
      self.col = 0

      if self.row + 1 >= self.height:
        self.content_row_offset += 1
        await self.draw_field(start_at=top)
      else:
        self.row += 1
        await ansi_move(self.user, row=self.row_offset + self.row,
                        col=self.col_offset + self.col, drain=False)
        if self.insert_mode:
          await self.show_insert_cursor(drain=drain)
        elif drain:
          await send(self.user, "", drain=True)
    else:
      self.col += 1
      if self.col >= self.width:
        if self.word_wrap:
          # In word wrap mode, moving right past the visible area goes to next line
          self.col = 0
          self.content_col_offset = 0
          if self.row + 1 >= self.height:
            self.content_row_offset += 1
            await self.draw_field(start_at=top)
          else:
            self.row += 1
            await ansi_move(self.user, row=self.row_offset + self.row,
                            col=self.col_offset + self.col, drain=False)
            if self.insert_mode:
              await self.show_insert_cursor(drain=drain)
            elif drain:
              await send(self.user, "", drain=True)
        else:
          # Horizontal scroll 8 chars at a time
          self.content_col_offset += 8
          self.col = ac + 1 - self.content_col_offset
          await self.draw_field(start_at=top)
      else:
        await ansi_move(self.user, row=self.row_offset + self.row,
                        col=self.col_offset + self.col, drain=False)
        if self.insert_mode:
          await self.show_insert_cursor(drain=drain)
        elif drain:
          await send(self.user, "", drain=True)

    self.updown_end_col = self.col
    return RetVals(escape=False)

  async def _move_up(self, drain=True):
    ar = self._adjusted_row()

    if ar == 0:
      if self.parent:
        return RetVals(escape=True)
      return RetVals(escape=False)

    if self.insert_mode:
      await self._hide_insert_cursor()

    prev_row = ar - 1
    prev_len = self._content_line_length(prev_row)
    target_ac = self.content_col_offset + self.updown_end_col
    if target_ac > prev_len:
      target_ac = prev_len

    do_redraw = False
    if self.row == 0:
      self.content_row_offset -= 1
      do_redraw = True
    else:
      self.row -= 1

    # Adjust horizontal scroll if needed
    if target_ac < self.content_col_offset:
      self.content_col_offset = 0
      do_redraw = True
    elif target_ac >= self.content_col_offset + self.width:
      self.content_col_offset = target_ac - (self.width - 2)
      do_redraw = True

    self.col = target_ac - self.content_col_offset

    if do_redraw:
      await self.draw_field(start_at=top)
    else:
      await ansi_move(self.user, row=self.row_offset + self.row,
                      col=self.col_offset + self.col, drain=False)
      if self.insert_mode:
        await self.show_insert_cursor(drain=drain)
      elif drain:
        await send(self.user, "", drain=True)

    return RetVals(escape=False)

  async def _move_down(self, drain=True):
    ar = self._adjusted_row()

    if ar + 1 >= self._total_content_lines():
      if self.parent:
        return RetVals(escape=True)
      return RetVals(escape=False)

    if self.insert_mode:
      await self._hide_insert_cursor()

    next_row = ar + 1
    next_len = self._content_line_length(next_row)
    target_ac = self.content_col_offset + self.updown_end_col
    if target_ac > next_len:
      target_ac = next_len

    do_redraw = False
    if self.row + 1 >= self.height:
      self.content_row_offset += 1
      do_redraw = True
    else:
      self.row += 1

    if target_ac < self.content_col_offset:
      self.content_col_offset = 0
      do_redraw = True
    elif target_ac >= self.content_col_offset + self.width:
      self.content_col_offset = target_ac - (self.width - 2)
      do_redraw = True

    self.col = target_ac - self.content_col_offset

    if do_redraw:
      await self.draw_field(start_at=top)
    else:
      await ansi_move(self.user, row=self.row_offset + self.row,
                      col=self.col_offset + self.col, drain=False)
      if self.insert_mode:
        await self.show_insert_cursor(drain=drain)
      elif drain:
        await send(self.user, "", drain=True)

    return RetVals(escape=False)

  # ---- Editing operations ----

  async def _do_delete(self, drain=True):
    """Delete the character at the cursor position."""
    if self._cursor_at_end():
      ar = self._adjusted_row()
      # Check if we're at end of a line but not end of content
      if ar + 1 < self._total_content_lines():
        pass  # Will be handled by _delete_at_cursor finding the newline
      else:
        return

    deleted = self._delete_at_cursor()
    if not deleted:
      return

    self.content_length -= 1
    self._rebuild_all()

    # Clamp cursor if needed
    ar = self._adjusted_row()
    if ar >= self._total_content_lines():
      if self._total_content_lines() > 0:
        ar = self._total_content_lines() - 1
        self.row = ar - self.content_row_offset
        if self.row < 0:
          self.content_row_offset = ar
          self.row = 0
      else:
        self.row = 0
        self.content_row_offset = 0

    await self.draw_field(start_at=cur if not self.word_wrap else top, end_row=null)

  async def _do_backspace(self, drain=True):
    """Delete the character before the cursor (backspace)."""
    ar = self._adjusted_row()
    ac = self._adjusted_col()

    if ar == 0 and ac == 0:
      return  # Nothing to delete

    # Move cursor left first
    if self.insert_mode:
      await self._hide_insert_cursor()

    if ac == 0:
      # Moving to end of previous line, then deleting the newline there
      prev_row = ar - 1
      prev_len = self._content_line_length(prev_row)

      if self.row == 0:
        self.content_row_offset -= 1
      else:
        self.row -= 1

      self.col = min(prev_len, self.width - 1)
      if prev_len > self.width - 1:
        self.content_col_offset = prev_len - self.col
      else:
        self.content_col_offset = 0
    else:
      self.col -= 1
      if self.col < 0:
        self.content_col_offset = max(0, self.content_col_offset - 8)
        self.col = max(0, ac - 1 - self.content_col_offset)

    # Now delete at the new cursor position
    deleted = self._delete_at_cursor()
    if deleted:
      self.content_length -= 1
    self._rebuild_all()

    # Clamp
    ar = self._adjusted_row()
    if ar >= self._total_content_lines() and self._total_content_lines() > 0:
      ar = self._total_content_lines() - 1
      self.row = ar - self.content_row_offset
      if self.row < 0:
        self.content_row_offset = ar
        self.row = 0
    line_len = self._content_line_length(self._adjusted_row())
    if self._adjusted_col() > line_len:
      self.col = line_len - self.content_col_offset
      if self.col < 0:
        self.content_col_offset = 0
        self.col = line_len

    self.updown_end_col = self.col
    await self.draw_field(start_at=top)

  async def _do_char(self, ch, drain=True):
    """Handle a printable character input."""
    if self.max_length and self.content_length >= self.max_length and not self.insert_mode:
      return

    if self.insert_mode:
      # Overwrite mode (insert key toggles this)
      ar = self._adjusted_row()
      ac = self._adjusted_col()
      i = self.word_indices[ar][ac] if ar < len(self.word_indices) and ac < len(self.word_indices[ar]) else invalid

      if i != invalid and i.index_into_word != after:
        wstr = str(self.words[int(i)])
        if wstr != "\n":
          # Overwrite character
          self._replace_char_at_cursor(ch)
        else:
          # At a newline, insert before it
          if self.max_length and self.content_length >= self.max_length:
            return
          self._insert_text_at_cursor(ch)
          self.content_length += 1
      else:
        # At end of content or after token - insert
        if self.max_length and self.content_length >= self.max_length:
          return
        self._insert_text_at_cursor(ch)
        self.content_length += 1
    else:
      # Normal insert (non-insert-mode, confusingly)
      if ch == " ":
        self._insert_text_at_cursor(" ")
      else:
        ar = self._adjusted_row()
        ac = self._adjusted_col()
        i = self.word_indices[ar][ac] if ar < len(self.word_indices) and ac < len(self.word_indices[ar]) else invalid

        if i == invalid or len(self.words) == 0:
          self.words.append(Estr(ch))
        elif i.index_into_word == after:
          wstr = str(self.words[int(i)])
          if wstr in (" ", "\n"):
            self.words.insert(int(i) + 1, Estr(ch))
          else:
            # Append to current word
            self.words[int(i)] = Estr(wstr + ch)
        elif i.index_into_word == 0:
          wstr = str(self.words[int(i)])
          if wstr in (" ", "\n"):
            self.words.insert(int(i), Estr(ch))
          else:
            self.words[int(i)] = Estr(ch + wstr)
        else:
          wstr = str(self.words[int(i)])
          self.words[int(i)] = Estr(wstr[:i.index_into_word] + ch + wstr[i.index_into_word:])

      self.content_length += 1

    # Recompute layout
    old_total = self._total_content_lines()
    self._rebuild_all()

    # Check max_lines
    if self.max_lines and self._total_content_lines() > self.max_lines:
      # Undo
      # This is a simplistic undo - in practice we'd need to save/restore words
      # For now, just rebuild
      pass

    # Advance cursor
    self.col += 1
    if self.col >= self.width - 1:
      if self.word_wrap:
        # Check if cursor wrapped to next line
        ar = self._adjusted_row()
        ac = self._adjusted_col()
        if ac < len(self.content[ar]) if ar < len(self.content) else False:
          pass  # Still on same line
        else:
          # Wrap to next line
          self.col = 0
          self.content_col_offset = 0
          if self.row + 1 >= self.height:
            self.content_row_offset += 1
          else:
            self.row += 1
      else:
        # Horizontal scroll
        self.content_col_offset += 8
        self.col = self._adjusted_col() - self.content_col_offset
        if self.col < 0:
          self.col = 0
    elif self.col >= self.width:
      if self.word_wrap:
        self.col = 0
        self.content_col_offset = 0
        if self.row + 1 >= self.height:
          self.content_row_offset += 1
        else:
          self.row += 1
      else:
        self.content_col_offset += 8
        self.col = self._adjusted_col() - self.content_col_offset
        if self.col < 0:
          self.col = 0

    # After word wrap recomputation, check if the cursor position still makes sense.
    # The character we just typed may have caused a word to wrap to the next line.
    if self.word_wrap:
      ar = self._adjusted_row()
      ac = self._adjusted_col()
      # Find where in the new layout the cursor should be
      # It should be right after the character we inserted
      # Simple approach: look at word_indices for our position
      if ar < len(self.word_indices) and ac < len(self.word_indices[ar]):
        i = self.word_indices[ar][ac]
        if i == invalid and ar < len(self.content):
          # We overshot - cursor is past end of this line, need to go to next line
          line_len = self._content_line_length(ar)
          if ac > line_len:
            self.col = 0
            self.content_col_offset = 0
            next_ar = ar + 1
            if next_ar < self._total_content_lines():
              if self.row + 1 >= self.height:
                self.content_row_offset += 1
              else:
                self.row += 1
              # Find the right column on the new line
              # After a word wrap, cursor should be right after the margin prefix
              # or at the position the wrapped word continues
              new_ar = self._adjusted_row()
              if new_ar < len(self.content):
                # Place cursor after whatever margin prefix is there
                prefix = _get_margin_prefix(self.content[new_ar], self.margin_char)
                self.col = len(prefix)

    self.updown_end_col = self.col
    await self.draw_field(start_at=top)
