"""
User Settings page — lets users view and edit their profile and preferences.
Settings are stored in the user's YAML config file (user_configs/{handle}.yaml).
"""

import json
import os
import yaml

from input_fields import InputFields, InputField, show_message_box
from input_output import send, ansi_color, ansi_move_deferred, ansi_cls
from definitions import RetVals, success, fail, cr, lf, null, white, black, green, red
from config import get_config

config = get_config()
time_zones = json.load(open(os.path.join(os.path.dirname(__file__), "time_zones.json"), "r"))

# Settings layout: list of rows. Each row is a list of (key, label, width, max_length) tuples.
# Rows with 2 items are two-column; rows with 1 item span the full width.
SETTINGS_LAYOUT = [
  [("encoding",          "Encoding: ",     10, 9),    ("time_zone",   "Time zone: ",   11, 10)],
  [("email",             "Email: ",        50, 100)],
  [("age",               "Age: ",          11, 10),   ("sex",         "Sex: ",         11, 10)],
  [("location",          "Location: ",     50, 100)],
  [("bio",               "Bio: ",          50, 400)],
  [("allow_door_popups", "Door popups: ",  10, 5),    ("allow_pages", "Pages: ",       10, 5)],
  [("allow_bbs_messages","BBS messages: ", 10, 5),    ("scroll_step", "Scroll step: ",  5, 3)],
  [("blocked_users",     "Blocked: ",      50, 200)],
]

# Flat list of all keys in layout order (for mapping field indices to keys)
SETTINGS_KEYS = []
for row in SETTINGS_LAYOUT:
  for item in row:
    SETTINGS_KEYS.append(item[0])


