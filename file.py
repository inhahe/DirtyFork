"""
File Library — browse, search, upload, and download files via ZMODEM or YMODEM-G.

Files live in `config.files_dir` (default "files").
Metadata (keys + description per file) lives in `config.files_meta` (default "files/meta.yaml").
Valid tags are defined in `config.file_tags`.
"""

import os
from ruamel.yaml import YAML
_yaml = YAML()
_yaml.default_flow_style = False

from definitions import (RetVals, Disconnected, success, fail,
                         cr, lf, null,
                         white, black, green, cyan, red, blue, brown, magenta)
from input_output import send, ansi_color, ansi_move_deferred, ansi_wrap, ansi_cls, get_input_key
from input_fields import show_message_box, InputFields
from file_transfer import (send_file_zmodem, recv_file_zmodem,
                           send_file_ymodem, recv_file_ymodem,
                           get_available_protocols)
from keyboard_codes import up, down, pgup, pgdn, home, end, back
from config import get_config
from logger import log
import paths

config = get_config()

# ---------------------------------------------------------------------------
# Box-drawing helpers (CP437)
# ---------------------------------------------------------------------------
_TL  = bytes([218]).decode('cp437')  # top-left
_TR  = bytes([191]).decode('cp437')  # top-right
_BL  = bytes([192]).decode('cp437')  # bottom-left
_BR  = bytes([217]).decode('cp437')  # bottom-right
_H   = bytes([196]).decode('cp437')  # horizontal
_V   = bytes([179]).decode('cp437')  # vertical
_ARR_UP   = bytes([30]).decode('cp437')   # arrow up
_ARR_DOWN = bytes([31]).decode('cp437')   # arrow down
_THUMB    = bytes([219]).decode('cp437')  # scroll thumb
_TRACK    = bytes([176]).decode('cp437')  # scroll track


# ---------------------------------------------------------------------------
# Config accessors
# ---------------------------------------------------------------------------

def _files_dir():
  """Return the file library directory, creating it if needed."""
  d = paths.resolve_project(str(config.files_dir) if config.files_dir else "files")
  os.makedirs(d, exist_ok=True)
  return d


def _meta_path():
  """Return the path to the metadata YAML file."""
  p = str(config.files_meta) if config.files_meta else os.path.join(_files_dir(), "meta.yaml")
  return paths.resolve_project(p)


def _valid_keys():
  """Return the list of sysop-defined valid file keys."""
  keys = config.file_tags
  if keys and keys is not null:
    return list(keys)
  return []


# ---------------------------------------------------------------------------
# Metadata I/O
# ---------------------------------------------------------------------------

def _load_meta():
  """Load metadata from the YAML file. Returns a dict of filename -> {keys, description}."""
  path = _meta_path()
  if os.path.isfile(path):
    try:
      with open(path, 'r', encoding='utf-8') as f:
        data = _yaml.load(f)
      if isinstance(data, dict):
        return data
    except Exception as exc:
      log.warning("Failed to load file metadata from %s: %s", path, exc)
  return {}


def _save_meta(meta):
  """Save metadata dict to the YAML file."""
  path = _meta_path()
  os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
  try:
    with open(path, 'w', encoding='utf-8') as f:
      _yaml.dump(meta, f)
  except Exception as exc:
    log.error("Failed to save file metadata to %s: %s", path, exc)


# ---------------------------------------------------------------------------
# File listing helpers
# ---------------------------------------------------------------------------

def _format_size(size):
  """Human-readable file size string, right-justified to 10 chars."""
  if size < 1024:
    return f"{size} B"
  elif size < 1024 * 1024:
    return f"{size // 1024} KB"
  else:
    return f"{size // (1024 * 1024)} MB"


def _get_all_files():
  """Return a list of (filename, size, keys, description) for every file on disk.

  Files present on disk but missing from meta.yaml get empty keys and no description.
  """
  files_dir = _files_dir()
  meta = _load_meta()
  result = []
  if not os.path.isdir(files_dir):
    return result

  for name in sorted(os.listdir(files_dir)):
    path = os.path.join(files_dir, name)
    if not os.path.isfile(path):
      continue
    # Skip the metadata file itself if it lives inside files_dir
    if os.path.abspath(path) == os.path.abspath(_meta_path()):
      continue
    size = os.path.getsize(path)
    entry = meta.get(name, {})
    if not isinstance(entry, dict):
      entry = {}
    keys = entry.get('keys', []) or []
    desc = entry.get('description', '') or ''
    result.append((name, size, list(keys), str(desc)))
  return result


