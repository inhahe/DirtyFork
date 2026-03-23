"""
User information features: /info command, Who's Online, User List.
"""

import asyncio
import time
import sqlite3

from input_fields import show_message_box
from input_output import send, ansi_color, ansi_cls
from definitions import RetVals, success, null, cr, lf, white, black, green, cyan, yellow
from config import get_config
import paths

config = get_config()


def _format_time(timestamp):
  """Format a Unix timestamp as a readable date string."""
  if not timestamp:
    return "Unknown"
  try:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(int(timestamp)))
  except (ValueError, TypeError, OSError):
    return "Unknown"


def _format_idle(seconds):
  """Format idle seconds as a human-readable string."""
  if seconds < 60:
    return f"{int(seconds)}s"
  elif seconds < 3600:
    return f"{int(seconds // 60)}m"
  elif seconds < 86400:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}h {m}m"
  else:
    d = int(seconds // 86400)
    h = int((seconds % 86400) // 3600)
    return f"{d}d {h}h"


def _get_idle_seconds(target_user):
  """Get idle seconds for a user, or None if not available."""
  try:
    reader = target_user.reader
    if hasattr(reader, '_last_activity'):
      return asyncio.get_event_loop().time() - reader._last_activity
  except Exception:
    pass
  return None


def _get_current_location(target_user):
  """Get the name of where a user currently is."""
  if target_user.destination_history:
    last = target_user.destination_history[-1]
    name = getattr(last, 'dest_name', None)
    if name:
      return str(name)
  return "Unknown"


def _load_user_config(config_filename):
  """Load a user's YAML config by their config_filename. Returns a dict or {}."""
  if not config_filename:
    return {}
  try:
    user_conf_dir = paths.resolve_data(str(config.user_configs or "user_configs"))
    import os
    from ruamel.yaml import YAML
    conf_path = os.path.join(str(user_conf_dir), config_filename + ".yaml")
    if os.path.exists(conf_path):
      with open(conf_path, "r") as f:
        return YAML().load(f) or {}
  except Exception:
    pass
  return {}


def _profile_field(profile, key, label, public_key, sysop=False):
  """Return (label, value, is_private) for a profile field."""
  val = profile.get(key, "")
  is_public = profile.get(public_key, True)  # default to public if setting missing
  if not val:
    return None  # skip empty fields entirely
  if not is_public and not sysop:
    return (label, "<Private>", True)
  return (label, str(val), False)


async def show_user_info(user, target_handle):
  """Show a user profile popup. Returns error string on failure, None on success."""
  from common import lookup_handle, global_data, con

  row = lookup_handle(target_handle)
  if not row:
    return f"User '{target_handle}' not found."

  user_id, handle = row.id, row.handle

  # Get DB info
  db_row = con.execute(
    "SELECT time_created, last_login, config_filename FROM USERS WHERE id = ?", (user_id,)
  ).fetchone()
  time_created = db_row["time_created"] if db_row else None
  last_login = db_row["last_login"] if db_row else None
  config_filename = db_row["config_filename"] if db_row else None

  # Load profile from YAML
  profile = _load_user_config(config_filename)

  sysop = _is_sysop(user)

  # Check if the target user has the viewer blocked (sysops bypass)
  if not sysop:
    blocked = profile.get("blocked_users", [])
    if isinstance(blocked, list) and user.handle:
      if user.handle.lower() in (b.lower() for b in blocked):
        return f"User '{handle}' is not available."

  # Check online status
  live = global_data.users.get(handle.lower())
  if live:
    idle = _get_idle_seconds(live)
    location = _get_current_location(live)
    idle_str = f" (idle {_format_idle(idle)})" if idle is not None and idle > 60 else ""
    status = f"Online - {location}{idle_str}"
  else:
    status = "Offline"

  # Build profile lines: list of (label, value, is_private)
  fields = []
  fields.append(("Handle", handle, False))

  for key, label, public_key in [
    ("location", "Location", "public_location"),
    ("age",      "Age",      "public_age"),
    ("sex",      "Sex",      "public_sex"),
    ("email",    "Email",    "public_email"),
  ]:
    f = _profile_field(profile, key, label, public_key, sysop)
    if f:
      fields.append(f)

  fields.append(("Created", _format_time(time_created), False))
  if last_login:
    fields.append(("Last on", _format_time(last_login), False))
  fields.append(("Status", status, False))

  # Bio (always public — if you don't want it seen, leave it empty)
  bio = profile.get("bio", "")

  # Calculate label width for alignment
  max_label = max(len(f[0]) for f in fields)

  # Build text with private markers for show_message_box
  # We use show_message_box but mark private fields so they stand out
  lines = []
  for label, value, is_private in fields:
    padded = (label + ":").ljust(max_label + 2)
    if is_private:
      lines.append(f"{padded}{value}")
    else:
      lines.append(f"{padded}{value}")

  if bio:
    lines.append("")
    lines.append("Bio:")
    lines.append(bio)

  text = "\n".join(lines)
  await show_message_box(user, text, title=f" {handle} ",
                         fg=white, fg_br=True, bg=black,
                         outline_fg=cyan, outline_fg_br=True)
  return None


def _is_sysop(user):
  """Check if a user has sysop privileges."""
  return hasattr(user, 'keys') and 'sysop' in user.keys


def _get_public_field(profile, key, public_key, sysop=False):
  """Get a profile field value if public (or if viewer is sysop), or empty string if private/missing."""
  val = profile.get(key, "")
  if not val:
    return ""
  is_public = profile.get(public_key, True)
  if is_public or sysop:
    return str(val)
  return ""


def _build_details_line(profile, sysop=False):
  """Build an indented details line from public profile fields. Returns string or empty."""
  parts = []
  age = _get_public_field(profile, "age", "public_age", sysop)
  if age:
    parts.append(f"Age: {age}")
  sex = _get_public_field(profile, "sex", "public_sex", sysop)
  if sex:
    parts.append(f"Sex: {sex}")
  loc = _get_public_field(profile, "location", "public_location", sysop)
  if loc:
    parts.append(f"Location: {loc}")
  if parts:
    return "    " + "  ".join(parts)
  return ""


async def run_user_info(user, dest_conf, menu_item=None):
  """User Info module — prompt for a handle and show their profile."""
  from common import Destinations
  from input_fields import InputField

  await ansi_cls(user)
  ansi_color(user, fg=white, bg=black, fg_br=True)
  await send(user, "User Info" + cr + lf + cr + lf, drain=False)
  ansi_color(user, fg=white, bg=black, fg_br=False)
  await send(user, "Handle: ", drain=True)
  r = await InputField.create(user=user, conf=config.input_fields.input_field,
                               width=30, max_length=50)
  handle = r.content.strip() if hasattr(r, 'content') else ""
  if not handle:
    return RetVals(status=success, next_destination=Destinations.main)

  err = await show_user_info(user, handle)
  if err:
    await show_message_box(user, err, title=" Not Found ",
                           fg=white, fg_br=True, bg=black,
                           outline_fg=yellow, outline_fg_br=True)
  return RetVals(status=success, next_destination=Destinations.main)


async def run_whos_online(user, dest_conf, menu_item=None):
  """Who's Online module — shows all logged-in users."""
  from common import Destinations, global_data, con

  sysop = _is_sysop(user)
  users = dict(global_data.users)  # snapshot

  if not users:
    await show_message_box(user, "No users currently online.",
                           title=" Who's Online ",
                           fg=white, fg_br=True, bg=black,
                           outline_fg=green, outline_fg_br=True)
    return RetVals(status=success, next_destination=Destinations.main)

  # Build two-line-per-user display
  lines = []

  for handle_key, target in sorted(users.items()):
    handle = target.handle or handle_key
    activity = _get_current_location(target)
    idle = _get_idle_seconds(target)
    idle_str = f", idle {_format_idle(idle)}" if idle is not None and idle > 60 else ""
    status = f"Online ({activity}{idle_str})"

    lines.append(f"{handle}  -  {status}")

    # Load profile for details line
    db_row = con.execute(
      "SELECT config_filename FROM USERS WHERE handle = ? COLLATE NOCASE", (handle,)
    ).fetchone()
    cf = db_row["config_filename"] if db_row else None
    profile = _load_user_config(cf) if cf else {}
    details = _build_details_line(profile, sysop)
    if details:
      lines.append(details)
      lines.append("")  # blank line between users with details

  # Remove trailing blank if present (last user's separator)
  if lines and lines[-1] == "":
    lines.pop()
  lines.append("")
  lines.append(f"{len(users)} user(s) online")

  text = "\n".join(lines)
  await show_message_box(user, text, title=" Who's Online ",
                         fg=white, fg_br=True, bg=black,
                         outline_fg=green, outline_fg_br=True,
                         word_wrap=False)
  return RetVals(status=success, next_destination=Destinations.main)


async def run_user_list(user, dest_conf, menu_item=None):
  """User List module — browse/search all registered users."""
  from common import Destinations, global_data, con
  from input_fields import InputField

  sysop = _is_sysop(user)

  # Prompt for search (optional)
  search = None
  item_name = menu_item[0] if isinstance(menu_item, tuple) else menu_item
  if item_name and str(item_name).lower() == "search":
    await ansi_cls(user)
    ansi_color(user, fg=white, bg=black, fg_br=True)
    await send(user, "Search users" + cr + lf + cr + lf, drain=False)
    ansi_color(user, fg=white, bg=black, fg_br=False)
    await send(user, "Handle: ", drain=True)
    r = await InputField.create(user=user, conf=config.input_fields.input_field,
                                 width=30, max_length=50)
    search = r.content.strip() if hasattr(r, 'content') else ""
    if not search:
      return RetVals(status=success, next_destination=Destinations.main)

  # Query database
  if search:
    rows = con.execute(
      "SELECT handle, time_created, last_login, config_filename FROM USERS WHERE handle LIKE ? COLLATE NOCASE ORDER BY handle COLLATE NOCASE",
      (f"%{search}%",)
    ).fetchall()
  else:
    rows = con.execute(
      "SELECT handle, time_created, last_login, config_filename FROM USERS ORDER BY handle COLLATE NOCASE"
    ).fetchall()

  if not rows:
    msg = f"No users matching '{search}'." if search else "No registered users."
    await show_message_box(user, msg, title=" User List ",
                           fg=white, fg_br=True, bg=black,
                           outline_fg=green, outline_fg_br=True)
    return RetVals(status=success, next_destination=Destinations.main)

  # Build two-line-per-user display
  online_users = set(global_data.users.keys())
  lines = []

  for row in rows:
    handle = row["handle"]
    last_login = _format_time(row["last_login"])
    live = global_data.users.get(handle.lower())
    if live:
      activity = _get_current_location(live)
      idle = _get_idle_seconds(live)
      idle_str = f", idle {_format_idle(idle)}" if idle is not None and idle > 60 else ""
      status = f"Online ({activity}{idle_str})"
    else:
      status = f"Offline  -  Last on: {last_login}"

    lines.append(f"{handle}  -  {status}")

    cf = row["config_filename"] if row["config_filename"] else None
    profile = _load_user_config(cf) if cf else {}
    details = _build_details_line(profile, sysop)
    if details:
      lines.append(details)
      lines.append("")  # blank line between users with details

  # Remove trailing blank if present (last user's separator)
  if lines and lines[-1] == "":
    lines.pop()
  lines.append("")
  lines.append(f"{len(rows)} user(s)" + (f" matching '{search}'" if search else ""))

  text = "\n".join(lines)
  title = f" Users: {search} " if search else " User List "
  await show_message_box(user, text, title=title,
                         fg=white, fg_br=True, bg=black,
                         outline_fg=green, outline_fg_br=True,
                         word_wrap=False)
  return RetVals(status=success, next_destination=Destinations.main)
