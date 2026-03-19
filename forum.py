"""
Forum module - browse, compose, search, and reply to forum posts.
Each forum is selected from the forums menu; this module handles
the selected forum's action loop.
"""

import json
import sqlite3
import time

from definitions import (RetVals, Disconnected, success, fail,
                         cr, lf, null,
                         white, black, green, cyan, red, blue, brown, magenta)
from input_output import send, ansi_color, ansi_move_deferred, ansi_wrap, ansi_cls, get_input_key, send_wrapped
from input_fields import InputField, InputFields, Block, show_message_box
from keyboard_codes import up, down, pgup, pgdn, home, end, back
from config import get_config
from logger import log
import paths

config = get_config()

# Box-drawing (CP437)
_H = bytes([196]).decode('cp437')

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _get_db():
  con = sqlite3.connect(paths.resolve_data(str(config.database)))
  con.row_factory = sqlite3.Row
  return con


def _get_handle_by_id(con, user_id):
  cur = con.cursor()
  cur.execute("SELECT handle FROM USERS WHERE id = ?", (user_id,))
  row = cur.fetchone()
  return row["handle"] if row else "Unknown"


def _lookup_handle(con, handle):
  from common import lookup_handle
  return lookup_handle(handle, db=con)


def _get_or_create_forum(con, forum_name):
  """Get the forum id for a given name, creating it if needed."""
  cur = con.cursor()
  cur.execute("SELECT id FROM FORUMS WHERE name = ? COLLATE NOCASE", (forum_name,))
  row = cur.fetchone()
  if row:
    return row["id"]
  cur.execute("INSERT INTO FORUMS (name) VALUES (?)", (forum_name,))
  con.commit()
  return cur.lastrowid


def _blocks_to_json(blocks):
  return json.dumps([{"text": b.text, "level": b.level} for b in blocks])


def _json_to_blocks(json_str):
  try:
    data = json.loads(json_str)
    return [Block(text=item["text"], level=item["level"]) for item in data]
  except (json.JSONDecodeError, KeyError, TypeError):
    return [Block(text=json_str or "", level=0)]


def _format_time(timestamp):
  if not timestamp:
    return ""
  return time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))


# ---------------------------------------------------------------------------
# Post list (scrollable, shared by "new" and "search")
# ---------------------------------------------------------------------------

async def _show_post_list(user, posts, title):
  """Display forum posts in a scrollable list.
  posts: list of dicts with keys: id, from_handle, subject, time_created, is_read, reply_to
  Returns the selected post dict, or None if user pressed Q.
  """
  if not posts:
    await show_message_box(user, "No posts found.")
    return None

  header_rows = 3
  footer_rows = 2
  list_height = user.screen_height - header_rows - footer_rows
  if list_height < 1:
    list_height = 1

  total = len(posts)
  scroll_offset = 0
  selected = 0

  reply_marker = bytes([175]).decode('cp437')  # >> marker for replies

  async def _draw():
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
    hdr = "  Status  Date              From             Subject"
    await send(user, hdr[:user.screen_width].ljust(user.screen_width), drain=False)

    # Separator
    ansi_color(user, fg=green, fg_br=False, bg=black)
    await ansi_move_deferred(user, row=3, col=1, drain=False)
    await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

    # Post lines
    for i in range(list_height):
      post_idx = scroll_offset + i
      row = header_rows + i + 1
      await ansi_move_deferred(user, row=row, col=1, drain=False)

      if post_idx >= total:
        ansi_color(user, fg=white, fg_br=False, bg=black)
        await send(user, " " * user.screen_width, drain=False)
        continue

      post = posts[post_idx]
      is_selected = (post_idx == selected)
      is_unread = not post["is_read"]

      status = "[NEW]" if is_unread else "[   ]"
      date_str = _format_time(post["time_created"])
      from_handle = post["from_handle"][:15]
      subj = post.get("subject", "") or ""
      if post.get("reply_to"):
        subj = reply_marker + " " + subj

      line_text = f"  {status}  {date_str:<17} {from_handle:<16} {subj}"
      padded = line_text[:user.screen_width].ljust(user.screen_width)

      if is_selected:
        ansi_color(user, fg=white, fg_br=True, bg=blue)
        await send(user, padded, drain=False)
      else:
        if is_unread:
          ansi_color(user, fg=white, fg_br=True, bg=black)
        else:
          ansi_color(user, fg=white, fg_br=False, bg=black)
        await send(user, padded, drain=False)

    # Bottom separator
    sep_row = header_rows + list_height + 1
    ansi_color(user, fg=green, fg_br=False, bg=black)
    await ansi_move_deferred(user, row=sep_row, col=1, drain=False)
    await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

    # Controls
    ctrl_row = sep_row + 1
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await ansi_move_deferred(user, row=ctrl_row, col=1, drain=False)
    ctrl_text = " Up/Down: navigate  PgUp/PgDn: page  Enter: read  Q: back"
    await send(user, ctrl_text[:user.screen_width].ljust(user.screen_width), drain=False)

    ansi_wrap(user, True)
    await user.writer.drain()

  await _draw()

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
      return posts[selected]
    elif isinstance(key, str) and key.lower() == "q":
      return None


