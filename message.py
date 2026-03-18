"""
Private Messaging — compose, read, search, and reply to private messages.
"""

import json
import sqlite3
import time

from definitions import (RetVals, Disconnected, success, fail,
                         cr, lf, null,
                         white, black, green, cyan, red, blue, brown, magenta)
from input_output import send, ansi_color, ansi_move, ansi_wrap, ansi_cls, get_input_key, send_wrapped
from input_fields import InputField, InputFields, Block, show_message_box
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


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _get_db():
  con = sqlite3.connect(paths.resolve_data(str(config.database)))
  con.row_factory = sqlite3.Row
  return con


def _lookup_handle(con, handle):
  """Look up a user by handle (case-insensitive). Returns user row or None."""
  cur = con.cursor()
  cur.execute("SELECT id, handle FROM USERS WHERE handle = ? COLLATE NOCASE", (handle,))
  return cur.fetchone()


def _get_handle_by_id(con, user_id):
  """Get a user's handle by their id."""
  cur = con.cursor()
  cur.execute("SELECT handle FROM USERS WHERE id = ?", (user_id,))
  row = cur.fetchone()
  return row["handle"] if row else "Unknown"


def _blocks_to_json(blocks):
  """Serialize a list of Block objects to JSON string."""
  return json.dumps([{"text": b.text, "level": b.level} for b in blocks])


def _json_to_blocks(json_str):
  """Deserialize a JSON string back to a list of Block objects."""
  try:
    data = json.loads(json_str)
    return [Block(text=item["text"], level=item["level"]) for item in data]
  except (json.JSONDecodeError, KeyError, TypeError):
    return [Block(text=json_str or "", level=0)]


def _format_time(timestamp):
  """Format a unix timestamp for display."""
  if not timestamp:
    return ""
  return time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))


# ---------------------------------------------------------------------------
# Scrollable message list (shared by "new" and "search")
# ---------------------------------------------------------------------------

async def _show_message_list(user, messages, title):
  """Display messages in a scrollable full-screen list.

  messages: list of dicts with keys: id, from_handle, to_handle, subject, time_created, time_read
  Returns the selected message dict, or None if user pressed Q.
  """
  if not messages:
    await show_message_box(user, "No messages found.")
    return None

  header_rows = 3   # title + column header + separator
  footer_rows = 2   # separator + controls
  list_height = user.screen_height - header_rows - footer_rows
  if list_height < 1:
    list_height = 1

  total = len(messages)
  scroll_offset = 0
  selected = 0

  async def _draw():
    await ansi_cls(user)
    ansi_wrap(user, False)

    # Title
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await ansi_move(user, row=1, col=1, drain=False)
    padded_title = title[:user.screen_width].center(user.screen_width)
    await send(user, padded_title, drain=False)

    # Column header
    ansi_color(user, fg=white, fg_br=True, bg=black)
    await ansi_move(user, row=2, col=1, drain=False)
    hdr = "  Status  Date              From             Subject"
    await send(user, hdr[:user.screen_width].ljust(user.screen_width), drain=False)

    # Separator
    ansi_color(user, fg=green, fg_br=False, bg=black)
    await ansi_move(user, row=3, col=1, drain=False)
    await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

    # Message lines
    for i in range(list_height):
      msg_idx = scroll_offset + i
      row = header_rows + i + 1
      await ansi_move(user, row=row, col=1, drain=False)

      if msg_idx >= total:
        ansi_color(user, fg=white, fg_br=False, bg=black)
        await send(user, " " * user.screen_width, drain=False)
        continue

      msg = messages[msg_idx]
      is_selected = (msg_idx == selected)
      is_unread = msg["time_read"] is None

      status = "[NEW]" if is_unread else "[   ]"
      date_str = _format_time(msg["time_created"])
      from_handle = msg["from_handle"][:15]
      subj = msg.get("subject", "") or ""

      # Build the line
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
    await ansi_move(user, row=sep_row, col=1, drain=False)
    await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

    # Controls
    ctrl_row = sep_row + 1
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await ansi_move(user, row=ctrl_row, col=1, drain=False)
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
      return messages[selected]
    elif isinstance(key, str) and key.lower() == "q":
      return None


# ---------------------------------------------------------------------------
# Read view
# ---------------------------------------------------------------------------

