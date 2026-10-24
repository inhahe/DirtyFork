"""
File Library: search, browse, list, download and upload files (ZMODEM or YMODEM-G).

What the library lists is in its catalogue (library.py): uploads, which live
in the library folder (files_dir), and the files library_sync.py lists,
which are zips it makes or files linked where they are (H:, a picture
gallery, ...). Callers are sent only files the catalogue lists, from inside
their roots (library.resolve).

Uploads by holders of the upload key (file_library.upload_key, and sysops)
are listed at once. Anyone else's wait in the pending folder, listed to no
one, until a sysop approves (moves it into the library) or rejects (deletes)
it in Sysop > Vet Uploads; online sysops get a popup when one arrives, and
a sysop logging in is told how many are waiting.

Valid tags for uploads are config.file_tags. Searching uses the language in
library.QUERY_HELP.
"""

import asyncio
import os
import sqlite3
import time

from definitions import (RetVals, Disconnected, success,
                         cr, lf, null,
                         white, black, green, cyan, red, blue)
from input_output import send, ansi_color, ansi_move, ansi_move_deferred, ansi_wrap, ansi_cls, get_input_key
from input_fields import show_message_box, InputField, InputFields
from file_transfer import (send_files_zmodem, receive_files_zmodem,
                           send_files_ymodem, receive_files_ymodem,
                           get_available_protocols, parse_size, UploadPolicy, TEMP_PREFIX)
import file_transfer
import library
from keyboard_codes import up, down, pgup, pgdn, home, end, back
from config import get_config
from logger import log

config = get_config()

_H = bytes([196]).decode('cp437')  # horizontal line


# ---------------------------------------------------------------------------
# The catalogue
# ---------------------------------------------------------------------------

_lib = None


def _library():
  """The library's settings (library.Library), read from the config once."""
  global _lib
  if _lib is None:
    _lib = library.from_config(config)
  return _lib


async def _db(work, *args):
  """work(connection, *args) in a thread, on a connection of its own, so a
  search over millions of files never holds up other callers."""
  lib = _library()

  def run():
    con = library.connect(lib)
    try:
      return work(con, *args)
    finally:
      con.close()
  return await asyncio.to_thread(run)


def startup():
  """At BBS startup: create the catalogue if need be, delete what uploads
  cut short by a crash left behind (later, it could be an upload in
  progress), catalogue what is in the library folders without being
  catalogued (library.reconcile_uploads), and take what an old meta.yaml
  catalogue said of those files (library.read_legacy_meta: retired only
  once applied, so a start that fails meanwhile tries again)."""
  lib = _library()
  library.ensure_schema(lib)
  for folder in (lib.files_dir, lib.pending_dir):
    file_transfer.remove_stale_uploads(folder)
  legacy = library.read_legacy_meta(lib)  # (meta.yaml, from before the catalogue)
  con = library.connect(lib)
  try:
    added, forgotten = library.reconcile_uploads(lib, con, TEMP_PREFIX)
    if legacy:
      log.info("File library: took the tags and descriptions of %d file(s) from %s",
               library.apply_legacy_meta(con, legacy), lib.legacy_meta)
      library.retire_legacy_meta(lib, TEMP_PREFIX)
  except sqlite3.OperationalError as exc:  # (a sync holding the catalogue: it reconciles too)
    log.warning("File library: could not check its folders against the catalogue: %s", exc)
    return
  finally:
    con.close()
  if added or forgotten:
    log.info("File library: catalogued %d file(s) found in its folders, forgot %d gone", added, forgotten)


def _valid_tags():
  """The sysop-defined tags an uploader may choose from."""
  tags = config.file_tags
  if tags and tags is not null:
    return [str(t) for t in tags]
  return []


def _is_sysop(user):
  return 'sysop' in getattr(user, 'keys', ())


def _trusted(user):
  """True when the user's uploads are listed without the sysop's approval."""
  keys = getattr(user, 'keys', ())
  return 'sysop' in keys or _library().upload_key in keys


# ---------------------------------------------------------------------------
# Showing files
# ---------------------------------------------------------------------------