# ---------------------------------------------------------------------------
# Read view
# ---------------------------------------------------------------------------

async def _read_post(user, post, posts, post_index, con, forum_id):
  """Show a single forum post. Supports reply, next, prev, back."""
  while True:
    cur_post = posts[post_index] if 0 <= post_index < len(posts) else None
    if cur_post is None:
      return ("back", post_index)

    post = cur_post

    # Mark as read
    if not post["is_read"]:
      db_cur = con.cursor()
      db_cur.execute(
        "INSERT OR IGNORE INTO FORUM_MESSAGES_READ (user_id, message_id, time_read) VALUES (?, ?, ?)",
        (user.user_id, post["id"], int(time.time()))
      )
      con.commit()
      post["is_read"] = True

    await ansi_cls(user)
    ansi_wrap(user, False)

    # Header
    row = 1
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await ansi_move_deferred(user, row=row, col=1, drain=False)
    await send(user, f"  From: {post['from_handle']}"[:user.screen_width].ljust(user.screen_width), drain=False)

    row += 1
    ansi_color(user, fg=green, fg_br=False, bg=black)
    await ansi_move_deferred(user, row=row, col=1, drain=False)
    await send(user, f"  Date: {_format_time(post['time_created'])}"[:user.screen_width].ljust(user.screen_width), drain=False)

    row += 1
    ansi_color(user, fg=white, fg_br=True, bg=black)
    await ansi_move_deferred(user, row=row, col=1, drain=False)
    await send(user, f"  Subj: {post.get('subject', '')}"[:user.screen_width].ljust(user.screen_width), drain=False)

    row += 1
    ansi_color(user, fg=green, fg_br=False, bg=black)
    await ansi_move_deferred(user, row=row, col=1, drain=False)
    await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

    # Body - read-only InputField
    row += 1
    body_height = user.screen_height - row - 2
    if body_height < 1:
      body_height = 1
    body_width = user.screen_width - 2

    blocks = _json_to_blocks(post.get("message", "[]"))

    ansi_color(user)
    await ansi_move_deferred(user, row=row, col=2, drain=True)
    body_field = await InputField.create(
      parent=True,  # return field object, don't auto-run
      user=user,
      content=blocks,
      allow_edit=False,
      word_wrap=True,
      height=body_height,
      width=body_width,
      outline=False,
      fill=" ",
    )
    await body_field.draw_field()

    # Controls
    ctrl_row = user.screen_height - 1
    ansi_color(user, fg=green, fg_br=False, bg=black)
    await ansi_move_deferred(user, row=ctrl_row, col=1, drain=False)
    await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

    ctrl_row += 1
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await ansi_move_deferred(user, row=ctrl_row, col=1, drain=False)
    nav_info = f" ({post_index + 1}/{len(posts)})"
    ctrl_text = f" R)eply  N)ext  P)rev  Q)back{nav_info}"
    await send(user, ctrl_text[:user.screen_width].ljust(user.screen_width), drain=False)

    ansi_wrap(user, True)
    await user.writer.drain()

    r = await body_field.run()
    key = r.key if hasattr(r, 'key') else None

    if isinstance(key, str) and key.lower() == "r":
      await _compose_post(user, con, forum_id, reply_to_post=post)
      continue
    elif isinstance(key, str) and key.lower() == "n":
      if post_index + 1 < len(posts):
        post_index += 1
        continue
      else:
        await show_message_box(user, "No more posts.")
        continue
    elif isinstance(key, str) and key.lower() == "p":
      if post_index > 0:
        post_index -= 1
        continue
      else:
        await show_message_box(user, "Already at first post.")
        continue
    elif isinstance(key, str) and key.lower() == "q":
      return ("back", post_index)
    else:
      return ("back", post_index)


# ---------------------------------------------------------------------------
# Compose
# ---------------------------------------------------------------------------