async def _read_message(user, msg, messages, msg_index, con):
  """Show a single message in read view. Returns when user navigates away.

  Returns (action, new_index) where action is one of:
    "back" - return to list
    "next" - show next message
    "prev" - show previous message
    "deleted" - message was deleted, return to list
  """
  while True:
    # Reload message in case it was modified
    cur_msg = messages[msg_index] if 0 <= msg_index < len(messages) else None
    if cur_msg is None:
      return ("back", msg_index)

    msg = cur_msg

    # Mark as read
    if msg["time_read"] is None:
      db_cur = con.cursor()
      db_cur.execute("UPDATE PRIVATE_MESSAGES SET time_read = ? WHERE id = ?",
                     (int(time.time()), msg["id"]))
      con.commit()
      msg["time_read"] = int(time.time())

    await ansi_cls(user)
    ansi_wrap(user, False)

    # Header
    row = 1
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await ansi_move(user, row=row, col=1, drain=False)
    await send(user, f"  From: {msg['from_handle']}"[:user.screen_width].ljust(user.screen_width), drain=False)

    row += 1
    ansi_color(user, fg=cyan, fg_br=False, bg=black)
    await ansi_move(user, row=row, col=1, drain=False)
    await send(user, f"    To: {msg['to_handle']}"[:user.screen_width].ljust(user.screen_width), drain=False)

    row += 1
    ansi_color(user, fg=green, fg_br=False, bg=black)
    await ansi_move(user, row=row, col=1, drain=False)
    await send(user, f"  Date: {_format_time(msg['time_created'])}"[:user.screen_width].ljust(user.screen_width), drain=False)

    row += 1
    ansi_color(user, fg=white, fg_br=True, bg=black)
    await ansi_move(user, row=row, col=1, drain=False)
    await send(user, f"  Subj: {msg.get('subject', '')}"[:user.screen_width].ljust(user.screen_width), drain=False)

    row += 1
    ansi_color(user, fg=green, fg_br=False, bg=black)
    await ansi_move(user, row=row, col=1, drain=False)
    await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

    # Message body — use InputField in read-only mode
    row += 1
    body_height = user.screen_height - row - 2  # leave room for controls
    if body_height < 1:
      body_height = 1
    body_width = user.screen_width - 2

    blocks = _json_to_blocks(msg.get("message", "[]"))

    ansi_color(user)
    await ansi_move(user, row=row, col=2, drain=True)
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

    # Controls row
    ctrl_row = user.screen_height - 1
    ansi_color(user, fg=green, fg_br=False, bg=black)
    await ansi_move(user, row=ctrl_row, col=1, drain=False)
    await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

    ctrl_row += 1
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await ansi_move(user, row=ctrl_row, col=1, drain=False)
    nav_info = f" ({msg_index + 1}/{len(messages)})"
    ctrl_text = f" R)eply  D)elete  N)ext  P)rev  Q)back{nav_info}"
    await send(user, ctrl_text[:user.screen_width].ljust(user.screen_width), drain=False)

    ansi_wrap(user, True)
    await user.writer.drain()

    # Run the read-only field to allow scrolling, then handle keys
    r = await body_field.run()

    # After the field returns, check what key was pressed
    key = r.key if hasattr(r, 'key') else None

    if isinstance(key, str) and key.lower() == "r":
      await _reply_message(user, msg, con)
      continue  # re-draw after reply
    elif isinstance(key, str) and key.lower() == "d":
      db_cur = con.cursor()
      db_cur.execute("DELETE FROM PRIVATE_MESSAGES WHERE id = ?", (msg["id"],))
      con.commit()
      messages.pop(msg_index)
      await show_message_box(user, "Message deleted.")
      if not messages:
        return ("deleted", 0)
      if msg_index >= len(messages):
        msg_index = len(messages) - 1
      continue
    elif isinstance(key, str) and key.lower() == "n":
      if msg_index + 1 < len(messages):
        msg_index += 1
        continue
      else:
        await show_message_box(user, "No more messages.")
        continue
    elif isinstance(key, str) and key.lower() == "p":
      if msg_index > 0:
        msg_index -= 1
        continue
      else:
        await show_message_box(user, "Already at first message.")
        continue
    elif isinstance(key, str) and key.lower() == "q":
      return ("back", msg_index)
    else:
      # Any other key — treat as back
      return ("back", msg_index)