def _filter_files(files, include_keys, exclude_keys):
  """Filter a files list by include/exclude key sets.

  include_keys: file must have ALL of these keys (empty = no filter).
  exclude_keys: file must have NONE of these keys (empty = no filter).
  """
  result = []
  for fname, size, keys, desc in files:
    key_set = set(keys)
    if include_keys and not include_keys.issubset(key_set):
      continue
    if exclude_keys and exclude_keys.intersection(key_set):
      continue
    result.append((fname, size, keys, desc))
  return result


# ---------------------------------------------------------------------------
# Scrollable file list display
# ---------------------------------------------------------------------------

async def _show_file_list(user, files_with_meta, title):
  """Display files in a scrollable full-screen list.

  files_with_meta: list of (filename, size, keys, description) tuples.
  Returns the selected filename (str) or None if user pressed Q.
  """
  if not files_with_meta:
    await show_message_box(user, "No files found.")
    return None

  # Layout constants
  header_rows = 3   # title line + column header + separator
  footer_rows = 2   # separator + controls line
  list_height = user.screen_height - header_rows - footer_rows
  if list_height < 1:
    list_height = 1

  total = len(files_with_meta)
  scroll_offset = 0
  selected = 0  # cursor index into files_with_meta

  # Pre-format lines
  num_width = len(str(total))
  avail_width = user.screen_width - 2  # left margin

  def _build_line(idx):
    fname, size, keys, desc = files_with_meta[idx]
    num_str = f"{idx + 1:>{num_width}}."
    size_str = _format_size(size)
    key_str = "[" + ", ".join(keys) + "]" if keys else ""
    # Truncate description to fit
    fixed = len(num_str) + 1 + len(size_str) + 2
    if key_str:
      fixed += len(key_str) + 1
    max_fname = max(10, avail_width - fixed - len(desc) - 2)
    if len(fname) > max_fname:
      fname = fname[:max_fname - 1] + "~"
    max_desc = avail_width - len(num_str) - 1 - len(fname) - 2 - len(size_str) - 2 - (len(key_str) + 1 if key_str else 0)
    if max_desc < 0:
      max_desc = 0
    d = desc[:max_desc] if len(desc) > max_desc else desc
    return num_str, fname, size_str, key_str, d

  async def _draw():
    # Clear screen
    await ansi_cls(user)

    ansi_wrap(user, False)

    # Title
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await ansi_move_deferred(user, row=1, col=1, drain=False)
    padded_title = title[:user.screen_width].center(user.screen_width)
    await send(user, padded_title, drain=False)

    # Column header
    ansi_color(user, fg=white, fg_br=True, bg=black)
    await ansi_move_deferred(user, row=2, col=1, drain=False)
    hdr = f"  {'#':>{num_width}}  {'Filename':<20} {'Size':>10}  {'Keys':<16} Description"
    await send(user, hdr[:user.screen_width].ljust(user.screen_width), drain=False)

    # Separator
    ansi_color(user, fg=green, fg_br=False, bg=black)
    await ansi_move_deferred(user, row=3, col=1, drain=False)
    await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

    # File lines
    for i in range(list_height):
      file_idx = scroll_offset + i
      row = header_rows + i + 1
      await ansi_move_deferred(user, row=row, col=1, drain=False)

      if file_idx >= total:
        ansi_color(user, fg=white, fg_br=False, bg=black)
        await send(user, " " * user.screen_width, drain=False)
        continue

      num_str, fname, size_str, key_str, desc = _build_line(file_idx)
      is_selected = (file_idx == selected)

      # Number
      if is_selected:
        ansi_color(user, fg=white, fg_br=True, bg=blue)
      else:
        ansi_color(user, fg=white, fg_br=False, bg=black)

      line_parts = []

      # Build the line as a single padded string for background highlighting
      line_text = f"  {num_str} {fname:<20} {size_str:>10}"
      if key_str:
        line_text += f"  {key_str}"
      if desc:
        line_text += f"  {desc}"

      padded = line_text[:user.screen_width].ljust(user.screen_width)

      if is_selected:
        # Highlight entire line
        ansi_color(user, fg=white, fg_br=True, bg=blue)
        await send(user, padded, drain=False)
      else:
        # Build with color segments
        # Number + filename in normal
        seg1 = f"  {num_str} {fname:<20} {size_str:>10}"
        ansi_color(user, fg=white, fg_br=False, bg=black)
        await send(user, seg1, drain=False)
        # Keys in cyan
        if key_str:
          ansi_color(user, fg=cyan, fg_br=False, bg=black)
          await send(user, f"  {key_str}", drain=False)
        # Description in normal
        if desc:
          ansi_color(user, fg=white, fg_br=False, bg=black)
          await send(user, f"  {desc}", drain=False)
        # Pad rest
        used = len(seg1) + (len(f"  {key_str}") if key_str else 0) + (len(f"  {desc}") if desc else 0)
        remaining = user.screen_width - used
        if remaining > 0:
          ansi_color(user, fg=white, fg_br=False, bg=black)
          await send(user, " " * remaining, drain=False)

    # Bottom separator
    sep_row = header_rows + list_height + 1
    ansi_color(user, fg=green, fg_br=False, bg=black)
    await ansi_move_deferred(user, row=sep_row, col=1, drain=False)
    await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

    # Controls
    ctrl_row = sep_row + 1
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await ansi_move_deferred(user, row=ctrl_row, col=1, drain=False)
    ctrl_text = " Up/Down: scroll  PgUp/PgDn: page  Enter/#: download  Q: back"
    await send(user, ctrl_text[:user.screen_width].ljust(user.screen_width), drain=False)

    ansi_wrap(user, True)
    await user.writer.drain()

  # Initial draw
  await _draw()

  # Input loop
  while True:
    key = await get_input_key(user)

    if key == up:
      if selected > 0:
        selected -= 1
        if selected < scroll_offset:
          scroll_offset = selected
        await _draw()
    elif key == down:
      if selected < total - 1:
        selected += 1
        if selected >= scroll_offset + list_height:
          scroll_offset = selected - list_height + 1
        await _draw()
    elif key == pgup:
      selected = max(0, selected - list_height)
      if selected < scroll_offset:
        scroll_offset = selected
      await _draw()
    elif key == pgdn:
      selected = min(total - 1, selected + list_height)
      if selected >= scroll_offset + list_height:
        scroll_offset = selected - list_height + 1
      await _draw()
    elif key == home:
      selected = 0
      scroll_offset = 0
      await _draw()
    elif key == end:
      selected = total - 1
      scroll_offset = max(0, total - list_height)
      await _draw()
    elif key == "\r" or key == "\x0d":
      return files_with_meta[selected][0]
    elif isinstance(key, str) and key.lower() == "q":
      return None
    elif isinstance(key, str) and key.isdigit():
      # Accumulate multi-digit number entry
      num_str = key
      # Give a brief moment for more digits (simple approach: just use single digit for now)
      # Actually, for multi-digit: read characters until a non-digit or timeout
      try:
        idx = int(num_str) - 1
        if 0 <= idx < total:
          return files_with_meta[idx][0]
      except (ValueError, TypeError):
        pass