async def _compose_post(user, con, forum_id, reply_to_post=None):
  """Compose a new forum post or reply."""
  await ansi_cls(user)
  ansi_wrap(user, False)

  # Title
  ansi_color(user, fg=cyan, fg_br=True, bg=black)
  await ansi_move_deferred(user, row=1, col=1, drain=False)
  title = "  Reply to Post" if reply_to_post else "  New Post"
  await send(user, title[:user.screen_width].ljust(user.screen_width), drain=False)

  ansi_color(user, fg=green, fg_br=False, bg=black)
  await ansi_move_deferred(user, row=2, col=1, drain=False)
  await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

  # Defaults for reply
  if reply_to_post:
    orig_subject = reply_to_post.get("subject", "") or ""
    if orig_subject.lower().startswith("re: "):
      default_subject = orig_subject
    else:
      default_subject = "Re: " + orig_subject
    orig_blocks = _json_to_blocks(reply_to_post.get("message", "[]"))
    date_str = _format_time(reply_to_post.get("time_created"))
    attribution = f"On {date_str}, {reply_to_post['from_handle']} wrote:"
    content_blocks = [Block(text="", level=0), Block(text=attribution, level=1)]
    for b in orig_blocks:
      content_blocks.append(Block(text=b.text, level=b.level + 1))
  else:
    default_subject = ""
    content_blocks = [Block(text="", level=0)]

  # Build form
  form = InputFields(user)

  # Subject field
  ansi_color(user, fg=white, fg_br=True, bg=black)
  await ansi_move_deferred(user, row=3, col=1, drain=False)
  await send(user, "  Subj: ", drain=True)
  subj_field = await form.add_field(
    conf=config.input_fields.input_field,
    width=user.screen_width - 10,
    max_length=200,
    content=default_subject,
  )
  await send(user, cr + lf, drain=False)

  # Separator
  ansi_color(user, fg=green, fg_br=False, bg=black)
  await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

  # Editor
  editor_top = user.cur_row + 1
  editor_height = user.screen_height - editor_top - 3
  if editor_height < 3:
    editor_height = 3

  await ansi_move_deferred(user, row=editor_top, col=1, drain=True)
  editor_field = await form.add_field(
    conf=config.input_fields.input_field,
    content=content_blocks,
    word_wrap=True,
    height=editor_height,
    width=user.screen_width,
    fill=" ",
    fill_fg=white, fill_fg_br=False,
    fill_bg=black, fill_bg_br=False,
  )

  # Divider
  divider_row = editor_top + editor_height
  ansi_color(user, fg=green, fg_br=False, bg=black)
  await ansi_move_deferred(user, row=divider_row, col=1, drain=False)
  await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

  # Buttons
  button_row = divider_row + 1
  await ansi_move_deferred(user, row=button_row, col=2, drain=True)
  await form.add_button("post", content=" Post ")
  post_btn = form._buttons[-1][1]
  cancel_col = post_btn.col_offset + post_btn.width + (1 if post_btn.outline else 0) + 1
  cancel_row = post_btn.row_offset - (1 if post_btn.outline else 0)
  await ansi_move_deferred(user, row=cancel_row, col=cancel_col, drain=True)
  await form.add_button("cancel", content=" Cancel ")

  ansi_wrap(user, True)
  start = 1 if reply_to_post else 0
  result = await form.run(start_index=start)

  if result.button == "post":
    subject = result.fields[0].content.strip()
    blocks = editor_field.get_blocks()
    message_json = _blocks_to_json(blocks)

    reply_to_id = reply_to_post["id"] if reply_to_post else None
    db_cur = con.cursor()
    db_cur.execute(
      "INSERT INTO FORUM_MESSAGES (from_user, reply_to, forum, subject, message, time_created) "
      "VALUES (?, ?, ?, ?, ?, ?)",
      (user.user_id, reply_to_id, forum_id, subject, message_json, int(time.time()))
    )
    con.commit()
    await show_message_box(user, "Post submitted.")


# ---------------------------------------------------------------------------
# New posts
# ---------------------------------------------------------------------------

async def _new_posts(user, con, forum_id, forum_name):
  """Show unread posts in this forum."""
  db_cur = con.cursor()
  db_cur.execute(
    "SELECT fm.id, fm.from_user, fm.reply_to, fm.subject, fm.message, fm.time_created, "
    "u.handle AS from_handle, "
    "CASE WHEN fmr.id IS NOT NULL THEN 1 ELSE 0 END AS is_read "
    "FROM FORUM_MESSAGES fm "
    "JOIN USERS u ON fm.from_user = u.id "
    "LEFT JOIN FORUM_MESSAGES_READ fmr ON fmr.message_id = fm.id AND fmr.user_id = ? "
    "WHERE fm.forum = ? AND fmr.id IS NULL "
    "ORDER BY fm.time_created DESC",
    (user.user_id, forum_id)
  )
  rows = db_cur.fetchall()

  posts = [dict(r) for r in rows]

  while True:
    chosen = await _show_post_list(user, posts, f"New Posts - {forum_name}")
    if chosen is None:
      return

    post_index = posts.index(chosen)
    action, new_index = await _read_post(user, chosen, posts, post_index, con, forum_id)

    if action == "back":
      continue