# ---------------------------------------------------------------------------
# Compose
# ---------------------------------------------------------------------------

async def _compose_message(user, con, reply_to_msg=None):
  """Compose and send a new message. If reply_to_msg is provided, pre-fill from it."""

  await ansi_cls(user)
  ansi_wrap(user, False)

  # Title
  ansi_color(user, fg=cyan, fg_br=True, bg=black)
  await ansi_move(user, row=1, col=1, drain=False)
  title = "  Reply to Message" if reply_to_msg else "  Compose Message"
  await send(user, title[:user.screen_width].ljust(user.screen_width), drain=False)

  ansi_color(user, fg=green, fg_br=False, bg=black)
  await ansi_move(user, row=2, col=1, drain=False)
  await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

  # Recipient
  if reply_to_msg:
    recipient_handle = reply_to_msg["from_handle"]
    recipient_id = reply_to_msg["from_user"] if "from_user" in reply_to_msg else None
    if not recipient_id:
      row = _lookup_handle(con, recipient_handle)
      recipient_id = row["id"] if row else None
  else:
    recipient_handle = None
    recipient_id = None

  # Default values
  if reply_to_msg:
    default_recipient = reply_to_msg.get("from_handle", "") or ""
    orig_subject = reply_to_msg.get("subject", "") or ""
    if orig_subject.lower().startswith("re: "):
      default_subject = orig_subject
    else:
      default_subject = "Re: " + orig_subject
    orig_blocks = _json_to_blocks(reply_to_msg.get("message", "[]"))
    date_str = _format_time(reply_to_msg.get("time_created"))
    attribution = f"On {date_str}, {reply_to_msg.get('from_handle', '')} wrote:"
    content_blocks = [Block(text="", level=0), Block(text=attribution, level=1)]
    for b in orig_blocks:
      content_blocks.append(Block(text=b.text, level=b.level + 1))
  else:
    default_recipient = ""
    default_subject = ""
    content_blocks = [Block(text="", level=0)]

  # Build the form: To, Subject, Editor, Send, Cancel — all in one InputFields
  form = InputFields(user)

  # To field
  ansi_color(user, fg=white, fg_br=True, bg=black)
  await ansi_move(user, row=3, col=1, drain=False)
  await send(user, "    To: ", drain=True)
  to_field = await form.add_field(
    conf=config.input_fields.input_field,
    width=30,
    max_length=30,
    content=default_recipient,
  )
  await send(user, cr + lf, drain=False)

  # Subject field
  ansi_color(user, fg=white, fg_br=True, bg=black)
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

  # Editor — frameless, full width
  editor_top = user.cur_row + 1
  editor_height = user.screen_height - editor_top - 3
  if editor_height < 3:
    editor_height = 3

  await ansi_move(user, row=editor_top, col=1, drain=True)
  editor_field = await form.add_field(
    conf=config.input_fields.input_field,
    content=content_blocks,
    word_wrap=True,
    height=editor_height,
    width=user.screen_width,
    fill=" ",
    fill_fg=white,
    fill_fg_br=False,
    fill_bg=black,
    fill_bg_br=False,
  )

  # Divider between editor and buttons
  divider_row = editor_top + editor_height
  ansi_color(user, fg=green, fg_br=False, bg=black)
  await ansi_move(user, row=divider_row, col=1, drain=False)
  await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

  # Buttons
  button_row = divider_row + 1
  await ansi_move(user, row=button_row, col=2, drain=True)
  await form.add_button("send", content=" Send ")
  send_btn = form._buttons[-1][1]
  abort_col = send_btn.col_offset + send_btn.width + (1 if send_btn.outline else 0) + 1
  abort_row = send_btn.row_offset - (1 if send_btn.outline else 0)
  await ansi_move(user, row=abort_row, col=abort_col, drain=True)
  await form.add_button("cancel", content=" Cancel ")

  # Run the form — loop on validation errors
  # Start on editor (index 2) for replies, recipient (index 0) for new messages
  start = 2 if reply_to_msg else 0
  while True:
    result = await form.run(start_index=start)

    if result.button != "send":
      return  # Cancel

    # Validate recipient
    recipient_handle = result.fields[0].content.strip()
    if not recipient_handle:
      await show_message_box(user, "Recipient is required.")
      continue
    row = _lookup_handle(con, recipient_handle)
    if not row:
      await show_message_box(user, f"User '{recipient_handle}' not found.")
      continue
    recipient_id = row["id"]
    recipient_handle = row["handle"]

    subject = result.fields[1].content.strip()
    blocks = editor_field.get_blocks()
    message_json = _blocks_to_json(blocks)

    db_cur = con.cursor()
    reply_to_id = reply_to_msg["id"] if reply_to_msg else None
    db_cur.execute(
      "INSERT INTO PRIVATE_MESSAGES (from_user, to_user, reply_to, subject, message, time_created, time_read) "
      "VALUES (?, ?, ?, ?, ?, ?, NULL)",
      (user.user_id, recipient_id, reply_to_id, subject, message_json, int(time.time()))
    )
    con.commit()
    await show_message_box(user, "Message sent.")
    return