# ---------------------------------------------------------------------------
# Protocol chooser
# ---------------------------------------------------------------------------

async def _choose_protocol(user):
  """Let the user choose a transfer protocol. Returns protocol name or None."""
  protocols = get_available_protocols()
  available = [p for p, ok in protocols.items() if ok]
  if not available:
    await show_message_box(user, "No file transfer protocols are available on this system.")
    return None

  ansi_color(user, fg=cyan, fg_br=True, bg=black)
  await send(user, cr + lf + "Select transfer protocol:" + cr + lf, drain=False)
  ansi_color(user, fg=white, fg_br=False, bg=black)
  for i, name in enumerate(available, 1):
    await send(user, f"  {i}. {name.upper()}" + cr + lf, drain=False)
  await send(user, cr + lf + "Choice: ", drain=True)

  key = await get_input_key(user)
  try:
    idx = int(key) - 1
    if 0 <= idx < len(available):
      return available[idx]
  except (ValueError, TypeError):
    pass
  return available[0]


# ---------------------------------------------------------------------------
# Transfer helpers
# ---------------------------------------------------------------------------

async def _do_download(user, filename):
  """Download a single file to the user."""
  file_path = os.path.join(_files_dir(), filename)
  if not os.path.isfile(file_path):
    await show_message_box(user, f"File not found: {filename}")
    return

  protocol = await _choose_protocol(user)
  if not protocol:
    return

  log.info("User %s downloading %s via %s", user.handle, filename, protocol)
  await send(user, cr + lf + f"Sending {filename} via {protocol.upper()}..." + cr + lf, drain=True)

  if protocol == "zmodem":
    result = await send_file_zmodem(user, file_path)
  elif protocol == "ymodem":
    result = await send_file_ymodem(user, file_path)
  else:
    result = RetVals(status=fail, message="Unknown protocol")

  if result.status == success:
    log.info("Download complete: %s for %s", filename, user.handle)
    await show_message_box(user, f"Transfer of {filename} complete!")
  else:
    msg = getattr(result, 'message', 'Unknown error')
    log.warning("Download failed: %s for %s: %s", filename, user.handle, msg)
    await show_message_box(user, f"Transfer failed: {msg}")