# ---------------------------------------------------------------------------
# Search posts
# ---------------------------------------------------------------------------

async def _search_posts(user, con, forum_id, forum_name):
  """Search posts in this forum."""
  await ansi_cls(user)
  ansi_wrap(user, False)

  # Title
  ansi_color(user, fg=cyan, fg_br=True, bg=black)
  await ansi_move_deferred(user, row=1, col=1, drain=False)
  await send(user, f"  Search - {forum_name}"[:user.screen_width].ljust(user.screen_width), drain=False)

  ansi_color(user, fg=green, fg_br=False, bg=black)
  await ansi_move_deferred(user, row=2, col=1, drain=False)
  await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

  field_width = min(40, user.screen_width - 20)

  form = InputFields(user)

  ansi_color(user, fg=white, fg_br=True, bg=black)
  await ansi_move_deferred(user, row=3, col=1, drain=False)
  await send(user, "  From user: ", drain=True)
  from_field = await form.add_field(
    conf=config.input_fields.input_field,
    width=field_width, max_length=30, height=1
  )

  ansi_color(user, fg=white, fg_br=True, bg=black)
  await ansi_move_deferred(user, row=5, col=1, drain=False)
  await send(user, "  Subject:   ", drain=True)
  subj_field = await form.add_field(
    conf=config.input_fields.input_field,
    width=field_width, max_length=200, height=1
  )

  ansi_color(user, fg=white, fg_br=True, bg=black)
  await ansi_move_deferred(user, row=7, col=1, drain=False)
  await send(user, "  Body:      ", drain=True)
  body_field = await form.add_field(
    conf=config.input_fields.input_field,
    width=field_width, max_length=200, height=1
  )

  ansi_color(user, fg=white, fg_br=True, bg=black)
  await ansi_move_deferred(user, row=9, col=1, drain=False)
  await send(user, "  Date from: ", drain=True)
  date_from_field = await form.add_field(
    conf=config.input_fields.input_field,
    width=12, max_length=10, height=1
  )

  ansi_color(user, fg=white, fg_br=True, bg=black)
  await ansi_move_deferred(user, row=11, col=1, drain=False)
  await send(user, "  Date to:   ", drain=True)
  date_to_field = await form.add_field(
    conf=config.input_fields.input_field,
    width=12, max_length=10, height=1
  )

  # Buttons
  await ansi_move_deferred(user, row=13, col=3, drain=True)
  await form.add_button("search", content=" Search ")
  await ansi_move_deferred(user, row=13, col=15, drain=True)
  await form.add_button("cancel", content=" Cancel ")

  ansi_wrap(user, True)
  result = await form.run(start_index=0)

  if result.button == "cancel":
    return

  # Gather criteria
  from_text = result.fields[0].content.strip()
  subj_text = result.fields[1].content.strip()
  body_text = result.fields[2].content.strip()
  date_from_text = result.fields[3].content.strip()
  date_to_text = result.fields[4].content.strip()

  # Build query
  conditions = ["fm.forum = ?"]
  params = [forum_id]

  if from_text:
    from_row = _lookup_handle(con, from_text)
    if from_row:
      conditions.append("fm.from_user = ?")
      params.append(from_row.id)
    else:
      await show_message_box(user, f"User '{from_text}' not found.")
      return

  if subj_text:
    conditions.append("fm.subject LIKE ?")
    params.append(f"%{subj_text}%")

  if body_text:
    conditions.append("fm.message LIKE ?")
    params.append(f"%{body_text}%")

  if date_from_text:
    try:
      ts = int(time.mktime(time.strptime(date_from_text, "%Y-%m-%d")))
      conditions.append("fm.time_created >= ?")
      params.append(ts)
    except ValueError:
      await show_message_box(user, "Invalid 'Date from' format. Use YYYY-MM-DD.")
      return

  if date_to_text:
    try:
      ts = int(time.mktime(time.strptime(date_to_text, "%Y-%m-%d"))) + 86400
      conditions.append("fm.time_created < ?")
      params.append(ts)
    except ValueError:
      await show_message_box(user, "Invalid 'Date to' format. Use YYYY-MM-DD.")
      return

  where_clause = " AND ".join(conditions)

  db_cur = con.cursor()
  db_cur.execute(
    f"SELECT fm.id, fm.from_user, fm.reply_to, fm.subject, fm.message, fm.time_created, "
    f"u.handle AS from_handle, "
    f"CASE WHEN fmr.id IS NOT NULL THEN 1 ELSE 0 END AS is_read "
    f"FROM FORUM_MESSAGES fm "
    f"JOIN USERS u ON fm.from_user = u.id "
    f"LEFT JOIN FORUM_MESSAGES_READ fmr ON fmr.message_id = fm.id AND fmr.user_id = ? "
    f"WHERE {where_clause} "
    f"ORDER BY fm.time_created DESC",
    [user.user_id] + params
  )
  rows = db_cur.fetchall()
  posts = [dict(r) for r in rows]

  if not posts:
    await show_message_box(user, "No posts found matching your search.")
    return

  while True:
    chosen = await _show_post_list(user, posts, f"Search Results - {forum_name} ({len(posts)} found)")
    if chosen is None:
      return

    post_index = posts.index(chosen)
    action, new_index = await _read_post(user, chosen, posts, post_index, con, forum_id)

    if action == "back":
      continue