# ---------------------------------------------------------------------------
# Reply
# ---------------------------------------------------------------------------

async def _reply_message(user, msg, con):
  """Reply to a message."""
  await _compose_message(user, con, reply_to_msg=msg)


# ---------------------------------------------------------------------------
# New messages
# ---------------------------------------------------------------------------

async def _new_messages(user):
  """Show unread messages for the current user."""
  con = _get_db()
  try:
    db_cur = con.cursor()
    db_cur.execute(
      "SELECT pm.id, pm.from_user, pm.to_user, pm.reply_to, pm.subject, pm.message, "
      "pm.time_created, pm.time_read, u.handle as from_handle "
      "FROM PRIVATE_MESSAGES pm "
      "JOIN USERS u ON pm.from_user = u.id "
      "WHERE pm.to_user = ? AND pm.time_read IS NULL "
      "ORDER BY pm.time_created DESC",
      (user.user_id,)
    )
    rows = db_cur.fetchall()

    # Convert to mutable dicts so we can update time_read
    messages = []
    for r in rows:
      msg = dict(r)
      msg["to_handle"] = user.handle
      messages.append(msg)

    while True:
      chosen = await _show_message_list(user, messages, "New Messages")
      if chosen is None:
        return

      msg_index = messages.index(chosen)
      action, new_index = await _read_message(user, chosen, messages, msg_index, con)

      if action == "back":
        continue  # back to list
      elif action == "deleted":
        if not messages:
          return
        continue
  finally:
    con.close()


# ---------------------------------------------------------------------------
# Search messages
# ---------------------------------------------------------------------------