# ---------------------------------------------------------------------------
# Search mode (S)
# ---------------------------------------------------------------------------

async def _search_files(user):
  """Prompt for include/exclude keys and display matching files."""
  all_files = _get_all_files()
  valid = _valid_keys()

  # Clear screen for prompts
  await ansi_cls(user)

  ansi_color(user, fg=cyan, fg_br=True, bg=black)
  await send(user, "Search Files by Keys" + cr + lf, drain=False)
  ansi_color(user, fg=white, fg_br=False, bg=black)

  if valid:
    await send(user, cr + lf + "Available keys: " + ", ".join(valid) + cr + lf, drain=False)

  await send(user, cr + lf + "Include keys (comma-separated, or blank for all): ", drain=True)

  # Read include keys (simple line input via get_input_key)
  inc_str = await _read_line(user, max_len=200)
  include_keys = set()
  if inc_str.strip():
    for k in inc_str.split(","):
      k = k.strip().lower()
      if k:
        include_keys.add(k)

  await send(user, cr + lf + "Exclude keys (comma-separated, or blank): ", drain=True)
  exc_str = await _read_line(user, max_len=200)
  exclude_keys = set()
  if exc_str.strip():
    for k in exc_str.split(","):
      k = k.strip().lower()
      if k:
        exclude_keys.add(k)

  filtered = _filter_files(all_files, include_keys, exclude_keys)
  title = "Search Results"
  if include_keys:
    title += f" [+{','.join(sorted(include_keys))}]"
  if exclude_keys:
    title += f" [-{','.join(sorted(exclude_keys))}]"

  chosen = await _show_file_list(user, filtered, title)
  if chosen:
    await _do_download(user, chosen)


# ---------------------------------------------------------------------------
# Hierarchy/Browse mode (B)
# ---------------------------------------------------------------------------