# ---------------------------------------------------------------------------
# Inner action menu (shown after selecting a forum)
# ---------------------------------------------------------------------------

async def _forum_action_menu(user, forum_name, forum_id, con):
  """Show the action menu for a specific forum: New Posts, Compose, Search, eXit."""
  actions = ["New Posts", "Compose", "Search", "eXit"]

  while True:
    await ansi_cls(user)

    # Breadcrumb
    ansi_color(user, fg=cyan, fg_br=False, bg=black)
    await send(user, f" Main > Forums > {forum_name}" + cr + lf + cr + lf, drain=False)

    # Menu items
    ansi_color(user, fg=white, fg_br=True, bg=black)
    await send(user, "  N", drain=False)
    ansi_color(user, fg=white, fg_br=False, bg=black)
    await send(user, "ew Posts" + cr + lf, drain=False)

    ansi_color(user, fg=white, fg_br=True, bg=black)
    await send(user, "  C", drain=False)
    ansi_color(user, fg=white, fg_br=False, bg=black)
    await send(user, "ompose" + cr + lf, drain=False)

    ansi_color(user, fg=white, fg_br=True, bg=black)
    await send(user, "  S", drain=False)
    ansi_color(user, fg=white, fg_br=False, bg=black)
    await send(user, "earch" + cr + lf, drain=False)

    ansi_color(user, fg=white, fg_br=False, bg=black)
    await send(user, "  e", drain=False)
    ansi_color(user, fg=white, fg_br=True, bg=black)
    await send(user, "X", drain=False)
    ansi_color(user, fg=white, fg_br=False, bg=black)
    await send(user, "it" + cr + lf, drain=False)

    ansi_color(user, fg=white, fg_br=False, bg=black)
    await send(user, cr + lf + "Enter an option: ", drain=True)

    buf = []
    while True:
      key = await get_input_key(user)
      if isinstance(key, str) and len(key) == 1 and ord(key) >= 32:
        buf.append(key)
        await send(user, key, drain=True)
      elif key == "\x08" or key == "\x7f":
        if buf:
          buf.pop()
          await send(user, "\x08 \x08", drain=True)
      elif key == "\r" or key == "\x0d":
        break

    choice = "".join(buf).strip().lower()
    if not choice:
      continue

    if "new posts".startswith(choice) or choice == "n":
      await _new_posts(user, con, forum_id, forum_name)
    elif "compose".startswith(choice) or choice == "c":
      await _compose_post(user, con, forum_id)
    elif "search".startswith(choice) or choice == "s":
      await _search_posts(user, con, forum_id, forum_name)
    elif "exit".startswith(choice) or choice == "x":
      return
    # else: invalid, loop back


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def run(user, destination, menu_item=None):
  from common import Destinations

  if not menu_item or menu_item is null:
    await show_message_box(user, "No forum selected.")
    return RetVals(status=success, next_destination=Destinations.forums, next_menu_item=null)

  forum_name = menu_item if isinstance(menu_item, str) else str(menu_item)

  con = _get_db()
  try:
    forum_id = _get_or_create_forum(con, forum_name)
    await _forum_action_menu(user, forum_name, forum_id, con)
  except Disconnected:
    log.info("User disconnected from forum %s", forum_name)
  finally:
    con.close()

  return RetVals(status=success, next_destination=Destinations.forums, next_menu_item=null)
