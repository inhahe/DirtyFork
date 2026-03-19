"""
User Settings page — lets users view and edit their profile and preferences.
Settings are stored in the user's YAML config file (user_configs/{handle}.yaml).
"""

import json
import os
from ruamel.yaml import YAML
_yaml = YAML()
_yaml.default_flow_style = False

from input_fields import InputFields, InputField, show_message_box
from input_output import send, ansi_color, ansi_move_deferred, ansi_cls
from definitions import RetVals, success, fail, cr, lf, null, white, black, green, red
from config import get_config
import paths

config = get_config()
time_zones = json.load(open(os.path.join(os.path.dirname(__file__), "time_zones.json"), "r"))

# Field types
TEXT = "text"
SELECT = "select"
LIST = "list"
BOOL = "bool"  # boolean select — defaults to ["yes", "no"], stored as True/False

# Settings layout: list of rows. Each row is a list of field descriptors.
# Text fields:   (key, label, width, max_length, TEXT)
# Select fields:  (key, label, options, SELECT)
# Bool fields:    (key, label, BOOL)  — yes/no select, stored as boolean
# List fields:    (key, label, width, height, LIST)
SETTINGS_LAYOUT = [
  [("handle",            "Handle: ",        0, 0,                    TEXT)],  # width/max_length 0 = auto from register.yaml
  [("encoding",          "Encoding: ",      ["cp437", "utf-8"],      SELECT),
   ("time_zone",         "Time zone: ",     11, 10,                  TEXT)],
  [("start_destination", "Start at: ",      30, 50,                  TEXT)],
  [("email",             "Email: ",         40, 100,                 TEXT),
   ("public_email",      "Public? ",                                 BOOL)],
  [("age",               "Age: ",           11, 10,                  TEXT),
   ("public_age",        "Public? ",                                 BOOL)],
  [("sex",               "Sex: ",           11, 10,                  TEXT),
   ("public_sex",        "Public? ",                                 BOOL)],
  [("location",          "Location: ",      40, 100,                 TEXT),
   ("public_location",   "Public? ",                                 BOOL)],
  # Bio is edited via a separate full-screen editor (Edit Bio button)
  [("allow_door_popups", "Door popups: ",                            BOOL)],
  [("allow_pages",       "Allow pages: ",                            BOOL)],
  [("scroll_step",       "H. scroll step: ",5, 3,                   TEXT)],
  [("blocked_users",     "Blocked: ",       0, 3,                    LIST)],  # width 0 = auto from handle max_length
]

# Flat list of all keys in layout order (for mapping field indices to keys)
SETTINGS_KEYS = []
BOOL_KEYS = set()
for row in SETTINGS_LAYOUT:
  for item in row:
    SETTINGS_KEYS.append(item[0])
    if item[-1] == BOOL:
      BOOL_KEYS.add(item[0])


async def _validate_handle(handle):
  """Validate that a handle exists in the database. Returns (ok, error_msg)."""
  from common import handle_exists
  if handle_exists(handle):
    return True, None
  return False, f"'{handle}' not found."


async def _edit_bio(user, target_handle, user_conf_path):
  """Full-screen bio editor. Returns new bio text, or None if cancelled."""
  # Load current bio
  current_bio = ""
  if os.path.exists(user_conf_path):
    try:
      with open(user_conf_path, "r") as f:
        data = _yaml.load(f) or {}
        current_bio = data.get("bio", "")
    except Exception:
      pass

  await ansi_cls(user)
  ansi_color(user, fg=white, bg=black, fg_br=True)
  await send(user, f"Edit Bio for {target_handle}" + cr + lf, drain=False)
  ansi_color(user, fg=white, bg=black, fg_br=False)

  inputFields = InputFields(user)
  style_conf = config.input_fields.input_field

  await inputFields.add_field(conf=style_conf, width=user.screen_width - 2,
                               max_length=400, height_from_end=3,
                               word_wrap=True, content=current_bio)

  save_btn = await inputFields.add_button("save", content="Save")
  next_col = save_btn.col_offset + save_btn.width + (1 if save_btn.outline else 0) + 1
  btn_row = save_btn.row_offset - (1 if save_btn.outline else 0)
  await ansi_move_deferred(user, row=btn_row, col=next_col, drain=True)
  await inputFields.add_button("cancel", content="Cancel")

  r = await inputFields.run()
  if r.button == "cancel":
    return None
  return r.fields[0].content