async def _browse_files(user):
  """Virtual directory tree built from file keys. Navigate with arrow keys and Enter."""
  path_keys = []  # current "directory" path as a list of keys

  while True:
    all_files = _get_all_files()

    # Files matching all path_keys
    path_set = set(path_keys)
    matching = [(f, s, k, d) for f, s, k, d in all_files if path_set.issubset(set(k))]

    # Subdirectories: remaining keys that any matching file has, excluding path_keys
    sub_keys = {}
    for fname, size, keys, desc in matching:
      for k in keys:
        if k not in path_set:
          if k not in sub_keys:
            sub_keys[k] = 0
          sub_keys[k] += 1

    sub_list = sorted(sub_keys.items(), key=lambda x: x[0])

    # Build a unified list of items: ("dir", key, count) or ("file", fname, size, keys, desc)
    items = []
    if path_keys:
      items.append(("parent", "..", 0))
    for key, count in sub_list:
      items.append(("dir", key, count))
    for fname, size, keys, desc in matching:
      items.append(("file", fname, size, keys, desc))

    if not items:
      await show_message_box(user, "No files or subdirectories here.")
      break

    # Layout
    header_rows = 2   # path + separator
    footer_rows = 2   # separator + controls
    list_height = user.screen_height - header_rows - footer_rows
    if list_height < 1:
      list_height = 1

    total = len(items)
    scroll_offset = 0
    selected = 0

    async def _draw():
      await ansi_cls(user)
      ansi_wrap(user, False)

      # Header
      path_str = "/" + "/".join(path_keys) + "/" if path_keys else "/"
      ansi_color(user, fg=cyan, fg_br=True, bg=black)
      await ansi_move_deferred(user, row=1, col=1, drain=False)
      await send(user, f"Browse: {path_str}".ljust(user.screen_width), drain=False)

      ansi_color(user, fg=green, fg_br=False, bg=black)
      await ansi_move_deferred(user, row=2, col=1, drain=False)
      await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

      # Items
      for i in range(list_height):
        item_idx = scroll_offset + i
        row = header_rows + i + 1
        await ansi_move_deferred(user, row=row, col=1, drain=False)

        if item_idx >= total:
          ansi_color(user, fg=white, fg_br=False, bg=black)
          await send(user, " " * user.screen_width, drain=False)
          continue

        item = items[item_idx]
        is_sel = (item_idx == selected)

        if item[0] == "parent":
          if is_sel:
            ansi_color(user, fg=white, fg_br=True, bg=blue)
          else:
            ansi_color(user, fg=cyan, fg_br=True, bg=black)
          line = "  ../ (up one level)"
          await send(user, line[:user.screen_width].ljust(user.screen_width), drain=False)

        elif item[0] == "dir":
          key, count = item[1], item[2]
          if is_sel:
            ansi_color(user, fg=white, fg_br=True, bg=blue)
            line = f"  {key}/ ({count} file{'s' if count != 1 else ''})"
            await send(user, line[:user.screen_width].ljust(user.screen_width), drain=False)
          else:
            ansi_color(user, fg=cyan, fg_br=True, bg=black)
            await send(user, f"  {key}/", drain=False)
            ansi_color(user, fg=white, fg_br=False, bg=black)
            rest = f" ({count} file{'s' if count != 1 else ''})"
            await send(user, rest, drain=False)
            used = 2 + len(key) + 1 + len(rest)
            if used < user.screen_width:
              await send(user, " " * (user.screen_width - used), drain=False)

        elif item[0] == "file":
          fname, size, keys, desc = item[1], item[2], item[3], item[4]
          size_str = _format_size(size)
          key_str = "[" + ", ".join(keys) + "]" if keys else ""
          if is_sel:
            ansi_color(user, fg=white, fg_br=True, bg=blue)
            line = f"  {fname:<20} {size_str:>10}"
            if key_str:
              line += f"  {key_str}"
            if desc:
              line += f"  {desc}"
            await send(user, line[:user.screen_width].ljust(user.screen_width), drain=False)
          else:
            ansi_color(user, fg=white, fg_br=False, bg=black)
            seg1 = f"  {fname:<20} {size_str:>10}"
            await send(user, seg1, drain=False)
            used = len(seg1)
            if key_str:
              ansi_color(user, fg=cyan, fg_br=False, bg=black)
              await send(user, f"  {key_str}", drain=False)
              used += 2 + len(key_str)
            if desc:
              ansi_color(user, fg=white, fg_br=False, bg=black)
              await send(user, f"  {desc}", drain=False)
              used += 2 + len(desc)
            if used < user.screen_width:
              ansi_color(user, fg=white, fg_br=False, bg=black)
              await send(user, " " * (user.screen_width - used), drain=False)

      # Footer
      sep_row = header_rows + list_height + 1
      ansi_color(user, fg=green, fg_br=False, bg=black)
      await ansi_move_deferred(user, row=sep_row, col=1, drain=False)
      await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

      ctrl_row = sep_row + 1
      ansi_color(user, fg=cyan, fg_br=True, bg=black)
      await ansi_move_deferred(user, row=ctrl_row, col=1, drain=False)
      ctrl = " Up/Down: navigate  Enter: open/download  Backspace: up  Q: quit"
      await send(user, ctrl[:user.screen_width].ljust(user.screen_width), drain=False)

      ansi_wrap(user, True)
      await user.writer.drain()

    await _draw()

    # Input loop
    redraw_needed = False
    while True:
      key = await get_input_key(user)

      if key == up:
        if selected > 0:
          selected -= 1
          if selected < scroll_offset:
            scroll_offset = selected
          await _draw()
      elif key == down:
        if selected < total - 1:
          selected += 1
          if selected >= scroll_offset + list_height:
            scroll_offset = selected - list_height + 1
          await _draw()
      elif key == pgup:
        selected = max(0, selected - list_height)
        if selected < scroll_offset:
          scroll_offset = selected
        await _draw()
      elif key == pgdn:
        selected = min(total - 1, selected + list_height)
        if selected >= scroll_offset + list_height:
          scroll_offset = selected - list_height + 1
        await _draw()
      elif key == home:
        selected = 0
        scroll_offset = 0
        await _draw()
      elif key == end:
        selected = total - 1
        scroll_offset = max(0, total - list_height)
        await _draw()
      elif key == "\r" or key == "\x0d":
        item = items[selected]
        if item[0] == "parent":
          path_keys.pop()
          redraw_needed = True
          break
        elif item[0] == "dir":
          path_keys.append(item[1])
          redraw_needed = True
          break
        elif item[0] == "file":
          await _do_download(user, item[1])
          redraw_needed = True
          break
      elif key == back or key == "esc":
        if path_keys:
          path_keys.pop()
          redraw_needed = True
          break
        else:
          return  # at root, exit browse
      elif isinstance(key, str) and key.lower() == "q":
        return

    if not redraw_needed:
      break


