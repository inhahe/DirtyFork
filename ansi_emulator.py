from definitions import Char, black, red, green, brown, blue, magenta, cyan, white, gray

# Parser states
STATE_NORMAL = 0
STATE_ESC = 1
STATE_CSI = 2
STATE_ESC_INTERMEDIATE = 3


class AnsiEmulator:
  def __init__(self, user):
    self.user = user
    self.state = STATE_NORMAL
    self.csi_params = ""
    self.csi_intermediate = ""

    # Scroll region (1-based)
    self.scroll_top = 1
    self.scroll_bottom = user.screen_height

    # Origin mode
    self.origin_mode = False

    # Saved cursor
    self.saved_row = 1
    self.saved_col = 1
    self.saved_fg = white
    self.saved_bg = black
    self.saved_fg_br = False
    self.saved_bg_br = False

  # ── helpers ──────────────────────────────────────────────────

  def _clamp_cursor(self):
    u = self.user
    if u.cur_row < 1:
      u.cur_row = 1
    elif u.cur_row > u.screen_height:
      u.cur_row = u.screen_height
    if u.cur_col < 1:
      u.cur_col = 1
    elif u.cur_col > u.screen_width:
      u.cur_col = u.screen_width
    u.new_row = u.cur_row
    u.new_col = u.cur_col

  def _sync_cursor(self):
    u = self.user
    u.new_row = u.cur_row
    u.new_col = u.cur_col

  def _scroll_up(self, n=1):
    """Scroll the scroll region up by n lines (content moves up, blank line at bottom)."""
    u = self.user
    top = self.scroll_top - 1   # 0-based
    bot = self.scroll_bottom - 1  # 0-based
    for _ in range(n):
      del u.screen[top]
      u.screen.insert(bot, [Char() for _ in range(u.screen_width)])

  def _scroll_down(self, n=1):
    """Scroll the scroll region down by n lines (content moves down, blank line at top)."""
    u = self.user
    top = self.scroll_top - 1
    bot = self.scroll_bottom - 1
    for _ in range(n):
      del u.screen[bot]
      u.screen.insert(top, [Char() for _ in range(u.screen_width)])

  def _erase_cell(self, row0, col0):
    """Erase a single cell (0-based indices) to a space with current colors."""
    self.user.screen[row0][col0] = Char()

  def _erase_region(self, r0_start, c0_start, r0_end, c0_end):
    """Erase cells from (r0_start, c0_start) to (r0_end, c0_end) inclusive, 0-based."""
    u = self.user
    for r in range(r0_start, r0_end + 1):
      cs = c0_start if r == r0_start else 0
      ce = c0_end if r == r0_end else u.screen_width - 1
      for c in range(cs, ce + 1):
        u.screen[r][c] = Char()

  def _parse_params(self, default=None):
    """Parse semicolon-separated CSI params into a list of ints.
    Empty/missing params get the given default value."""
    if not self.csi_params:
      return []
    parts = self.csi_params.split(";")
    result = []
    for p in parts:
      p = p.strip()
      if p == "":
        result.append(default)
      else:
        try:
          result.append(int(p))
        except ValueError:
          result.append(default)
    return result

  def _param(self, index, default=1):
    """Get a single param by index, with a default if missing."""
    params = self._parse_params(default=None)
    if index < len(params) and params[index] is not None:
      return params[index]
    return default

  # ── feed ─────────────────────────────────────────────────────

  def feed(self, data):
    for ch in data:
      if self.state == STATE_NORMAL:
        self._handle_normal(ch)
      elif self.state == STATE_ESC:
        self._handle_esc(ch)
      elif self.state == STATE_CSI:
        self._handle_csi(ch)
      elif self.state == STATE_ESC_INTERMEDIATE:
        self._handle_esc_intermediate(ch)

  # ── STATE_NORMAL ─────────────────────────────────────────────

  def _handle_normal(self, ch):
    o = ord(ch)
    if o == 0x1b:  # ESC
      self.state = STATE_ESC
      return

    if o == 0x07:  # BEL
      return
    if o == 0x08:  # BS — destructive backspace per BANSI spec
      u = self.user
      if u.cur_col > 1:
        u.cur_col -= 1
        u.screen[u.cur_row-1][u.cur_col-1] = Char(" ", fg=u.cur_fg, fg_br=u.cur_fg_br, bg=u.cur_bg, bg_br=u.cur_bg_br)
      self._sync_cursor()
      return
    if o == 0x09:  # TAB
      u = self.user
      next_tab = ((u.cur_col - 1) // 8 + 1) * 8 + 1
      if next_tab > u.screen_width:
        next_tab = u.screen_width
      u.cur_col = next_tab
      self._sync_cursor()
      return
    if o == 0x0a or o == 0x0b:  # LF or VT
      self._line_feed()
      return
    if o == 0x0c:  # FF
      self._clear_screen()
      self._home_cursor()
      return
    if o == 0x0d:  # CR
      self.user.cur_col = 1
      self._sync_cursor()
      return

    # Ignore other control chars
    if o < 32:
      return

    # Printable character
    self._put_char(ch)

  def _put_char(self, ch):
    u = self.user
    # If cursor is beyond right edge (after writing last column without wrapping),
    # handle pending wrap
    if u.cur_col > u.screen_width:
      if u.cur_wrap:
        u.cur_col = 1
        if u.cur_row == self.scroll_bottom:
          self._scroll_up(1)
        elif u.cur_row < u.screen_height:
          u.cur_row += 1
      else:
        u.cur_col = u.screen_width

    r = u.cur_row - 1
    c = u.cur_col - 1
    cell = u.screen[r][c]
    cell.char = ch
    cell.fg = u.cur_fg
    cell.bg = u.cur_bg
    cell.fg_br = u.cur_fg_br
    cell.bg_br = u.cur_bg_br

    u.cur_col += 1
    # Allow cur_col to be screen_width + 1 temporarily (pending wrap state)
    # It will be resolved on the next printable char or explicit move
    if u.cur_col > u.screen_width:
      if not u.cur_wrap:
        u.cur_col = u.screen_width
    # Don't clamp yet -- leave the pending wrap state
    u.new_row = u.cur_row
    u.new_col = min(u.cur_col, u.screen_width)

  def _line_feed(self):
    u = self.user
    if u.cur_col > u.screen_width:
      u.cur_col = u.screen_width
    if u.cur_row == self.scroll_bottom:
      self._scroll_up(1)
    elif u.cur_row < u.screen_height:
      u.cur_row += 1
    self._sync_cursor()

  def _clear_screen(self):
    u = self.user
    for r in range(u.screen_height):
      for c in range(u.screen_width):
        u.screen[r][c] = Char()

  def _home_cursor(self):
    u = self.user
    u.cur_row = 1
    u.cur_col = 1
    self._sync_cursor()

  # ── STATE_ESC ────────────────────────────────────────────────

  def _handle_esc(self, ch):
    if ch == "[":
      self.state = STATE_CSI
      self.csi_params = ""
      self.csi_intermediate = ""
      return

    if ch == "M":  # Reverse Index
      self._reverse_index()
      self.state = STATE_NORMAL
      return

    if ch == "D":  # Index
      self._index()
      self.state = STATE_NORMAL
      return

    if ch == "E":  # Next Line
      self.user.cur_col = 1
      self._line_feed()
      self.state = STATE_NORMAL
      return

    if ch == "7":  # Save Cursor
      self._save_cursor()
      self.state = STATE_NORMAL
      return

    if ch == "8":  # Restore Cursor
      self._restore_cursor()
      self.state = STATE_NORMAL
      return

    if ch == "c":  # Full Reset
      self._full_reset()
      self.state = STATE_NORMAL
      return

    # Unknown ESC sequence -- some have intermediate bytes (e.g. ESC ( B)
    if ch in " #(%+":
      self.state = STATE_ESC_INTERMEDIATE
      return

    # Unknown, just go back to normal
    self.state = STATE_NORMAL

  def _handle_esc_intermediate(self, ch):
    # Eat the final byte of a two-byte ESC sequence (e.g. ESC ( B)
    self.state = STATE_NORMAL

  def _reverse_index(self):
    u = self.user
    if u.cur_row == self.scroll_top:
      self._scroll_down(1)
    elif u.cur_row > 1:
      u.cur_row -= 1
    self._sync_cursor()

  def _index(self):
    u = self.user
    if u.cur_row == self.scroll_bottom:
      self._scroll_up(1)
    elif u.cur_row < u.screen_height:
      u.cur_row += 1
    self._sync_cursor()

  def _save_cursor(self):
    u = self.user
    self.saved_row = u.cur_row
    self.saved_col = u.cur_col
    self.saved_fg = u.cur_fg
    self.saved_bg = u.cur_bg
    self.saved_fg_br = u.cur_fg_br
    self.saved_bg_br = u.cur_bg_br

  def _restore_cursor(self):
    u = self.user
    u.cur_row = self.saved_row
    u.cur_col = self.saved_col
    u.cur_fg = self.saved_fg
    u.cur_bg = self.saved_bg
    u.cur_fg_br = self.saved_fg_br
    u.cur_bg_br = self.saved_bg_br
    self._clamp_cursor()

  def _full_reset(self):
    u = self.user
    u.cur_row = 1
    u.cur_col = 1
    u.cur_fg = white
    u.cur_bg = black
    u.cur_fg_br = False
    u.cur_bg_br = False
    u.cur_wrap = True
    self.scroll_top = 1
    self.scroll_bottom = u.screen_height
    self.origin_mode = False
    self._clear_screen()
    self._sync_cursor()

  # ── STATE_CSI ────────────────────────────────────────────────

  def _handle_csi(self, ch):
    o = ord(ch)
    # Parameter bytes: 0x30-0x3F (digits 0-9, semicolon, and ? < = >)
    if 0x30 <= o <= 0x3F:
      self.csi_params += ch
      return
    # Intermediate bytes: 0x20-0x2F (space, ! " # $ etc.)
    if 0x20 <= o <= 0x2F:
      self.csi_intermediate += ch
      return
    # Final byte: 0x40-0x7E
    if 0x40 <= o <= 0x7E:
      self._dispatch_csi(ch)
      self.state = STATE_NORMAL
      return
    # Invalid byte -- abort
    self.state = STATE_NORMAL

  def _dispatch_csi(self, final):
    # Check for private mode sequences (ESC[? ...)
    if self.csi_params.startswith("?"):
      self._handle_private_mode(final)
      return

    if final == "A":
      self._csi_cuu()
    elif final == "B":
      self._csi_cud()
    elif final == "C":
      self._csi_cuf()
    elif final == "D":
      self._csi_cub()
    elif final == "E":
      self._csi_cnl()
    elif final == "F":
      self._csi_cpl()
    elif final == "G":
      self._csi_cha()
    elif final == "H" or final == "f":
      self._csi_cup()
    elif final == "J":
      self._csi_ed()
    elif final == "K":
      self._csi_el()
    elif final == "L":
      self._csi_il()
    elif final == "M":
      self._csi_dl()
    elif final == "P":
      self._csi_dch()
    elif final == "@":
      self._csi_ich()
    elif final == "S":
      self._csi_su()
    elif final == "T":
      self._csi_sd()
    elif final == "m":
      self._csi_sgr()
    elif final == "s":
      self._save_cursor()
    elif final == "u":
      self._restore_cursor()
    elif final == "U":
      # Clear screen (BananaCom, same as ^L)
      self._clear_screen()
    elif final == "Z":
      # Back tab — move cursor to previous tab stop
      self._csi_cbt()
    elif final == "n":
      pass  # Device Status Report -- ignore
    elif final == "r":
      self._csi_decstbm()
    # else: unknown CSI sequence, ignore

  # ── Private mode (ESC[? ...) ─────────────────────────────────

  def _handle_private_mode(self, final):
    # Strip the leading '?' from params
    param_str = self.csi_params[1:]
    try:
      code = int(param_str) if param_str else 0
    except ValueError:
      return

    if final == "h":  # Set mode
      if code == 7:
        self.user.cur_wrap = True
      elif code == 25:
        pass  # Show cursor -- ignore
      elif code == 6:
        self.origin_mode = True
        # Home cursor to top of scroll region
        self.user.cur_row = self.scroll_top
        self.user.cur_col = 1
        self._sync_cursor()
    elif final == "l":  # Reset mode
      if code == 7:
        self.user.cur_wrap = False
      elif code == 25:
        pass  # Hide cursor -- ignore
      elif code == 6:
        self.origin_mode = False
        self.user.cur_row = 1
        self.user.cur_col = 1
        self._sync_cursor()

  # ── CSI command implementations ──────────────────────────────

  def _csi_cuu(self):
    """Cursor Up"""
    n = self._param(0, 1)
    u = self.user
    u.cur_row = max(self.scroll_top, u.cur_row - n)
    self._sync_cursor()

  def _csi_cud(self):
    """Cursor Down"""
    n = self._param(0, 1)
    u = self.user
    u.cur_row = min(self.scroll_bottom, u.cur_row + n)
    self._sync_cursor()

  def _csi_cuf(self):
    """Cursor Forward"""
    n = self._param(0, 1)
    u = self.user
    u.cur_col = min(u.screen_width, u.cur_col + n)
    self._sync_cursor()

  def _csi_cub(self):
    """Cursor Backward"""
    n = self._param(0, 1)
    u = self.user
    u.cur_col = max(1, u.cur_col - n)
    self._sync_cursor()

  def _csi_cnl(self):
    """Cursor Next Line"""
    n = self._param(0, 1)
    u = self.user
    u.cur_row = min(self.scroll_bottom, u.cur_row + n)
    u.cur_col = 1
    self._sync_cursor()

  def _csi_cpl(self):
    """Cursor Previous Line"""
    n = self._param(0, 1)
    u = self.user
    u.cur_row = max(self.scroll_top, u.cur_row - n)
    u.cur_col = 1
    self._sync_cursor()

  def _csi_cha(self):
    """Cursor Horizontal Absolute"""
    col = self._param(0, 1)
    u = self.user
    u.cur_col = max(1, min(u.screen_width, col))
    self._sync_cursor()

  def _csi_cup(self):
    """Cursor Position"""
    row = self._param(0, 1)
    col = self._param(1, 1)
    u = self.user
    if self.origin_mode:
      row += self.scroll_top - 1
      row = max(self.scroll_top, min(self.scroll_bottom, row))
    else:
      row = max(1, min(u.screen_height, row))
    u.cur_row = row
    u.cur_col = max(1, min(u.screen_width, col))
    self._sync_cursor()

  def _csi_ed(self):
    """Erase in Display"""
    mode = self._param(0, 0)
    u = self.user
    r = u.cur_row - 1
    c = min(u.cur_col, u.screen_width) - 1
    if mode == 0:  # Erase below (from cursor to end)
      # Current position to end of line
      for col in range(c, u.screen_width):
        u.screen[r][col] = Char()
      # All lines below
      for row in range(r + 1, u.screen_height):
        for col in range(u.screen_width):
          u.screen[row][col] = Char()
    elif mode == 1:  # Erase above (from start to cursor)
      # All lines above
      for row in range(0, r):
        for col in range(u.screen_width):
          u.screen[row][col] = Char()
      # Start of current line to cursor
      for col in range(0, c + 1):
        u.screen[r][col] = Char()
    elif mode == 2 or mode == 3:  # Erase all
      self._clear_screen()

  def _csi_el(self):
    """Erase in Line"""
    mode = self._param(0, 0)
    u = self.user
    r = u.cur_row - 1
    c = min(u.cur_col, u.screen_width) - 1
    if mode == 0:  # Erase to right
      for col in range(c, u.screen_width):
        u.screen[r][col] = Char()
    elif mode == 1:  # Erase to left
      for col in range(0, c + 1):
        u.screen[r][col] = Char()
    elif mode == 2:  # Erase entire line
      for col in range(u.screen_width):
        u.screen[r][col] = Char()

  def _csi_il(self):
    """Insert Lines"""
    n = self._param(0, 1)
    u = self.user
    r = u.cur_row - 1
    bot = self.scroll_bottom - 1
    for _ in range(n):
      if bot < len(u.screen):
        del u.screen[bot]
      u.screen.insert(r, [Char() for _ in range(u.screen_width)])

  def _csi_dl(self):
    """Delete Lines"""
    n = self._param(0, 1)
    u = self.user
    r = u.cur_row - 1
    bot = self.scroll_bottom - 1
    for _ in range(n):
      if r < len(u.screen):
        del u.screen[r]
      u.screen.insert(bot, [Char() for _ in range(u.screen_width)])

  def _csi_dch(self):
    """Delete Characters"""
    n = self._param(0, 1)
    u = self.user
    r = u.cur_row - 1
    c = min(u.cur_col, u.screen_width) - 1
    row = u.screen[r]
    for _ in range(n):
      if c < len(row):
        del row[c]
        row.append(Char())

  def _csi_ich(self):
    """Insert Characters"""
    n = self._param(0, 1)
    u = self.user
    r = u.cur_row - 1
    c = min(u.cur_col, u.screen_width) - 1
    row = u.screen[r]
    for _ in range(n):
      row.insert(c, Char())
      if len(row) > u.screen_width:
        row.pop()

  def _csi_su(self):
    """Scroll Up"""
    n = self._param(0, 1)
    self._scroll_up(n)

  def _csi_sd(self):
    """Scroll Down"""
    n = self._param(0, 1)
    self._scroll_down(n)

  def _csi_sgr(self):
    """Select Graphic Rendition"""
    params = self._parse_params(default=0)
    if not params:
      params = [0]
    u = self.user
    for p in params:
      if p is None:
        p = 0
      if p == 0:
        u.cur_fg = white
        u.cur_bg = black
        u.cur_fg_br = False
        u.cur_bg_br = False
      elif p == 1:
        u.cur_fg_br = True
      elif p == 2 or p == 22:
        u.cur_fg_br = False
      elif p == 4:
        pass  # Underscore — not tracked, ignore
      elif p == 5 or p == 6:
        u.cur_bg_br = True  # Blink = bright bg on BBS terminals
      elif p == 7:
        # Reverse video — swap fg and bg
        u.cur_fg, u.cur_bg = u.cur_bg, u.cur_fg
        u.cur_fg_br, u.cur_bg_br = u.cur_bg_br, u.cur_fg_br
      elif p == 8:
        # Invisible text — set fg to match bg
        u.cur_fg = u.cur_bg
        u.cur_fg_br = u.cur_bg_br
      elif p == 25:
        u.cur_bg_br = False
      elif 30 <= p <= 37:
        u.cur_fg = p - 30
      elif 40 <= p <= 47:
        u.cur_bg = p - 40

  def _csi_cbt(self):
    """Cursor Backward Tabulation (back tab)"""
    n = self._param(0, 1)
    u = self.user
    for _ in range(n):
      # Tab stops at columns 1, 9, 17, 25, 33, 41, 49, 57, 65, 73
      col = u.cur_col - 1  # 0-based
      if col <= 0:
        break
      # Find previous tab stop: round down to nearest multiple of 8, then +1 for 1-based
      col = ((col - 1) // 8) * 8 + 1  # 1-based
      u.cur_col = max(1, col)
    self._sync_cursor()

  def _csi_decstbm(self):
    """Set Scrolling Region (DECSTBM)"""
    top = self._param(0, 1)
    bot = self._param(1, self.user.screen_height)
    u = self.user
    top = max(1, min(u.screen_height, top))
    bot = max(1, min(u.screen_height, bot))
    if top < bot:
      self.scroll_top = top
      self.scroll_bottom = bot
    else:
      self.scroll_top = 1
      self.scroll_bottom = u.screen_height
    # CUP to home after setting scroll region
    if self.origin_mode:
      u.cur_row = self.scroll_top
    else:
      u.cur_row = 1
    u.cur_col = 1
    self._sync_cursor()
