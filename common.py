import asyncio, os, sqlite3, collections, re
import paths
from collections import deque

import bcrypt

from input_output import *
from keyboard_codes import *
from config import *
from definitions import *

config = get_config()

# Lazy imports to avoid circular dependencies
_modules = None
_menu = None

def _ensure_imports():
  global _modules, _menu
  if _modules is None:
    from modules import modules
    _modules = modules
  if _menu is None:
    import menu
    _menu = menu

con = sqlite3.connect(paths.resolve_data(str(config.database)))
con.row_factory = sqlite3.Row
cur = con.cursor()

def _ensure_tables():
  cur.executescript("""
    CREATE TABLE IF NOT EXISTS USERS (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      handle TEXT UNIQUE NOT NULL,
      cmd_line_handle TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      password_salt TEXT NOT NULL,
      time_created INT );
    CREATE TABLE IF NOT EXISTS USER_KEYS (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INT NOT NULL,
      key TEXT,
      FOREIGN KEY (user_id) REFERENCES users(id) );
    CREATE TABLE IF NOT EXISTS PRIVATE_MESSAGES (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      from_user INT NOT NULL,
      to_user INT NOT NULL,
      reply_to INT,
      subject TEXT,
      message TEXT,
      time_created INT,
      time_read INT,
      FOREIGN KEY (from_user) REFERENCES users(id),
      FOREIGN KEY (to_user) REFERENCES users(id),
      FOREIGN KEY (reply_to) REFERENCES private_messages(id) );
    CREATE TABLE IF NOT EXISTS FORUMS (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT );
    CREATE TABLE IF NOT EXISTS FORUM_MESSAGES (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      from_user INT NOT NULL,
      reply_to INT,
      forum INT NOT NULL,
      subject TEXT,
      message TEXT,
      time_created INT,
      FOREIGN KEY (from_user) REFERENCES users(id),
      FOREIGN KEY (reply_to) REFERENCES forum_messages(id),
      FOREIGN KEY (forum) REFERENCES forums(id) );
    CREATE TABLE IF NOT EXISTS FORUM_MESSAGES_READ (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INT NOT NULL,
      message_id INT NOT NULL,
      time_read INT,
      FOREIGN KEY (user_id) REFERENCES users(id),
      FOREIGN KEY (message_id) REFERENCES forum_messages(id) );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_fmr_user_msg
      ON FORUM_MESSAGES_READ (user_id, message_id);
  """)
  con.commit()

_ensure_tables()

class GlobalData:
  def __init__(self):
    self.users = {}
    self.users_logging_in = set()

global_data = GlobalData()

class User:
  def __init__(self, reader, writer):
    if config.user_defaults and hasattr(config.user_defaults, 'keys'):
      for k in list(config.user_defaults.keys()):
        setattr(self, k, config.user_defaults[k])
    self.reader = reader
    self.writer = writer
    self.screen_width = None
    self.screen_height = None
    self.screen = None
    self.click_screen = None
    self.handle = None
    self.user_id = None
    self.keys = set()
    self.cur_input = None
    self.cur_wrap = True
    self.cur_in_input = False
    self.failed_login_attempts = 0
    self.destination_history = deque()
    self.input_timestamps = deque()
    self.batch_mode = False
    self.cur_input_code = ""
    self.screen_history = collections.deque()
    self.email = None
    self.sex = None
    self.age = None
    self.location = None
    self.time_created = None
    self.login_tries = []
    self.config = None
    self.cur_fg = white
    self.cur_bg = black
    self.cur_fg_br = False
    self.cur_bg_br = False
    self.new_fg = white
    self.new_bg = black
    self.new_fg_br = False
    self.new_bg_br = False
    self.cur_row = 1
    self.cur_col = 1
    self.new_row = 1
    self.new_col = 1
    self.scroll_region_top = None
    self.scroll_region_bottom = None
    self.scroll_region_strict = False
    self.terminal = SyncTERM  # default terminal type
    self.cur_show_cursor = True
    self.encoding = "cp437"   # default encoding, updated by detect_terminal
    self.ttype = "unknown"    # terminal type string from TTYPE negotiation
    self.in_door = False      # True while user is in a door game
    self.mouse_reporting = False  # True when mouse click reporting (ESC[?1000h) is active
    self.popup_event = None   # asyncio.Event set when a popup needs to interrupt the door bridge
    self.popup_queue = []     # queued popups waiting to show (list of kwarg dicts)
    self._in_popup = False    # True while a popup is being displayed