# ---------------------------------------------------------------------------
# List all files (L)
# ---------------------------------------------------------------------------

async def _list_all_files(user):
  """Show all files in a scrollable list."""
  files = _get_all_files()
  chosen = await _show_file_list(user, files, "All Files")
  if chosen:
    await _do_download(user, chosen)


# ---------------------------------------------------------------------------
# Download (D)
# ---------------------------------------------------------------------------

async def _download_file(user):
  """Prompt for a filename and download it."""
  await ansi_cls(user)

  ansi_color(user, fg=cyan, fg_br=True, bg=black)
  await send(user, "Download a File" + cr + lf, drain=False)
  ansi_color(user, fg=white, fg_br=False, bg=black)
  await send(user, cr + lf + "Enter filename (or Q to cancel): ", drain=True)

  name = await _read_line(user, max_len=200)
  name = name.strip()
  if not name or name.lower() == "q":
    return

  # Check if it's a valid file
  file_path = os.path.join(_files_dir(), name)
  if not os.path.isfile(file_path):
    await show_message_box(user, f"File not found: {name}")
    return

  await _do_download(user, name)


# ---------------------------------------------------------------------------
# Upload (U)
# ---------------------------------------------------------------------------

async def _upload_file(user):
  """Receive a file, then prompt for description and keys."""
  protocol = await _choose_protocol(user)
  if not protocol:
    return

  save_dir = _files_dir()
  log.info("User %s uploading via %s", user.handle, protocol)
  await send(user, cr + lf + f"Ready to receive via {protocol.upper()}. Start your transfer now." + cr + lf, drain=True)

  if protocol == "zmodem":
    result = await recv_file_zmodem(user, save_dir)
  elif protocol == "ymodem":
    result = await recv_file_ymodem(user, save_dir)
  else:
    result = RetVals(status=fail, message="Unknown protocol")

  if result.status != success:
    msg = getattr(result, 'message', 'Unknown error')
    log.warning("Upload failed for %s: %s", user.handle, msg)
    await show_message_box(user, f"Upload failed: {msg}")
    return

  received_msg = getattr(result, 'message', 'Transfer complete')
  log.info("Upload complete for %s: %s", user.handle, received_msg)

  await send(user, cr + lf + f"Upload complete! {received_msg}" + cr + lf, drain=True)

  # Figure out which file was received (the newest file in the directory)
  # We look for files that weren't in meta before
  meta = _load_meta()
  new_files = []
  for name in sorted(os.listdir(save_dir)):
    path = os.path.join(save_dir, name)
    if os.path.isfile(path) and os.path.abspath(path) != os.path.abspath(_meta_path()):
      if name not in meta:
        new_files.append(name)

  if not new_files:
    # Fallback: just ask for the filename
    await send(user, cr + lf + "Enter the filename of the uploaded file: ", drain=True)
    fname = await _read_line(user, max_len=200)
    fname = fname.strip()
    if not fname:
      return
    new_files = [fname]

  for fname in new_files:
    await send(user, cr + lf + f"Cataloguing: {fname}" + cr + lf, drain=False)

    # Description
    await send(user, "Enter description (or blank for none): ", drain=True)
    desc = await _read_line(user, max_len=200)
    desc = desc.strip()

    # Key assignment
    valid = _valid_keys()
    assigned_keys = []
    if valid:
      await send(user, cr + lf + "Available keys:" + cr + lf, drain=False)
      ansi_color(user, fg=cyan, fg_br=False, bg=black)
      for i, k in enumerate(valid, 1):
        await send(user, f"  {i:3}. {k}" + cr + lf, drain=False)
      ansi_color(user, fg=white, fg_br=False, bg=black)
      await send(user, cr + lf + "Enter key numbers (comma-separated, or blank for none): ", drain=True)
      key_input = await _read_line(user, max_len=200)
      if key_input.strip():
        for part in key_input.split(","):
          part = part.strip()
          try:
            idx = int(part) - 1
            if 0 <= idx < len(valid) and valid[idx] not in assigned_keys:
              assigned_keys.append(valid[idx])
          except (ValueError, TypeError):
            # Try matching by name
            part_lower = part.lower()
            for vk in valid:
              if vk.lower() == part_lower and vk not in assigned_keys:
                assigned_keys.append(vk)

    # Save to meta
    meta[fname] = {
      'keys': assigned_keys,
      'description': desc,
    }
    _save_meta(meta)
    log.info("User %s uploaded %s with keys=%s", user.handle, fname, assigned_keys)

  await show_message_box(user, "File(s) catalogued successfully.")