def _format_size(size):
  """A short size, at most 7 characters: 512 B, 37 KB, 12 MB, 3.4 GB, 120 GB."""
  if size < 1024:
    return f"{size} B"
  if size < 1024 * 1024:
    return f"{size // 1024} KB"
  if size < 1024 ** 3:
    return f"{size // (1024 * 1024)} MB"
  if size < 10 * 1024 ** 3:
    return f"{size / 1024 ** 3:.1f} GB"
  if size < 1024 ** 4:
    return f"{size // 1024 ** 3} GB"
  if size < 10 * 1024 ** 4:
    return f"{size / 1024 ** 4:.1f} TB"
  return f"{size // 1024 ** 4} TB"  # (never more than the 7 columns lists give it, below a petabyte)


def _fit(text, width):
  """*text* in at most *width* columns: its middle replaced by ~ if too long
  (a file's name keeps its start and its extension)."""
  if len(text) <= width:
    return text
  if width < 4:
    return text[:width]
  head = (width - 1) * 2 // 3
  return text[:head] + "~" + text[len(text) - (width - 1 - head):]


def _tag_text(tags):
  return "".join(f"[{t}]" for t in tags)


def _file_line(entry, number, num_width, name_width, width):
  """A list's line for *entry*: number, name (padded to *name_width*), size,
  tags and description, cut to *width*."""
  text = f"  {number:>{num_width}}. {_fit(entry.name, name_width):<{name_width}} {_format_size(entry.size):>7}"
  if entry.tags:
    text += "  " + _tag_text(entry.tags)
  if entry.description:
    text += "  " + " ".join(entry.description.split())
  return text[:width]


def _info_text(entry):
  """Everything the catalogue knows about a file, for its info popup."""
  lines = [f"Name: {entry.name}",
           f"Size: {entry.size:,} bytes ({_format_size(entry.size)})"]
  if entry.tags:
    lines.append("Tags: " + ", ".join(entry.tags))
  lines.append(f"Uploader: {entry.uploader or '(unknown)'}")
  lines.append("Added: " + time.strftime("%Y-%m-%d %H:%M", time.localtime(entry.added)))
  if entry.pending:
    lines.append("Waiting for the sysop's approval.")
  if entry.description:
    lines += ["", entry.description]
  return "\n".join(lines)


class _Items:
  """What a list shows: maybe a parent row and directory rows (browsing),
  then files, as catalogue ids whose entries are fetched as they come on
  screen. An item is ('parent',), ('dir', tag, count), ('file', Entry), or
  ('gone', id) for a file no longer catalogued."""

  CACHE = 5000  # entries kept before the cache is emptied

  def __init__(self, ids, dirs=(), parent=False):
    self.head = ([("parent",)] if parent else []) + [("dir", tag, n) for tag, n in dirs]
    self.ids = ids
    self.cache = {}

  def __len__(self):
    return len(self.head) + len(self.ids)

  @property
  def files(self):
    return len(self.ids)

  async def load(self, start, stop):
    """Fetch the entries of items start..stop-1 that aren't fetched yet
    (when the cache is full, keeping only those of these items)."""
    first = max(start, len(self.head)) - len(self.head)
    last = min(stop, len(self)) - len(self.head)
    shown = [self.ids[i] for i in range(first, last)]
    want = [i for i in shown if i not in self.cache]
    if not want:
      return
    if len(self.cache) + len(want) > self.CACHE:
      self.cache = {i: self.cache[i] for i in shown if i in self.cache}
    for e in await _db(library.fetch, want):
      self.cache[e.id] = e
    for i in want:  # (no longer catalogued: don't ask again)
      self.cache.setdefault(i, None)

  def item(self, i):
    if i < len(self.head):
      return self.head[i]
    file_id = self.ids[i - len(self.head)]
    e = self.cache.get(file_id)
    return ("file", e) if e is not None else ("gone", file_id)

  def number(self, i):
    """The file number shown for item i (files only, from 1)."""
    return i - len(self.head) + 1

  def index_of_number(self, number):
    return len(self.head) + number - 1