async def _search_messages(user):
  """Search sent and received messages."""
  con = _get_db()
  try:
    await ansi_cls(user)
    ansi_wrap(user, False)

    # Title
    ansi_color(user, fg=cyan, fg_br=True, bg=black)
    await ansi_move(user, row=1, col=1, drain=False)
    await send(user, "  Search Messages"[:user.screen_width].ljust(user.screen_width), drain=False)

    ansi_color(user, fg=green, fg_br=False, bg=black)
    await ansi_move(user, row=2, col=1, drain=False)
    await send(user, (_H * user.screen_width)[:user.screen_width], drain=False)

    field_width = min(40, user.screen_width - 20)

    # Build form
    ansi_color(user, fg=white, fg_br=True, bg=black)
    await ansi_move(user, row=3, col=1, drain=False)
    await send(user, "  From user: ", drain=True)
    form = InputFields(user)
    from_field = await form.add_field(
      conf=config.input_fields.input_field,
      width=field_width, max_length=30, height=1
    )

    ansi_color(user, fg=white, fg_br=True, bg=black)
    await ansi_move(user, row=5, col=1, drain=False)
    await send(user, "  Subject:   ", drain=True)
    subj_field = await form.add_field(
      conf=config.input_fields.input_field,
      width=field_width, max_length=200, height=1
    )

    ansi_color(user, fg=white, fg_br=True, bg=black)
    await ansi_move(user, row=7, col=1, drain=False)
    await send(user, "  Body:      ", drain=True)
    body_field = await form.add_field(
      conf=config.input_fields.input_field,
      width=field_width, max_length=200, height=1
    )

    ansi_color(user, fg=white, fg_br=True, bg=black)
    await ansi_move(user, row=9, col=1, drain=False)
    await send(user, "  Date from: ", drain=True)
    date_from_field = await form.add_field(
      conf=config.input_fields.input_field,
      width=12, max_length=10, height=1
    )

    ansi_color(user, fg=white, fg_br=True, bg=black)
    await ansi_move(user, row=11, col=1, drain=False)
    await send(user, "  Date to:   ", drain=True)
    date_to_field = await form.add_field(
      conf=config.input_fields.input_field,
      width=12, max_length=10, height=1
    )

    # Buttons
    await ansi_move(user, row=13, col=3, drain=True)
    await form.add_button("search", content=" Search ")
    await ansi_move(user, row=13, col=15, drain=True)
    await form.add_button("cancel", content=" Cancel ")

    ansi_wrap(user, True)
    result = await form.run(start_index=0)

    if result.button == "cancel":
      return

    # Gather search criteria
    from_text = result.fields[0].content.strip()
    subj_text = result.fields[1].content.strip()
    body_text = result.fields[2].content.strip()
    date_from_text = result.fields[3].content.strip()
    date_to_text = result.fields[4].content.strip()

    # Build query
    conditions = ["(pm.to_user = ? OR pm.from_user = ?)"]
    params = [user.user_id, user.user_id]

    if from_text:
      from_row = _lookup_handle(con, from_text)
      if from_row:
        conditions.append("pm.from_user = ?")
        params.append(from_row["id"])
      else:
        await show_message_box(user, f"User '{from_text}' not found.")
        return

    if subj_text:
      conditions.append("pm.subject LIKE ?")
      params.append(f"%{subj_text}%")

    if body_text:
      conditions.append("pm.message LIKE ?")
      params.append(f"%{body_text}%")

    if date_from_text:
      try:
        ts = int(time.mktime(time.strptime(date_from_text, "%Y-%m-%d")))
        conditions.append("pm.time_created >= ?")
        params.append(ts)
      except ValueError:
        await show_message_box(user, "Invalid 'Date from' format. Use YYYY-MM-DD.")
        return

    if date_to_text:
      try:
        ts = int(time.mktime(time.strptime(date_to_text, "%Y-%m-%d"))) + 86400  # end of day
        conditions.append("pm.time_created < ?")
        params.append(ts)
      except ValueError:
        await show_message_box(user, "Invalid 'Date to' format. Use YYYY-MM-DD.")
        return

    where_clause = " AND ".join(conditions)

    db_cur = con.cursor()
    db_cur.execute(
      f"SELECT pm.id, pm.from_user, pm.to_user, pm.reply_to, pm.subject, pm.message, "
      f"pm.time_created, pm.time_read, u.handle as from_handle "
      f"FROM PRIVATE_MESSAGES pm "
      f"JOIN USERS u ON pm.from_user = u.id "
      f"WHERE {where_clause} "
      f"ORDER BY pm.time_created DESC",
      params
    )
    rows = db_cur.fetchall()

    messages = []
    for r in rows:
      msg = dict(r)
      # Resolve to_handle
      if msg["to_user"] == user.user_id:
        msg["to_handle"] = user.handle
      else:
        msg["to_handle"] = _get_handle_by_id(con, msg["to_user"])
      messages.append(msg)

    if not messages:
      await show_message_box(user, "No messages found matching your search.")
      return

    # Show results in scrollable list
    while True:
      chosen = await _show_message_list(user, messages, f"Search Results ({len(messages)} found)")
      if chosen is None:
        return

      msg_index = messages.index(chosen)
      action, new_index = await _read_message(user, chosen, messages, msg_index, con)

      if action == "back":
        continue
      elif action == "deleted":
        if not messages:
          return
        continue
  finally:
    con.close()


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
      menu_conf = config.menu_system.messages
      if menu_conf and menu_conf.options:
        opt = menu_conf.options[menu_item]
        if opt and hasattr(opt, 'action') and opt.action:
          action = str(opt.action).lower()
      if not action:
        action = menu_item.lower()
    elif hasattr(menu_item, 'action') and menu_item.action:
      action = str(menu_item.action).lower()

  try:
    if action == "new":
      await _new_messages(user)
    elif action == "compose":
      con = _get_db()
      try:
        await _compose_message(user, con)
      finally:
        con.close()
    elif action == "search":
      await _search_messages(user)
  except Disconnected:
    log.info("User disconnected from Private Messages")

  return RetVals(status=success, next_destination=Destinations.messages, next_menu_item=null)