line_pos_re = re.compile('\x1b\\[(\\d+);(\\d+)R')
email_re = re.compile(r'''(?:[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+(?:\.[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9\x2d]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])''')
handle_re = re.compile("[A-Za-z0-9_]")

async def read_cursor_position(user):
  while True:
    key = await get_input_key(user)
    if key == position:
      return key.row, key.col

def setup_user_session(user, handle, user_id, time_created):
  """Set up a user's session after successful login or registration.
  Loads their keys from DB, their YAML config, and applies preferences."""
  user.handle = handle
  user.time_created = time_created
  user.user_id = user_id
  cur.execute("SELECT key FROM user_keys WHERE user_id = ?", (user_id,))
  key_rows = cur.fetchall()
  user.keys = expand_keys(set(kr["key"] for kr in key_rows))

  # Auto-grant or revoke the sysop key based on sysop_handle in config.
  # If sysop_handle is set, only that handle gets the sysop key; anyone else loses it on login.
  sysop_handle_conf = str(config.sysop_handle) if config.sysop_handle else None
  if sysop_handle_conf and handle.lower() == sysop_handle_conf.lower():
    if 'sysop' not in user.keys:
      cur.execute("INSERT INTO USER_KEYS (user_id, key) VALUES (?, ?)", (user_id, 'sysop'))
      con.commit()
      user.keys.add('sysop')
      user.keys = expand_keys(user.keys)
  elif sysop_handle_conf and 'sysop' in user.keys:
    cur.execute("DELETE FROM USER_KEYS WHERE user_id = ? AND key = 'sysop'", (user_id,))
    con.commit()
    user.keys.discard('sysop')

  user.input_timestamps = deque()
  user.batch_mode = False
  global_data.users_logging_in.discard(user)
  global_data.users[handle.lower()] = user

  # Load user's YAML config (profile data, preferences)
  conf3 = get_config()
  try:
    user_conf_dir = paths.resolve_data(str(config.user_configs or "user_configs"))
    user_conf_path = os.path.join(str(user_conf_dir), handle + ".yaml")
    conf1 = get_config(path=user_conf_path) if os.path.exists(user_conf_path) else conf3
  except Exception:
    conf1 = conf3
  conf2 = conf3
  user.conf = ConfigView(conf1, conf2, conf3)

  # Profile data from YAML
  user.email = str(user.conf.email) if user.conf.email else None
  user.age = str(user.conf.age) if user.conf.age else None
  user.sex = str(user.conf.sex) if user.conf.sex else None
  user.location = str(user.conf.location) if user.conf.location else None
  user.bio = str(user.conf.bio) if user.conf.bio else None

  # Apply saved encoding preference
  if user.conf.encoding:
    user.encoding = str(user.conf.encoding)
    _set_connection_encoding(user)


def expand_keys(keys):
  """Expand a set of keys through key_groups, resolving recursively."""
  groups = config.key_groups
  if not groups or groups is null:
    return keys
  expanded = set(keys)
  queue = list(keys)
  while queue:
    key = queue.pop()
    members = getattr(groups, key, None) if not isinstance(groups, dict) else groups.get(key)
    if not members:
      continue
    for member in members:
      if member not in expanded:
        expanded.add(member)
        queue.append(member)
  return expanded


def check_keys(user, destination, menu_item=None):
  # destination can be a handler (has .dest_name) or a config object
  item = menu_item or destination
  if item is None:
    return RetVals(status=success, lacking_keys=set(), bad_keys=set())
  dest_name = getattr(item, 'dest_name', None)
  if dest_name:
    item = config.destinations[dest_name] if config.destinations else null
  if not item or item is null or isinstance(item, str):
    return RetVals(status=success, lacking_keys=set(), bad_keys=set())
  wk = getattr(item, 'white_keys', None)
  bk = getattr(item, 'black_keys', None)
  white_set = set(wk) if wk else set()
  black_set = set(bk) if bk else set()
  lacking_keys = white_set - user.keys
  bad_keys = black_set & user.keys
  return RetVals(status=fail if (lacking_keys or bad_keys) else success, lacking_keys=lacking_keys, bad_keys=bad_keys)