# ---------------------------------------------------------------------------
# Simple line input helper
# ---------------------------------------------------------------------------

async def _read_line(user, max_len=200):
  """Read a line of text from the user using get_input_key, echoing characters.

  Returns the entered string (without trailing CR/LF).
  """
  buf = []
  while True:
    key = await get_input_key(user)
    if key == "\r" or key == "\x0d" or key == "\x0a":
      break
    elif key == "\x08" or key == "\x7f":  # backspace / delete
      if buf:
        buf.pop()
        await send(user, "\x08 \x08", drain=True)
    elif isinstance(key, str) and len(key) == 1 and ord(key) >= 32:
      if len(buf) < max_len:
        buf.append(key)
        await send(user, key, drain=True)
  return "".join(buf)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def run(user, destination, menu_item=None):
  from common import Destinations

  # Determine which action to run from the menu_item
  action = None
  if menu_item and menu_item is not None:
    if isinstance(menu_item, str):
      # Look up the option config to get the action
      menu_conf = config.menu_system.files
      if menu_conf and menu_conf.options:
        opt = menu_conf.options[menu_item]
        if opt and hasattr(opt, 'action') and opt.action:
          action = str(opt.action).lower()
      if not action:
        action = menu_item.lower()
    elif hasattr(menu_item, 'action') and menu_item.action:
      action = str(menu_item.action).lower()

  try:
    if action == "search":
      await _search_files(user)
    elif action == "browse":
      await _browse_files(user)
    elif action == "list":
      await _list_all_files(user)
    elif action == "download":
      await _download_file(user)
    elif action == "upload":
      await _upload_file(user)
  except Disconnected:
    log.info("User disconnected from File Library")

  return RetVals(status=success, next_destination=Destinations.files, next_menu_item=null)