async def run(user, destination, menu_item=None):
  from common import Destinations, _set_connection_encoding

  # Clear screen
  await ansi_cls(user)

  ansi_color(user, fg=white, bg=black, fg_br=True, bg_br=False)
  await send(user, f"Settings for {user.handle}" + cr + lf + cr + lf, drain=False)
  ansi_color(user, fg=white, bg=black, fg_br=False, bg_br=False)

  # Load current values from user config
  current = {}
  for key in SETTINGS_KEYS:
    val = user.conf[key] if user.conf else null
    if val is null or val is None:
      val = ""
    elif isinstance(val, list):
      val = ", ".join(str(v) for v in val)
    elif isinstance(val, bool):
      val = "true" if val else "false"
    current[key] = str(val)

  inputFields = InputFields(user)
  style_conf = config.input_fields.input_field

  # Compute max label length per column for alignment
  left_labels = []
  right_labels = []
  for row in SETTINGS_LAYOUT:
    left_labels.append(row[0][1])
    if len(row) > 1:
      right_labels.append(row[1][1])
  max_left_label = max((len(l) for l in left_labels), default=0)
  max_right_label = max((len(l) for l in right_labels), default=0) if right_labels else 0

  # Compute the right column start position:
  # Only consider two-column rows for the left field width
  two_col_rows = [row_def for row_def in SETTINGS_LAYOUT if len(row_def) > 1]
  max_left_field = max((row_def[0][2] for row_def in two_col_rows), default=10)
  right_col_start = max_left_label + max_left_field + 3  # 3 = gap

  for row_def in SETTINGS_LAYOUT:
    # First field in the row
    key, label, width, max_length = row_def[0]
    padded_left = label.rjust(max_left_label)
    label_row = user.cur_row
    ansi_color(user, fg=white, bg=black, fg_br=False, bg_br=False)
    await send(user, padded_left, drain=True)
    await inputFields.add_field(conf=style_conf, width=width, max_length=max_length, content=current[key])

    if len(row_def) > 1:
      key2, label2, width2, max_length2 = row_def[1]
      padded_right = label2.rjust(max_right_label)
      right_label_col = right_col_start
      # Position cursor for right-column label — must drain to actually move
      await ansi_move_deferred(user, row=label_row, col=right_label_col, drain=True)
      ansi_color(user, fg=white, bg=black, fg_br=False, bg_br=False)
      await send(user, padded_right, drain=True)
      await inputFields.add_field(conf=style_conf, width=width2, max_length=max_length2, content=current[key2])

    await send(user, cr + lf, drain=False)

  # Buttons
  submit_btn = await inputFields.add_button("save", content="Save")
  abort_col = submit_btn.col_offset + submit_btn.width + (1 if submit_btn.outline else 0) + 1
  abort_row = submit_btn.row_offset - (1 if submit_btn.outline else 0)
  await ansi_move_deferred(user, row=abort_row, col=abort_col, drain=True)
  await inputFields.add_button("cancel", content="Cancel")

  r = await inputFields.run()

  if r.button == "cancel":
    return RetVals(status=success, next_destination=Destinations.main, next_menu_item=null)

  # Save settings
  values = {}
  for i, key in enumerate(SETTINGS_KEYS):
    values[key] = r.fields[i].content.strip()

  # Validate encoding
  enc = values.get("encoding", "").lower()
  if enc not in ("cp437", "utf-8", "utf8"):
    await show_message_box(user, "Encoding must be 'cp437' or 'utf-8'.",
                           title="Error", outline_fg=red, outline_fg_br=True,
                           fg=white, fg_br=True, bg=black)
    return RetVals(status=success, next_destination=Destinations.settings, next_menu_item=null)
  if enc == "utf8":
    enc = "utf-8"
  values["encoding"] = enc

  # Validate time zone
  tz_raw = values.get("time_zone", "").strip()
  if tz_raw:
    from register import _validate_timezone, _parse_timezone
    tz_valid, tz_err = _validate_timezone(tz_raw)
    if not tz_valid:
      await show_message_box(user, tz_err,
                           title="Error", outline_fg=red, outline_fg_br=True,
                           fg=white, fg_br=True, bg=black)
      return RetVals(status=success, next_destination=Destinations.settings, next_menu_item=null)
    tz_letters, tz_hours, tz_mins = _parse_timezone(tz_raw)
    values["time_zone"] = tz_letters
    values["time_zone_hours"] = tz_hours
    values["time_zone_mins"] = tz_mins
  else:
    values["time_zone"] = ""
    values["time_zone_hours"] = 0
    values["time_zone_mins"] = 0

  # Validate boolean settings
  for bool_key in ("allow_door_popups", "allow_pages", "allow_bbs_messages"):
    val = values.get(bool_key, "").lower() if isinstance(values.get(bool_key, ""), str) else str(values.get(bool_key, ""))
    if val in ("true", "yes", "1", "on"):
      values[bool_key] = True
    elif val in ("false", "no", "0", "off"):
      values[bool_key] = False
    else:
      values[bool_key] = True  # default

  # Parse blocked_users: comma-separated handles → list
  blocked_raw = values.get("blocked_users", "")
  if isinstance(blocked_raw, str):
    values["blocked_users"] = [h.strip() for h in blocked_raw.split(",") if h.strip()]
  elif isinstance(blocked_raw, list):
    pass  # already a list
  else:
    values["blocked_users"] = []

  # Write to user YAML config
  user_conf_dir = str(config.user_configs or "user_configs")
  os.makedirs(user_conf_dir, exist_ok=True)
  user_conf_path = os.path.join(user_conf_dir, user.handle + ".yaml")

  # Load existing config to preserve any keys we don't show in settings
  existing = {}
  if os.path.exists(user_conf_path):
    try:
      with open(user_conf_path, "r") as f:
        existing = yaml.safe_load(f) or {}
    except Exception:
      pass

  existing.update(values)

  with open(user_conf_path, "w") as f:
    yaml.dump(existing, f, default_flow_style=False)

  # Apply encoding change immediately
  user.encoding = enc
  _set_connection_encoding(user)

  # Reload user config so user.conf reflects changes
  from config import get_config as gc, ConfigView
  try:
    conf1 = gc(path=user_conf_path)
  except Exception:
    conf1 = gc()
  user.conf = ConfigView(conf1, gc())

  # Apply profile fields to user object
  user.email = values.get("email") or None
  user.age = values.get("age") or None
  user.sex = values.get("sex") or None
  user.location = values.get("location") or None
  user.bio = values.get("bio") or None

  await show_message_box(user, "Settings saved successfully.",
                         title="Settings", outline_fg=green, outline_fg_br=True,
                         fg=white, fg_br=True, bg=black)

  return RetVals(status=success, next_destination=Destinations.main, next_menu_item=null)