# CGA color index (low 3 bits) → ANSI/BBS internal color
_CGA_TO_ANSI = [0, 4, 2, 6, 1, 5, 3, 7]

async def _render_screen_to_terminal(user):
  """Render user.screen to the terminal using run-length color encoding."""
  if not user.screen:
    return
  ansi_wrap(user, False)
  for r in range(min(user.screen_height, len(user.screen))):
    row_data = user.screen[r]
    n = min(user.screen_width, len(row_data))
    c = 0
    await ansi_move_deferred(user, row=r + 1, col=1, drain=False)
    while c < n:
      cell = row_data[c]
      run_end = c + 1
      while run_end < n:
        nc = row_data[run_end]
        if (nc.fg == cell.fg and nc.fg_br == cell.fg_br and
            nc.bg == cell.bg and nc.bg_br == cell.bg_br):
          run_end += 1
        else:
          break
      ansi_color(user, fg=cell.fg, fg_br=cell.fg_br, bg=cell.bg, bg_br=cell.bg_br)
      await send(user, "".join(row_data[i].char for i in range(c, run_end)), drain=False)
      c = run_end
  ansi_wrap(user, True)
  ansi_color(user)
  await user.writer.drain()

async def show_screen(user, path):
  """Display an ANSI (.ans/.ansi) or BIN (.bin) screen file.
  Clears the terminal, renders the file content, and updates user.screen."""
  resolved = paths.resolve_data(str(path))
  ext = os.path.splitext(resolved)[1].lower()
  try:
    with open(resolved, 'rb') as f:
      data = f.read()
  except OSError:
    await ansi_cls(user)
    return
  ansi_wrap(user, False)
  await ansi_cls(user)
  if ext == '.bin':
    cols = 80
    total_cells = len(data) // 2
    rows = min(total_cells // cols, user.screen_height)
    for r in range(rows):
      for c in range(min(cols, user.screen_width)):
        idx = (r * cols + c) * 2
        if idx + 1 >= len(data):
          break
        char_byte = data[idx]
        attr_byte = data[idx + 1]
        fg_cga = attr_byte & 0x0F
        bg_cga = (attr_byte >> 4) & 0x07
        bg_br = bool(attr_byte & 0x80)
        fg_ansi = _CGA_TO_ANSI[fg_cga & 7]
        fg_br = bool(fg_cga & 8)
        bg_ansi = _CGA_TO_ANSI[bg_cga]
        user.screen[r][c] = Char(bytes([char_byte]).decode('cp437'),
                                  fg=fg_ansi, fg_br=fg_br, bg=bg_ansi, bg_br=bg_br)
  else:
    from ansi_emulator import AnsiEmulator
    emu = AnsiEmulator(user)
    emu.feed(data.decode('cp437', errors='replace'))
  await _render_screen_to_terminal(user)

async def get_screen_size(user):
   user.writer.write("Detecting screen size...")
   user.writer.write("\x1b[999;999H\x1b[6n")
   await user.writer.drain()
   try:
     return await asyncio.wait_for(read_cursor_position(user), timeout=3.0)
   except asyncio.TimeoutError:
     user.writer.write("We couldn't detect your screen size. Assuming 25x80.")
     return 25, 80

def _set_connection_encoding(user):
  """Switch the telnetlib3 reader/writer encoding for this connection."""
  enc = user.encoding
  def fn_encoding(outgoing=False, incoming=False):
    return enc
  if hasattr(user.writer, 'fn_encoding'):
    user.writer.fn_encoding = fn_encoding
  if hasattr(user.reader, 'fn_encoding'):
    user.reader.fn_encoding = fn_encoding

# Known terminal types and their default encodings
# Terminals we can confidently auto-detect encoding for.
# SyncTERM is NOT here because it supports both CP437 and UTF-8.
_UTF8_TERMINALS = {"xterm", "xterm-256color", "vt100", "vt220", "linux",
                   "rxvt", "screen", "tmux", "iterm2", "alacritty",
                   "kitty", "wezterm", "foot", "contour", "ghostty"}
_CP437_TERMINALS = {"ansi", "ansi-bbs", "avatar", "pcansi"}

async def detect_terminal(user):
  """Detect terminal encoding from TTYPE negotiation. Defaults to CP437 if unknown.
  Any saved encoding preference in user.conf overrides this after login."""
  ttype = None
  try:
    ttype = user.writer.get_extra_info("TERM")
  except Exception:
    pass
  if not ttype:
    await asyncio.sleep(0.5)
    try:
      ttype = user.writer.get_extra_info("TERM")
    except Exception:
      pass

  if ttype:
    user.ttype = ttype
    ttype_lower = ttype.lower()
    for name in _CP437_TERMINALS:
      if name in ttype_lower:
        user.encoding = "cp437"
        _set_connection_encoding(user)
        return
    for name in _UTF8_TERMINALS:
      if name in ttype_lower:
        user.encoding = "utf-8"
        _set_connection_encoding(user)
        return
  else:
    user.ttype = "unknown"

  # Unknown terminal — default to CP437
  user.encoding = "cp437"
  _set_connection_encoding(user)


class _DestinationRegistry:
  """Every destination is accessible as Destinations.name and is an async callable(user) -> RetVals.
  Built-in destinations (login, logout) are defined as methods.
  Config-defined destinations (menus, modules) are created on first access and cached."""

  async def setup_terminal(self, user):
    """Detect terminal type, screen size, and clear screen. Only called once per connection."""
    await detect_terminal(user)
    rows, cols = await get_screen_size(user)
    user.screen_height = rows
    user.screen_width = cols
    user.screen = [[Char() for col in range(cols)] for row in range(rows)]
    user.click_screen = [[None]*cols for row in range(rows)]
    await ansi_cls(user)
  setup_terminal.dest_name = "setup_terminal"

  async def login(self, user):
    from input_fields import InputField
    def check_handle(handle):
      cur.execute("SELECT * FROM users WHERE handle = ? COLLATE NOCASE LIMIT 1", (handle,))
      user_in_db = cur.fetchone()
      if user_in_db is None:
        user.login_tries.append((handle,))
        return RetVals(status=fail, err_msg=f"{handle} is not a registered user on this system")
      return RetVals(status=success, user_in_db=user_in_db)

    async def check_password(user_in_db, password):
      if user_in_db["password_hash"] == bcrypt.hashpw(password.encode("utf-8"), user_in_db["password_salt"]):
        return RetVals(status=success)
      return RetVals(status=fail, err_msg="The password you entered is incorrect.")

    # Clear screen for login prompt
    await ansi_cls(user)
    await send(user, f"Welcome to {config.bbs_name}" + cr+lf)
    await send(user, f"Encoding: {user.encoding}  (change in Settings if graphics look wrong)" + cr+lf)
    allowed_attempts = config.login.allowed_attempts or 3
    for x in range(allowed_attempts):
      await send(user, cr+lf + 'Enter your handle or "new" to sign up.' + cr+lf+cr+lf, drain=True)
      handle_r = await InputField.create(user=user, conf=config.input_fields.input_field, width=31, max_length=30)
      handle = handle_r.content if hasattr(handle_r, 'content') else str(handle_r)
      handle = handle.strip()
      if not handle:
        continue
      if handle.lower() == "new":
        # Run registration inline
        _ensure_imports()
        if 'register' in _modules:
          dest_conf = config.destinations.register if config.destinations else null
          r = await _modules['register'].run(user, dest_conf)
          if r.status == success and user.handle:
            # Registration auto-logged in — go straight to main
            return RetVals(status=success, next_destination=self.main, next_menu_item=null)
          # Registration aborted or failed — clear screen and loop back to login
          await ansi_cls(user)
          await send(user, f"Welcome to {config.bbs_name}" + cr+lf)
          await send(user, f"Encoding: {user.encoding}  (change in Settings if graphics look wrong)" + cr+lf, drain=True)
        continue
      r = check_handle(handle)
      if r.status == fail:
        user.login_tries.append((handle, None))
        await send(user, cr+lf + r.err_msg)
        continue
      user_in_db = r.user_in_db
      await send(user, cr+lf + "Enter your password." + cr+lf, drain=True)
      password_r = await InputField.create(user=user, conf=config.input_fields.input_field, width=50, max_length=49, height=1)
      password = password_r.content if hasattr(password_r, 'content') else str(password_r)
      r = await check_password(user_in_db, password)
      if r.status == success:
        uid = user_in_db["id"] if "id" in user_in_db.keys() else null
        setup_user_session(user, user_in_db["handle"], uid, user_in_db["time_created"])
        if 'banned' in user.keys:
          await send(user, cr+lf+cr+lf + "Your account has been banned." + cr+lf, drain=True)
          return RetVals(status=fail, next_destination=self.logout, next_menu_item=null)
        # Check for user-defined start destination
        start_dest = self.main
        start_item = null
        if user.conf.start_destination:
          from menu import resolve_jump
          dest_name, menu_item, parent_menu, err = resolve_jump(str(user.conf.start_destination))
          if dest_name and not err:
            start_dest = getattr(Destinations, dest_name, self.main)
            start_item = menu_item if menu_item else null
        return RetVals(status=success, next_destination=start_dest, next_menu_item=start_item)
      user.login_tries.append((handle, password))
      await send(user, cr+lf+cr+lf + r.err_msg)
    return RetVals(status=fail, err_msg="max failed attempts", next_destination=self.logout, next_menu_item=null)
  login.dest_name = "login"

  async def logout(self, user):
    try:
      from input_output import ansi_cls, send, ansi_color
      from definitions import cr, lf, white, black, cyan
      await ansi_cls(user)
      ansi_color(user, fg=cyan, fg_br=True, bg=black)
      await send(user, cr + lf + "  Goodbye, " + getattr(user, 'handle', 'stranger') + "!" + cr + lf, drain=False)
      ansi_color(user, fg=white, fg_br=False, bg=black)
      bbs_name = config.bbs_name or "the BBS"
      await send(user, f"  Thanks for visiting {bbs_name}." + cr + lf, drain=True)
      import asyncio
      await asyncio.sleep(1)
    except Exception:
      pass
    user.writer.close()
    handle = getattr(user, 'handle', None)
    if handle and handle.lower() in global_data.users:
      del global_data.users[handle.lower()]
    global_data.users_logging_in.discard(user)
  logout.dest_name = "logout"

  def __getattr__(self, name):
    """Auto-create handlers for config-defined destinations (menus, modules)."""
    _ensure_imports()
    dest_conf = config.destinations[name] if config.destinations else null
    if not dest_conf or dest_conf is null:
      raise AttributeError(f"No destination '{name}'")

    dest_type = dest_conf.type

    if dest_type == "menu":
      async def handler(user, menu_item=null):
        r = await _menu.do_menu(user, name)
        if not hasattr(r, 'next_destination'):
          r.next_destination = self.main
        if not hasattr(r, 'next_menu_item'):
          r.next_menu_item = null
        return r

    elif dest_type == "module":
      async def handler(user, menu_item=null):
        mod_name = name  # capture for closure
        if menu_item and menu_item is not null and isinstance(menu_item, str):
          # Validate menu_item against the parent menu's options
          parent = getattr(handler, 'parent_menu', None)
          if parent and config.menu_system:
            mc = config.menu_system[parent]
            if mc and mc.options and menu_item not in mc.options:
              from logger import log as _log
              _log.warning("Module '%s' received unknown menu_item '%s' (parent menu '%s')",
                           mod_name, menu_item, parent)
        if mod_name in _modules:
          r = await _modules[mod_name].run(user, dest_conf, menu_item)
          if not hasattr(r, 'next_destination'):
            r.next_destination = self.main
          if not hasattr(r, 'next_menu_item'):
            r.next_menu_item = null
          return r
        return RetVals(status=fail, err_msg=f"Module not found: {mod_name}",
                       next_destination=self.main, next_menu_item=null)

    else:
      raise AttributeError(f"Unknown destination type for '{name}': {dest_type}")

    handler.dest_name = name
    handler.parent_menu = None
    setattr(self, name, handler)  # cache it so __getattr__ isn't called again
    return handler

Destinations = _DestinationRegistry()


def _find_fallback_destination(user, avoid=None):
  """Find a safe destination to fall back to.
  Walks backward through destination_history, skipping:
    - destinations that failed (status != success)
    - destinations the user no longer has keys for
    - the destination in `avoid` (the one that just errored)
  Falls back to main, then logout as last resort."""
  avoid_name = getattr(avoid, 'dest_name', None) if avoid else None
  seen = set()
  for entry in reversed(user.destination_history):
    dest = getattr(entry, 'destination', null)
    if not dest or dest is null:
      continue
    dest_name = getattr(dest, 'dest_name', None)
    # Skip the one we're trying to avoid
    if dest_name and dest_name == avoid_name:
      continue
    # Skip already-checked destinations
    if dest_name and dest_name in seen:
      continue
    if dest_name:
      seen.add(dest_name)
    # Skip destinations that failed last time
    if getattr(entry, 'status', null) != success:
      continue
    # Check that user still has access
    r = check_keys(user, dest)
    if r.status == success:
      return dest
  # Fall back to main (unless that's what we're avoiding)
  if avoid_name != 'main':
    r = check_keys(user, Destinations.main)
    if r.status == success:
      return Destinations.main
  # Absolute last resort
  return Destinations.logout


async def do_destination(user, destination, menu_item=null):
  """Execute a destination handler. Just runs it and ensures the return value
  has next_destination and next_menu_item. No key checking — that's user_director's job."""
  if menu_item and menu_item is not null:
    r = await destination(user, menu_item)
  else:
    r = await destination(user)
  if r is None:
    r = RetVals(status=fail, err_msg="Destination returned nothing")
  if not hasattr(r, 'next_destination'):
    r.next_destination = Destinations.main
  if not hasattr(r, 'next_menu_item'):
    r.next_menu_item = null
  return r


async def user_director(user, next_destination, menu_item=null):
  """Central routing function. Decides where the user goes next.
  1. Checks keys for the requested destination
  2. If denied, finds a safe fallback from destination history
  3. If allowed, calls do_destination to run it
  4. If the destination errors, finds a safe fallback
  Returns RetVals with next_destination set for the next iteration."""

  dest_name = getattr(next_destination, 'dest_name', None)

  # Check keys (skip for built-ins that must always be accessible)
  if dest_name and dest_name not in ('login', 'logout', 'setup_terminal', 'main'):
    result = check_keys(user, next_destination)
    if result.status == fail:
      lacking = getattr(result, 'lacking_keys', set())
      bad = getattr(result, 'bad_keys', set())
      parts = []
      if lacking:
        parts.append(f"Missing keys: {', '.join(lacking)}")
      if bad:
        parts.append(f"Restricted keys: {', '.join(bad)}")
      err_msg = f"Access denied to {dest_name}. " + "; ".join(parts)

      parent_menu = getattr(next_destination, 'parent_menu', None)
      if parent_menu:
        # Return to the source menu and let it show the error inline or as a popup
        user.pending_menu_error = err_msg
        return RetVals(status=fail, err_msg=err_msg,
                       next_destination=getattr(Destinations, parent_menu), next_menu_item=null)

      from input_fields import show_message_box
      await show_message_box(user, err_msg, title="Access Denied",
                             fg=white, fg_br=True, bg=black,
                             outline_fg=red, outline_fg_br=True)

      fallback = _find_fallback_destination(user, avoid=next_destination)
      return RetVals(status=fail, err_msg=err_msg,
                     next_destination=fallback, next_menu_item=null)

  # Reset mouse reporting and colors before each destination (in case previous one didn't clean up)
  user.writer.write("\x1b[?1000l")
  user.mouse_reporting = False
  ansi_color(user, drain=True)

  # Access granted — run the destination
  try:
    r = await do_destination(user, next_destination, menu_item)
  except Disconnected:
    raise
  except Exception:
    import traceback
    from logger import log as _log
    err_msg = traceback.format_exc()
    dest_name = getattr(next_destination, 'dest_name', '?')
    _log.error("Error in destination %s for user %s:\n%s", dest_name, getattr(user, 'handle', '?'), err_msg)
    fallback = _find_fallback_destination(user, avoid=next_destination)
    if getattr(fallback, 'dest_name', None) == 'logout':
      parent = getattr(next_destination, 'parent_menu', None)
      fallback = getattr(Destinations, parent) if parent else next_destination
    r = RetVals(status=fail, err_msg=err_msg, err_word_wrap=False,
                next_destination=fallback, next_menu_item=null)

  # If the destination returned a failure with an error message, show it to the user
  if r.status == fail and getattr(r, 'err_msg', None):
    from input_fields import show_message_box
    word_wrap = getattr(r, 'err_word_wrap', True)
    await show_message_box(user, r.err_msg, title="Error",
                           fg=white, fg_br=True, bg=black,
                           outline_fg=red, outline_fg_br=True,
                           word_wrap=word_wrap)

  # Record in history
  user.destination_history.append(RetVals(
    destination=next_destination,
    dest_name=dest_name,
    status=r.status,
    err_msg=getattr(r, 'err_msg', None)
  ))

  return r