async def edit_settings(user, target_handle, return_destination, return_menu_item=null):
  """Edit settings for target_handle. Called by both the user's own settings
  page and the sysop module. The form is displayed to `user` but the config
  read/written belongs to `target_handle`."""
  from common import Destinations, _set_connection_encoding, global_data, con as db_con

  is_self = (target_handle.lower() == (user.handle or "").lower())

  # Look up config_filename for this user
  if is_self and hasattr(user, 'config_filename'):
    config_fn = user.config_filename
  else:
    row = db_con.execute("SELECT config_filename FROM USERS WHERE handle = ? COLLATE NOCASE", (target_handle,)).fetchone()
    config_fn = row["config_filename"] if row and row["config_filename"] else target_handle

  # Load target user's config
  user_conf_dir = paths.resolve_data(str(config.user_configs or "user_configs"))
  user_conf_path = os.path.join(str(user_conf_dir), config_fn + ".yaml")

  from config import get_config as gc, ConfigView
  try:
    target_conf = ConfigView(gc(path=user_conf_path), gc()) if os.path.exists(user_conf_path) else ConfigView(gc(), gc())
  except Exception:
    target_conf = ConfigView(gc(), gc())

  await ansi_cls(user)

  ansi_color(user, fg=white, bg=black, fg_br=True, bg_br=False)
  await send(user, f"Settings for {target_handle}" + cr + lf + cr + lf, drain=False)
  ansi_color(user, fg=white, bg=black, fg_br=False, bg_br=False)

  # Load current values from target config
  current = {}
  for key in SETTINGS_KEYS:
    val = target_conf[key] if target_conf else null
    if val is null or val is None:
      if key in BOOL_KEYS:
        val = "no" if key == "public_email" else "yes"
      else:
        val = ""
    elif isinstance(val, list):
      current[key] = [str(v) for v in val]  # keep as list for LIST fields
      continue
    elif isinstance(val, bool):
      val = "yes" if val else "no"
    current[key] = str(val)

  # Handle is stored in DB, not YAML — override with the actual handle
  current["handle"] = target_handle

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

  # Compute the right column start position from two-column text/select fields
  two_col_rows = [row_def for row_def in SETTINGS_LAYOUT if len(row_def) > 1]
  max_left_field = 0
  for row_def in two_col_rows:
    ftype = row_def[0][-1]
    if ftype == TEXT:
      max_left_field = max(max_left_field, row_def[0][2])
    elif ftype == SELECT:
      opt_width = max((len(str(o)) for o in row_def[0][2]), default=1) + 4
      max_left_field = max(max_left_field, opt_width)
    elif ftype == BOOL:
      max_left_field = max(max_left_field, 7)  # "< yes >"
  if max_left_field == 0:
    max_left_field = 10
  right_col_start = max_left_label + max_left_field + 3

  # Track which fields are ListFields so we can read .items from them
  field_types = []  # parallel to inputFields.fields

  for row_def in SETTINGS_LAYOUT:
    desc = row_def[0]
    key = desc[0]
    label = desc[1]
    ftype = desc[-1]
    padded_left = label.rjust(max_left_label)
    label_row = user.cur_row

    ansi_color(user, fg=white, bg=black, fg_br=False, bg_br=False)
    await send(user, padded_left, drain=True)

    if ftype == TEXT:
      width, max_length = desc[2], desc[3]
      # Auto-size handle field from register.yaml
      if key == "handle" and not width:
        try:
          from config import get_config as _gc
          _reg = _gc(path=paths.resolve_project("register.yaml"))
          max_length = int(_reg.handle.max_length) if _reg.handle and _reg.handle.max_length else 29
          width = max_length + 1
        except Exception:
          width, max_length = 30, 29
      await inputFields.add_field(conf=style_conf, width=width, max_length=max_length, content=current.get(key, ""))
    elif ftype == SELECT:
      options = desc[2]
      await inputFields.add_select(options=options, value=current.get(key, ""), conf=style_conf)
    elif ftype == BOOL:
      await inputFields.add_select(options=["yes", "no"], value=current.get(key, "yes"), conf=style_conf)
    elif ftype == LIST:
      width, height = desc[2], desc[3]
      # Auto-size from handle max_length if width is 0
      if not width:
        try:
          from config import get_config as _gc
          _reg = _gc(path=paths.resolve_project("register.yaml"))
          width = int(_reg.handle.max_length) + 1 if _reg.handle and _reg.handle.max_length else 30
        except Exception:
          width = 30
        # Cap so it doesn't run off screen
        max_width = user.screen_width - user.cur_col - 3  # room for outline + margin
        width = min(width, max_width)
      items = current.get(key, [])
      if isinstance(items, str):
        items = [h.strip() for h in items.split(",") if h.strip()]
      list_field = await inputFields.add_list(items=items, width=width, height=height,
                                  validate=_validate_handle, title=" Blocked Users ")
      # Move cursor past the list field (outline + content + outline + add row)
      past_row = list_field.row_offset + list_field.height + (1 if list_field.outline else 0) + 1
      await ansi_move_deferred(user, row=past_row, col=1, drain=True)
    field_types.append(ftype)

    if len(row_def) > 1:
      desc2 = row_def[1]
      key2 = desc2[0]
      label2 = desc2[1]
      ftype2 = desc2[-1]
      padded_right = label2.rjust(max_right_label)
      await ansi_move_deferred(user, row=label_row, col=right_col_start, drain=True)
      ansi_color(user, fg=white, bg=black, fg_br=False, bg_br=False)
      await send(user, padded_right, drain=True)

      if ftype2 == TEXT:
        width2, max_length2 = desc2[2], desc2[3]
        await inputFields.add_field(conf=style_conf, width=width2, max_length=max_length2, content=current.get(key2, ""))
      elif ftype2 == SELECT:
        options2 = desc2[2]
        await inputFields.add_select(options=options2, value=current.get(key2, ""), conf=style_conf)
      elif ftype2 == BOOL:
        await inputFields.add_select(options=["yes", "no"], value=current.get(key2, "yes"), conf=style_conf)
      elif ftype2 == LIST:
        width2, height2 = desc2[2], desc2[3]
        items2 = current.get(key2, [])
        if isinstance(items2, str):
          items2 = [h.strip() for h in items2.split(",") if h.strip()]
        await inputFields.add_list(items=items2, width=width2, height=height2,
                                    validate=_validate_handle)
      field_types.append(ftype2)

    await send(user, cr + lf, drain=False)

  # Password fields (not part of layout — stored in DB, not YAML)
  pw_label = "New password: ".rjust(max_left_label)
  pw_label_row = user.cur_row
  ansi_color(user, fg=white, bg=black, fg_br=False, bg_br=False)
  await send(user, pw_label, drain=True)
  pw_field_idx = len(inputFields.fields)
  pw_field = await inputFields.add_field(conf=style_conf, width=20, max_length=19, content="", mask_char="*")
  field_types.append(TEXT)

  confirm_col = pw_field.col_offset + pw_field.width + 2
  await ansi_move_deferred(user, row=pw_label_row, col=confirm_col, drain=True)
  ansi_color(user, fg=white, bg=black, fg_br=False, bg_br=False)
  await send(user, "Confirm: ", drain=True)
  await inputFields.add_field(conf=style_conf, width=20, max_length=19, content="", mask_char="*")
  field_types.append(TEXT)

  # Move to next line for buttons
  await ansi_move_deferred(user, row=pw_label_row + 1, col=1, drain=True)
  await send(user, cr + lf, drain=False)

  # Buttons
  submit_btn = await inputFields.add_button("save", content="Save")
  btn_row = submit_btn.row_offset - (1 if submit_btn.outline else 0)
  next_col = submit_btn.col_offset + submit_btn.width + (1 if submit_btn.outline else 0) + 1
  await ansi_move_deferred(user, row=btn_row, col=next_col, drain=True)
  bio_btn = await inputFields.add_button("edit_bio", content="Edit Bio")
  next_col = bio_btn.col_offset + bio_btn.width + (1 if bio_btn.outline else 0) + 1
  await ansi_move_deferred(user, row=btn_row, col=next_col, drain=True)
  await inputFields.add_button("cancel", content="Cancel")

  r = await inputFields.run()

  if r.button == "cancel":
    return RetVals(status=success, next_destination=return_destination, next_menu_item=return_menu_item)

  if r.button == "edit_bio":
    # Open full-screen bio editor, save result, then re-enter settings
    new_bio = await _edit_bio(user, target_handle, user_conf_path)
    if new_bio is not None:
      # Save bio to YAML
      existing = {}
      if os.path.exists(user_conf_path):
        try:
          with open(user_conf_path, "r") as f:
            existing = _yaml.load(f) or {}
        except Exception:
          pass
      existing["bio"] = new_bio
      os.makedirs(os.path.dirname(user_conf_path), exist_ok=True)
      with open(user_conf_path, "w") as f:
        _yaml.dump(existing, f)
      # Update live session
      live_user = global_data.users.get(target_handle.lower())
      if live_user:
        live_user.bio = new_bio
        try:
          from config import get_config as gc, ConfigView
          conf1 = gc(path=user_conf_path)
          live_user.conf = ConfigView(conf1, gc())
        except Exception:
          pass
    return await edit_settings(user, target_handle, return_destination, return_menu_item)

  # Read values back from fields
  values = {}
  for i, key in enumerate(SETTINGS_KEYS):
    field = inputFields.fields[i]
    if field_types[i] == LIST:
      # ListField: read .items directly as a list
      values[key] = list(field.items)
    else:
      values[key] = r.fields[i].content.strip()

  # Validate encoding (select field, so value is always valid, just normalize)
  enc = values.get("encoding", "cp437").lower()
  if enc == "utf8":
    enc = "utf-8"
  values["encoding"] = enc

  # Validate start destination
  sd_raw = values.get("start_destination", "").strip()
  if sd_raw:
    from menu import resolve_jump
    dest_name, mi, parent_menu, err = resolve_jump(sd_raw)
    if err:
      await show_message_box(user, err,
                           title="Error", outline_fg=red, outline_fg_br=True,
                           fg=white, fg_br=True, bg=black)
      return await edit_settings(user, target_handle, return_destination, return_menu_item)
    values["start_destination"] = sd_raw
  else:
    values["start_destination"] = ""

  # Validate time zone
  tz_raw = values.get("time_zone", "").strip()
  if tz_raw:
    from register import _validate_timezone, _parse_timezone
    tz_valid, tz_err = _validate_timezone(tz_raw)
    if not tz_valid:
      await show_message_box(user, tz_err,
                           title="Error", outline_fg=red, outline_fg_br=True,
                           fg=white, fg_br=True, bg=black)
      return await edit_settings(user, target_handle, return_destination, return_menu_item)
    tz_letters, tz_hours, tz_mins = _parse_timezone(tz_raw)
    values["time_zone"] = tz_letters
    values["time_zone_hours"] = tz_hours
    values["time_zone_mins"] = tz_mins
  else:
    values["time_zone"] = ""
    values["time_zone_hours"] = 0
    values["time_zone_mins"] = 0

  # Convert BOOL fields from "yes"/"no" strings to actual booleans
  for bool_key in BOOL_KEYS:
    val = values.get(bool_key, "")
    if isinstance(val, str):
      values[bool_key] = val.lower() in ("true", "yes", "1", "on")
    elif isinstance(val, bool):
      pass
    else:
      values[bool_key] = True

  # blocked_users is already a list from the ListField

  # Handle capitalization change (DB field, not YAML — config_filename stays the same)
  new_handle = values.pop("handle", "").strip()
  if new_handle and new_handle.lower() == target_handle.lower() and new_handle != target_handle:
    db_con.execute(
      "UPDATE USERS SET handle = ? WHERE handle = ? COLLATE NOCASE",
      (new_handle, target_handle)
    )
    db_con.commit()
    # Update live session
    live_user = global_data.users.get(target_handle.lower())
    if live_user:
      live_user.handle = new_handle
    target_handle = new_handle
  elif new_handle and new_handle.lower() != target_handle.lower():
    await show_message_box(user, "You can only change the capitalization of your handle.",
                         title="Error", outline_fg=red, outline_fg_br=True,
                         fg=white, fg_br=True, bg=black)
    return await edit_settings(user, target_handle, return_destination, return_menu_item)

  # Handle password change (fields are after the layout fields)
  new_pw = r.fields[pw_field_idx].content
  confirm_pw = r.fields[pw_field_idx + 1].content
  if new_pw or confirm_pw:
    if new_pw != confirm_pw:
      await show_message_box(user, "Passwords do not match.",
                           title="Error", outline_fg=red, outline_fg_br=True,
                           fg=white, fg_br=True, bg=black)
      return await edit_settings(user, target_handle, return_destination, return_menu_item)
    pw_min = config.register.password.min_length if config.register and config.register.password else null
    if pw_min and pw_min is not null and len(new_pw) < int(pw_min):
      await show_message_box(user, f"Password must be at least {pw_min} characters.",
                           title="Error", outline_fg=red, outline_fg_br=True,
                           fg=white, fg_br=True, bg=black)
      return await edit_settings(user, target_handle, return_destination, return_menu_item)
    import bcrypt
    _bcrypt_rounds = int(config.bcrypt_rounds) if config.bcrypt_rounds else 8
    salt = bcrypt.gensalt(rounds=_bcrypt_rounds)
    pw_hash = bcrypt.hashpw(new_pw.encode("utf-8"), salt)
    db_con.execute(
      "UPDATE USERS SET password_hash = ?, password_salt = ? WHERE handle = ? COLLATE NOCASE",
      (pw_hash, salt, target_handle)
    )
    db_con.commit()
    from logger import log as _log
    if is_self:
      _log.info("User '%s' changed their password", target_handle)
    else:
      _log.info("Sysop '%s' changed password for '%s'", user.handle, target_handle)

  # Remove password fields from values (they're not YAML settings)
  # (they were never added to values since they're outside SETTINGS_KEYS)

  # Write to user YAML config
  os.makedirs(str(user_conf_dir), exist_ok=True)

  # Load existing config to preserve any keys we don't show in settings
  existing = {}
  if os.path.exists(user_conf_path):
    try:
      with open(user_conf_path, "r") as f:
        existing = _yaml.load(f) or {}
    except Exception:
      pass

  existing.update(values)

  with open(user_conf_path, "w") as f:
    _yaml.dump(existing, f)

  # Apply changes to the live session if the target user is online
  live_user = global_data.users.get(target_handle.lower())
  if live_user:
    live_user.encoding = enc
    if is_self:
      _set_connection_encoding(live_user)

    # Reload config
    try:
      conf1 = gc(path=user_conf_path)
    except Exception:
      conf1 = gc()
    live_user.conf = ConfigView(conf1, gc())

    # Apply profile fields
    live_user.email = values.get("email") or None
    live_user.age = values.get("age") or None
    live_user.sex = values.get("sex") or None
    live_user.location = values.get("location") or None
    live_user.bio = values.get("bio") or None

  if not is_self:
    from logger import log
    log.info("Sysop '%s' edited settings for '%s'", user.handle, target_handle)

  await show_message_box(user, f"Settings for {target_handle} saved successfully.",
                         title="Settings", outline_fg=green, outline_fg_br=True,
                         fg=white, fg_br=True, bg=black)

  return RetVals(status=success, next_destination=return_destination, next_menu_item=return_menu_item)


async def run(user, destination, menu_item=None):
  from common import Destinations
  return await edit_settings(user, user.handle, Destinations.main)