async def _show_list(user, items, title, controls, selected=0):
  """Show *items* (an _Items) in a scrolling full-screen list.

  Up/Down/PgUp/PgDn/Home/End move, digits then Enter go to a file by
  number, I shows a file's details. Returns (action, item, index): action
  'open' (Enter on an item), 'back' (Backspace or Esc) or 'quit' (Q)."""
  header_rows, footer_rows = 2, 2
  height = max(1, user.screen_height - header_rows - footer_rows)
  width = user.screen_width
  total = len(items)
  num_width = len(str(max(1, items.files)))
  selected = min(max(0, selected), max(0, total - 1))
  top = max(0, min(selected - height // 2, total - height))
  number = ""  # digits typed, to go to a file by its number
  name_width = 20

  def page_name_width():
    """Names get what the page's tags and descriptions leave: all of it
    when nothing on the page has a description (samples: the name says it
    all), else at most two fifths, so descriptions show too."""
    entries = [it[1] for it in (items.item(i) for i in range(top, min(top + height, total))) if it[0] == "file"]
    if not entries:
      return 20
    room = width - (2 + num_width + 2) - 8                     # (less number and size)
    room -= max((len(_tag_text(e.tags)) + 2 for e in entries if e.tags), default=0)
    longest = max(len(e.name) for e in entries)
    if any(e.description for e in entries):
      room = min(room - 12, (width - num_width) * 2 // 5)
    return max(12, min(longest, room))

  async def draw_row(i):
    row = header_rows + 1 + (i - top)
    await ansi_move_deferred(user, row=row, col=1, drain=False)
    if i >= total:
      ansi_color(user, fg=white, fg_br=False, bg=black)
      await send(user, " " * width, drain=False)
      return
    item = items.item(i)
    chosen = i == selected
    if item[0] == "parent":
      text = "  ../  (up one level)"
    elif item[0] == "dir":
      text = f"  {item[1]}/  ({item[2]:,} file{'s' if item[2] != 1 else ''})"
    elif item[0] == "gone":
      text = f"  {items.number(i):>{num_width}}. (no longer in the library)"
    else:
      text = _file_line(item[1], items.number(i), num_width, name_width, width)
    text = text[:width].ljust(width)
    if chosen:
      ansi_color(user, fg=white, fg_br=True, bg=blue)
      await send(user, text, drain=False)
    elif item[0] in ("parent", "dir"):
      ansi_color(user, fg=cyan, fg_br=True, bg=black)
      await send(user, text, drain=False)
    elif item[0] == "file" and item[1].tags:
      # the tags in cyan: they start after the size
      entry = item[1]
      head = len(f"  {items.number(i):>{num_width}}. {'':<{name_width}} {'':>7}")
      tags = _tag_text(entry.tags)
      ansi_color(user, fg=white, fg_br=False, bg=black)
      await send(user, text[:head + 2], drain=False)
      ansi_color(user, fg=cyan, fg_br=False, bg=black)
      await send(user, text[head + 2:head + 2 + len(tags)], drain=False)
      ansi_color(user, fg=white, fg_br=False, bg=black)
      await send(user, text[head + 2 + len(tags):], drain=False)
    else:
      ansi_color(user, fg=white, fg_br=False, bg=black)
      await send(user, text, drain=False)

  async def draw_footer():
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await ansi_move_deferred(user, row=header_rows + height + 2, col=1, drain=False)
    text = f" Go to file number: {number}_   (Enter: go, Esc: cancel)" if number else controls
    await send(user, text[:width].ljust(width), drain=False)

  async def draw_rows():
    nonlocal name_width
    await items.load(top, top + height)
    name_width = page_name_width()
    ansi_wrap(user, False)
    for i in range(top, top + height):
      await draw_row(i)
    ansi_wrap(user, True)
    await user.writer.drain()

  async def draw_all():
    await items.load(top, top + height)
    await ansi_cls(user)
    ansi_wrap(user, False)
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await ansi_move_deferred(user, row=1, col=1, drain=False)
    folders = sum(1 for h in items.head if h[0] == "dir")
    counts = ([f"{folders:,} folder{'s' if folders != 1 else ''}"] if folders else []) \
      + [f"{items.files:,} file{'s' if items.files != 1 else ''}"]
    shown = f"{title}  ({', '.join(counts)})"
    await send(user, shown[:width].center(width), drain=False)
    ansi_color(user, fg=green, fg_br=False, bg=black)
    for row in (2, header_rows + height + 1):
      await ansi_move_deferred(user, row=row, col=1, drain=False)
      await send(user, _H * width, drain=False)
    await draw_footer()
    ansi_wrap(user, True)
    await draw_rows()

  async def move_to(i):
    nonlocal selected, top
    i = min(max(0, i), total - 1)
    if i == selected:
      return
    old, selected = selected, i
    if top <= selected < top + height:
      ansi_wrap(user, False)
      await draw_row(old)
      await draw_row(selected)
      ansi_wrap(user, True)
      await user.writer.drain()
      return
    top = selected if selected < top else selected - height + 1
    await draw_rows()

  if total == 0:
    await show_message_box(user, "No files here.")
    return "back", None, 0
  await draw_all()
  while True:
    key = await get_input_key(user)
    if isinstance(key, str) and len(key) == 1 and key in "0123456789":
      if len(number) < 9:  # (a tenth digit is no file: ignored, the number kept)
        number += key
      ansi_wrap(user, False)
      await draw_footer()
      ansi_wrap(user, True)
      await user.writer.drain()
      continue
    if number:
      if key in (back, "\x7f"):
        number = number[:-1]
      elif key in ("\r", "\n"):
        n, number = int(number), ""
        if 1 <= n <= items.files:
          await move_to(items.index_of_number(n))
      else:
        number = ""
      ansi_wrap(user, False)
      await draw_footer()
      ansi_wrap(user, True)
      await user.writer.drain()
      continue
    if key == up:
      await move_to(selected - 1)
    elif key == down:
      await move_to(selected + 1)
    elif key == pgup:
      await move_to(selected - height)
    elif key == pgdn:
      await move_to(selected + height)
    elif key == home:
      await move_to(0)
    elif key == end:
      await move_to(total - 1)
    elif key in ("\r", "\n"):
      return "open", items.item(selected), selected
    elif key in (back, "\x7f", "esc"):
      return "back", None, selected
    elif isinstance(key, str) and key.lower() == "q":
      return "quit", None, selected
    elif isinstance(key, str) and key.lower() == "i":
      item = items.item(selected)
      if item[0] == "file":
        await show_message_box(user, _info_text(item[1]), title="File Information")
        await draw_all()


async def _pick_files(user, items, title, selected=0):
  """A list of files where Enter downloads one; until Q or Backspace."""
  controls = " Arrows/PgUp/PgDn: move  Enter: download  I: info  Digits: go to #  Q: back"
  while True:
    action, item, selected = await _show_list(user, items, title, controls, selected)
    if action != "open":
      return action
    if item[0] == "file":
      await _do_download(user, item[1])


# ---------------------------------------------------------------------------
# Protocol chooser
# ---------------------------------------------------------------------------

def _usable_protocols(user):
  """The protocols this BBS has that the caller's terminal can run (it may
  run only some: common.detect_terminal sets user.transfer_protocols)."""
  available = [p for p, ok in get_available_protocols().items() if ok]
  terminal = getattr(user, 'transfer_protocols', None)
  return [p for p in available if terminal is None or p in terminal]


async def _transfers_refused(user):
  """True, after telling the user why, when no transfer protocol can be used.
  Check it before asking for anything a transfer needs, so they don't answer in vain."""
  if _usable_protocols(user):
    return False
  if any(get_available_protocols().values()):
    await show_message_box(user, "Your terminal can't run the file transfer protocols this BBS has "
                                 "(ZMODEM, YMODEM-G). Connect with a terminal program that can, such "
                                 "as SyncTERM, to upload or download.")
  else:
    await show_message_box(user, "No file transfer protocols are available on this system.")
  return True


async def _choose_protocol(user):
  """The transfer protocol to use: the only usable one, or the caller's
  choice. None (after saying why) when there is none."""
  if await _transfers_refused(user):
    return None
  available = _usable_protocols(user)
  if len(available) == 1:
    return available[0]

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
# Downloads
# ---------------------------------------------------------------------------

def _download_path(user, entry):
  """The path to send for *entry*, or None. Only a file inside its root
  (library.resolve); an upload awaiting approval only to a sysop."""
  return library.resolve(_library(), entry, allow_pending=_is_sysop(user))


async def _do_download(user, entry):
  """Send one catalogued file to the user."""
  file_path = _download_path(user, entry)
  if file_path is None:
    await show_message_box(user, f"File not found: {entry.name}")
    return

  protocol = await _choose_protocol(user)
  if not protocol:
    return

  log.info("User %s downloading %s (%s) via %s", user.handle, entry.name, file_path, protocol)
  send_files = send_files_zmodem if protocol == "zmodem" else send_files_ymodem
  result = await send_files(user, [file_path])

  if result.status == success:
    log.info("Download complete: %s for %s", entry.name, user.handle)
    await show_message_box(user, f"Transfer of {entry.name} complete!")
  else:
    log.warning("Download failed: %s for %s: %s", entry.name, user.handle, result.message)
    await show_message_box(user, result.message)


async def _download_file(user):
  """Download by name: ask for it; with several of that name, pick one."""
  if await _transfers_refused(user):
    return
  await ansi_cls(user)
  ansi_color(user, fg=cyan, fg_br=True, bg=black)
  await send(user, "Download a File" + cr + lf, drain=False)
  ansi_color(user, fg=white, fg_br=False, bg=black)
  await send(user, cr + lf + "Enter its name (or Q to cancel): ", drain=True)
  name = (await _read_line(user, max_len=200)).strip()
  if not name or name.lower() == "q":
    return
  ids = await _db(library.ids_named, name)  # (only names the catalogue lists: never a path)
  if not ids:
    await show_message_box(user, f"No file in the library is called {name}. Search for it instead.")
  elif len(ids) == 1:
    entries = await _db(library.fetch, ids)
    if entries:
      await _do_download(user, entries[0])
  else:
    await _pick_files(user, _Items(ids), f"Files called {name}")


# ---------------------------------------------------------------------------
# Search (S)
# ---------------------------------------------------------------------------

async def _search_form(user, query, count):
  """Ask for a search, with help and examples under the field (*count*:
  the files listed, for the title). Returns what was typed (stripped), ""
  to go back."""
  width = user.screen_width
  await ansi_cls(user)
  ansi_color(user, fg=cyan, fg_br=True, bg=black)
  await send(user, f"Search the File Library  ({count:,} files)"[:width] + cr + lf + cr + lf, drain=False)
  ansi_color(user, fg=white, fg_br=False, bg=black)
  await send(user, "Search for (Enter searches, Ctrl+U clears, empty goes back):", drain=False)

  lines = list(library.QUERY_HELP) + ["", "Examples:"] + ["  " + e for e in library.QUERY_EXAMPLES]
  first = 7
  for i, line in enumerate(lines[:max(0, user.screen_height - first)]):
    await ansi_move_deferred(user, row=first + i, col=1, drain=False)
    if line == "Examples:":
      ansi_color(user, fg=cyan, fg_br=True, bg=black)
    elif line.startswith("  "):
      ansi_color(user, fg=green, fg_br=True, bg=black)
    else:
      ansi_color(user, fg=white, fg_br=False, bg=black)
    await send(user, line[:width], drain=False)
  ansi_color(user, fg=white, fg_br=False, bg=black)

  while True:
    await ansi_move(user, 4, 2, drain=True)
    r = await InputField.create(user=user, conf=config.input_fields.input_field,
                                width=max(10, width - 3), max_length=500, content=query)
    query = r.content if hasattr(r, 'content') else str(r)
    if getattr(r, 'key', cr) == cr:
      return query.strip()


async def _search_files(user):
  """Search with the query language (library.parse_query); refine and repeat
  until an empty search."""
  query = getattr(user, 'file_search', "")
  count = await _db(library.listed_count)  # (once: it doesn't change while they search)
  while True:
    query = await _search_form(user, query, count)
    if not query:
      return
    try:
      node = library.parse_query(query)
    except library.QueryError as exc:
      await show_message_box(user, str(exc), title="Can't search for that",
                             outline_fg=red, outline_fg_br=True)
      continue
    user.file_search = query
    ids = await _db(library.search_ids, node)
    if not ids:
      await show_message_box(user, "No files match that search.")
      continue
    await _pick_files(user, _Items(ids), f"Search: {query}")  # (Q or Backspace: back to the search)


# ---------------------------------------------------------------------------
# Browse (B): the tag tree
# ---------------------------------------------------------------------------

async def _browse_files(user):
  """Tags as directories: in a directory are the further tags of its files
  (subdirectories) and the files whose tags are exactly the path; at the
  top, the untagged files. Enter opens or downloads; Backspace goes up."""
  path = []        # tags chosen so far
  selections = []  # where the selection was in each level above
  selected = 0
  controls = " Arrows: move  Enter: open/download  I: info  Backspace: up  Q: quit"
  while True:
    dirs, ids = await _db(library.browse, path)
    items = _Items(ids, dirs=dirs, parent=bool(path))
    if not len(items):
      await show_message_box(user, "The library is empty." if not path else "Nothing here.")
      if not path:
        return
      path.pop()
      selected = selections.pop()
      continue
    title = "Browse: /" + "".join(t + "/" for t in path)
    action, item, selected = await _show_list(user, items, title, controls, selected)
    if action == "quit":
      return
    if action == "back" or (action == "open" and item[0] == "parent"):
      if not path:
        return
      path.pop()
      selected = selections.pop()
    elif item[0] == "dir":
      path.append(item[1])
      selections.append(selected)
      selected = 0
    elif item[0] == "file":
      await _do_download(user, item[1])


# ---------------------------------------------------------------------------
# List all (L)
# ---------------------------------------------------------------------------

async def _list_all_files(user):
  ids = await _db(library.all_ids)
  if not ids:
    await show_message_box(user, "The library is empty.")
    return
  await _pick_files(user, _Items(ids), "All Files")


# ---------------------------------------------------------------------------
# Upload (U)
# ---------------------------------------------------------------------------

def _upload_policy(trusted):
  """What uploads may be (file_transfer.UploadPolicy): into the library
  folder for a trusted uploader, else into the pending folder, a name taken
  in neither (approving moves a file from one to the other) and none the
  library keeps for itself, within the size limits from the config
  (upload_max_size, upload_keep_free)."""
  lib = _library()
  directory, other = (lib.files_dir, lib.pending_dir) if trusted else (lib.pending_dir, lib.files_dir)
  os.makedirs(directory, exist_ok=True)
  return UploadPolicy(directory=directory, reserved=lib.reserved_names(), others=(other,),
                      max_bytes=parse_size(config.upload_max_size, 100 * 1024 * 1024),
                      keep_free=parse_size(config.upload_keep_free, 500 * 1024 * 1024))


async def _tell_sysops(text):
  """A popup for every sysop online (each as their own settings allow)."""
  from common import global_data
  from bbs_msg import send_popup
  for u in list(global_data.users.values()):
    if _is_sysop(u):
      # (work waiting for them, not a page from a caller: their paging
      # settings don't apply, as for the notice at login)
      await send_popup(u, text, title="File Library", skip_checks=True)


async def tell_sysop_of_pending(user):
  """At a sysop's login: a popup saying how many uploads await approval."""
  if not _is_sysop(user):
    return
  n = await _db(library.pending_count)
  if n:
    from bbs_msg import send_popup
    await send_popup(user, f"{n} upload{'s are' if n != 1 else ' is'} waiting for your approval "
                           "in Sysop > Vet Uploads.", title="File Library", skip_checks=True)


async def _ask_tags(user):
  """Ask for an upload's tags from config.file_tags, by number or name."""
  valid = _valid_tags()
  if not valid:
    return []
  await send(user, cr + lf + "Available tags:" + cr + lf, drain=False)
  ansi_color(user, fg=cyan, fg_br=False, bg=black)
  for i, k in enumerate(valid, 1):
    await send(user, f"  {i:3}. {k}" + cr + lf, drain=False)
  ansi_color(user, fg=white, fg_br=False, bg=black)
  await send(user, cr + lf + "Enter tag numbers or names (comma-separated, or blank for none): ", drain=True)
  chosen = []
  for part in (await _read_line(user, max_len=200)).split(","):
    part = part.strip()
    if part.isascii() and part.isdigit() and 1 <= int(part) <= len(valid):  # (not "²": int() refuses it)
      tag = valid[int(part) - 1]
    else:
      tag = next((v for v in valid if v.lower() == part.lower()), None)
    if tag and tag not in chosen:
      chosen.append(tag)
  return chosen


async def _upload_file(user):
  """Receive files, catalogue each one saved, then ask for its description
  and tags. A trusted uploader's are listed at once; anyone else's wait for
  a sysop's approval, and the sysops online are told."""
  protocol = await _choose_protocol(user)
  if not protocol:
    return

  trusted = _trusted(user)
  policy = _upload_policy(trusted)
  root = library.UPLOADS if trusted else library.PENDING
  log.info("User %s uploading via %s (%s)", user.handle, protocol, "listed at once" if trusted else "for approval")
  receive = receive_files_zmodem if protocol == "zmodem" else receive_files_ymodem
  result = await receive(user, policy)

  def catalogue(con):
    ids = {}
    for name in policy.saved:
      try:
        size, mtime = library.file_stamp(os.path.join(policy.directory, name))
      except OSError:  # (gone already: deleted by hand, or approved or rejected in a flash)
        continue
      ids[name] = library.put(con, root=root, path=name, size=size, mtime=mtime, uploader=user.handle)
    con.commit()
    return ids
  ids = await _db(catalogue) if policy.saved else {}

  lines = []
  if policy.saved:
    lines.append("Received: " + ", ".join(policy.saved) + ".")
    if not trusted:
      lines.append("They will be listed once the sysop has approved them.")
  for name, why in policy.refused:
    lines.append(f"Not kept: {name}: {why}.")
  if result.status != success:
    lines.append(result.message)
  elif not policy.saved and not policy.refused:
    lines.append("Nothing was uploaded.")
  log.info("Upload by %s: saved %s, refused %s, %s", user.handle, policy.saved, policy.refused,
           result.message)
  if not ids:
    await show_message_box(user, "\n".join(lines))
    return
  gone = []  # (rejected while the uploader typed its details)
  try:
    await show_message_box(user, "\n".join(lines))
    await ansi_cls(user)
    for fname, file_id in ids.items():
      await send(user, cr + lf + f"Cataloguing: {fname}" + cr + lf, drain=False)
      await send(user, "Enter description (or blank for none): ", drain=True)
      desc = (await _read_line(user, max_len=200)).strip()
      tags = await _ask_tags(user)

      def details(con, file_id=file_id):
        # (the sysop may have dealt with it meanwhile: approved, it is the
        # same entry in the library; rejected, it is gone)
        if con.execute("SELECT 1 FROM files WHERE id = ?", (file_id,)).fetchone() is None:
          return False
        library.set_description(con, file_id, desc)
        library.set_tags(con, file_id, tags)
        con.commit()
        return True
      if await _db(details):
        log.info("User %s uploaded %s with tags=%s", user.handle, fname, tags)
      else:
        gone.append(fname)
  finally:
    # The sysops hear of it once its details are in, or when the uploader
    # leaves without giving them.
    waiting = [n for n in ids if n not in gone]
    if not trusted and waiting:
      await _tell_sysops(f"{user.handle} uploaded {', '.join(waiting)}. "
                         "It is waiting for your approval in Sysop > Vet Uploads.")

  if not gone:
    await show_message_box(user, "File(s) catalogued successfully.")
  else:
    kept = [n for n in ids if n not in gone]
    await show_message_box(user, (f"Catalogued: {', '.join(kept)}.\n" if kept else "")
                           + f"No longer in the library (the sysop dealt with it meanwhile): {', '.join(gone)}.")


# ---------------------------------------------------------------------------
# Vetting uploads (Sysop > Vet Uploads)
# ---------------------------------------------------------------------------

async def _button_row(user, fields, buttons):
  """Add *buttons* ((name, label) pairs) to *fields* side by side, from the
  cursor's row and column 1. (Drawing a button moves the cursor: the row is
  taken once.)"""
  row, col = user.cur_row, 1
  for name, label in buttons:
    await ansi_move_deferred(user, row=row, col=col, drain=True)
    btn = await fields.add_button(name, content=label)
    col = btn.col_offset + btn.width + (1 if btn.outline else 0) + 1


async def _vet_one(user, entry):
  """Show an upload awaiting approval, and approve, reject or download it."""
  lib = _library()
  while True:
    await ansi_cls(user)
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await send(user, "Vet an Upload" + cr + lf + cr + lf, drain=False)
    ansi_color(user, fg=white, fg_br=False, bg=black)
    for line in _info_text(entry).split("\n")[:max(1, user.screen_height - 8)]:
      await send(user, line[:user.screen_width - 1] + cr + lf, drain=False)
    await send(user, cr + lf, drain=False)
    fields = InputFields(user)
    await _button_row(user, fields, (("approve", "Approve"), ("reject", "Reject"), ("download", "Download"),
                                     ("back", "Back")))
    r = await fields.run()
    if r.button == "approve":
      why = await _db(lambda con: library.approve(lib, con, entry.id, TEMP_PREFIX))
      log.info("Sysop %s approved upload %s by %s%s", user.handle, entry.name, entry.uploader,
               f": not done: {why}" if why else "")
      await show_message_box(user, why or f"{entry.name} is now in the library.")
      return
    if r.button == "reject":
      confirm = InputFields(user)
      await ansi_cls(user)
      await send(user, f"Delete {entry.name}, uploaded by {entry.uploader or '(unknown)'}?" + cr + lf + cr + lf,
                 drain=True)
      await _button_row(user, confirm, (("delete", "Delete"), ("keep", "Keep")))
      if (await confirm.run()).button == "delete":
        why = await _db(lambda con: library.reject(lib, con, entry.id))
        log.info("Sysop %s rejected upload %s by %s%s", user.handle, entry.name, entry.uploader,
                 f": not done: {why}" if why else "")
        await show_message_box(user, why or f"{entry.name} was deleted.")
        return
    elif r.button == "download":
      await _do_download(user, entry)
    else:
      return


async def vet_uploads(user):
  """The uploads awaiting approval, oldest first; Enter vets one."""
  if not _is_sysop(user):
    return
  controls = " Arrows: move  Enter: approve, reject or download  I: info  Q: back"
  selected = 0
  while True:
    ids = await _db(library.pending_ids)
    if not ids:
      await show_message_box(user, "No uploads are waiting for approval.")
      return
    action, item, selected = await _show_list(user, _Items(ids), "Uploads Awaiting Approval",
                                              controls, selected)
    if action != "open":
      return
    if item[0] == "file":
      await _vet_one(user, item[1])


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
  # Determine which action to run from the menu_item
  action = None
  if menu_item and menu_item is not None:
    # menu_item is a tuple: (option_name,)
    item_name = menu_item[0] if isinstance(menu_item, tuple) else str(menu_item)
    item_name = str(item_name)
    # Look up the option config to get the action
    menu_conf = config.menu_system.files
    if menu_conf and menu_conf.options:
      opt = menu_conf.options[item_name]
      if opt and hasattr(opt, 'action') and opt.action:
        action = str(opt.action).lower()
    if not action:
      action = item_name.lower()

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

  return RetVals(status=success, next_destination=null, next_menu_item=null)
