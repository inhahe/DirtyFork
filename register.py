import json
import os
import time
import re
import bcrypt
import sqlite3

import yaml

from input_fields import InputFields, InputField, show_message_box
from input_output import send, send_wrapped, ansi_color, ansi_move_deferred, ansi_cls
from definitions import RetVals, success, fail, cr, lf, null, white, black, red
from config import get_config
import paths

config = get_config()
register_config = get_config(path=paths.resolve_project("register.yaml"))
time_zones = json.load(open(os.path.join(os.path.dirname(__file__), "time_zones.json"), "r"))

FIELD_NAMES = ["handle", "password", "age", "sex", "location", "time_zone", "email", "bio"]


def _validate_timezone(tz_raw):
  """Validate a timezone string. Accepts abbreviations (EST, PST) or UTC offsets (UTC+8, UTC-5:30).
  Returns (valid: bool, error_msg: str or None)."""
  tz = tz_raw.strip().upper()
  # Check abbreviation first
  if tz in time_zones:
    return True, None
  # Check UTC offset format: UTC+N, UTC-N, UTC+N:MM, UTC-N:MM
  if tz.startswith("UTC") or tz.startswith("GMT"):
    offset_part = tz[3:]
    if not offset_part:
      return True, None  # plain UTC/GMT
    if offset_part[0] in ('+', '-'):
      parts = offset_part[1:].split(':')
      try:
        hours = int(parts[0])
        mins = int(parts[1]) if len(parts) > 1 else 0
        if 0 <= hours <= 14 and 0 <= mins <= 59:
          return True, None
      except (ValueError, IndexError):
        pass
  return False, f"Unknown time zone '{tz_raw}'. Use an abbreviation (EST, PST, UTC) or offset (UTC+8, UTC-5:30)."


def _parse_timezone(tz_raw):
  """Parse a timezone string into (letters, hours, minutes).
  Returns (tz_letters, tz_hours, tz_mins)."""
  tz = tz_raw.strip().upper()
  # Abbreviation lookup
  if tz in time_zones:
    offset = time_zones[tz]
    return tz, offset[0], offset[1]
  # UTC/GMT offset
  if tz.startswith("UTC") or tz.startswith("GMT"):
    prefix = tz[:3]
    offset_part = tz[3:]
    if not offset_part:
      return prefix, 0, 0
    sign = 1 if offset_part[0] == '+' else -1
    parts = offset_part[1:].split(':')
    try:
      hours = int(parts[0])
      mins = int(parts[1]) if len(parts) > 1 else 0
      return tz, sign * hours, mins  # mins always positive, hours carry the sign
    except (ValueError, IndexError):
      return tz, 0, 0
  return tz, 0, 0


async def run(user, destination, menu_item=None):
  inputFields = InputFields(user)

  # Clear screen
  await ansi_cls(user)

  # Title
  ansi_color(user, fg=white, bg=black, fg_br=True, bg_br=False)
  await send(user, "New User Registration" + cr + lf + cr + lf, drain=False)
  # Display header label
  if register_config.label:
    ansi_color(user, fg=white, bg=black, fg_br=False, bg_br=False)
    await send(user, register_config.label + cr + lf, drain=False)

  # Right-align all labels so input fields line up
  max_label_len = max(len(str(getattr(register_config, name).label or "")) for name in FIELD_NAMES)

  # Create an InputField for each registration field
  for name in FIELD_NAMES:
    field_conf = getattr(register_config, name)

    if field_conf.blurb:
      ansi_color(user, fg=white, bg=black, fg_br=False, bg_br=False)
      await send_wrapped(user, str(field_conf.blurb), drain=False)
      await send(user, cr + lf, drain=False)

    # Reset colors and right-justify the label
    ansi_color(user, fg=white, bg=black, fg_br=False, bg_br=False)
    label = str(field_conf.label or "")
    padded_label = label.rjust(max_label_len)
    await send(user, padded_label, drain=True)

    # Resolve the styling config from input_fields.yaml based on the field's type
    style_conf = getattr(config.input_fields, field_conf.type)

    kwargs = dict(
      conf=style_conf,
      width=field_conf.width,
      max_length=field_conf.max_length,
    )

    # Pass optional multiline parameters if present
    if field_conf.height:
      kwargs["height"] = field_conf.height
    if field_conf.max_lines:
      kwargs["max_lines"] = field_conf.max_lines
    if field_conf.word_wrap:
      kwargs["word_wrap"] = field_conf.word_wrap

    await inputFields.add_field(**kwargs)
    await send(user, cr + lf, drain=False)

  # Add Submit and Login buttons side by side
  submit_btn = await inputFields.add_button("submit", content="Submit")
  # Position the abort button next to the submit button on the same row.
  # create() will add +1 to cur_row and cur_col if outline is True,
  # so we set cur_row/cur_col to the pre-outline position.
  # The outline right edge is at col_offset + width (since col_offset already has +1 for outline).
  # We want a gap then the next outline starts.
  abort_col = submit_btn.col_offset + submit_btn.width + (1 if submit_btn.outline else 0) + 1
  abort_row = submit_btn.row_offset - (1 if submit_btn.outline else 0)
  await ansi_move_deferred(user, row=abort_row, col=abort_col, drain=True)
  await inputFields.add_button("abort", content="Abort")

  # Loop: run the form, validate, show errors, repeat until success or abort
  start_field = 0
  while True:
    r = await inputFields.run(start_index=start_field)
    start_field = 0  # reset for next iteration unless validation sets it

    # If the user pressed the Login button, abort registration
    if r.button == "abort":
      return RetVals(status=fail)

    # Map field results to names
    values = {}
    for i, name in enumerate(FIELD_NAMES):
      values[name] = r.fields[i].content

    # --- Validation ---
    errors = []
    first_bad_field = None  # index into FIELD_NAMES

    if not values["handle"] or not values["handle"].strip():
      errors.append("Handle is required.")
      if first_bad_field is None: first_bad_field = FIELD_NAMES.index("handle")
    else:
      con = sqlite3.connect(paths.resolve_data(str(config.database)))
      cur = con.cursor()
      cur.execute("SELECT id FROM USERS WHERE handle = ? COLLATE NOCASE LIMIT 1", (values["handle"],))
      if cur.fetchone():
        errors.append("That handle is already taken.")
        if first_bad_field is None: first_bad_field = FIELD_NAMES.index("handle")
      con.close()

    handle_min = register_config.handle.min_length or 1
    if values["handle"] and len(values["handle"].strip()) < handle_min:
      errors.append(f"Handle must be at least {handle_min} characters.")
      if first_bad_field is None: first_bad_field = FIELD_NAMES.index("handle")

    password_min = register_config.password.min_length or 6
    if not values["password"] or len(values["password"]) < password_min:
      errors.append(f"Password must be at least {password_min} characters.")
      if first_bad_field is None: first_bad_field = FIELD_NAMES.index("password")

    tz_raw = values["time_zone"].strip() if values["time_zone"] else ""
    if not tz_raw:
      errors.append("Time zone is required.")
      if first_bad_field is None: first_bad_field = FIELD_NAMES.index("time_zone")
    else:
      tz_valid, tz_err = _validate_timezone(tz_raw)
      if not tz_valid:
        errors.append(tz_err)
        if first_bad_field is None: first_bad_field = FIELD_NAMES.index("time_zone")

    if errors:
      error_text = "\n".join(errors)
      await show_message_box(user, error_text, title="Registration Error",
                             fg=white, fg_br=True, bg=black,
                             outline_fg=red, outline_fg_br=True)
      # Loop back with cursor on the first bad field
      start_field = first_bad_field if first_bad_field is not None else 0
      continue

    # --- Validation passed — insert into database ---
    break

  password_bytes = values["password"].encode("utf-8")
  salt = bcrypt.gensalt()
  password_hash = bcrypt.hashpw(password_bytes, salt)

  cmd_line_handle = re.sub(r"[ ,.\-]", "_", values["handle"])

  con = sqlite3.connect(paths.resolve_data(str(config.database)))
  con.row_factory = sqlite3.Row
  cur = con.cursor()

  # Ensure unique cmd_line_handle
  cur.execute(
    "SELECT cmd_line_handle FROM USERS WHERE cmd_line_handle LIKE ? ESCAPE '$' COLLATE NOCASE",
    (cmd_line_handle.replace("_", "$_") + "%",)
  )
  existing = [row[0].lower() for row in cur.fetchall()]
  n = 1
  while (cmd_line_handle.lower() + str(n)) in existing:
    n += 1
  cmd_line_handle = cmd_line_handle + str(n)

  # Database: only credentials and identity
  cur.execute(
    """INSERT INTO USERS (handle, cmd_line_handle, password_hash, password_salt, time_created)
       VALUES (?, ?, ?, ?, ?)""",
    (values["handle"], cmd_line_handle, password_hash, salt, int(time.time()))
  )
  con.commit()
  con.close()

  # YAML: profile data and preferences
  user_conf_dir = paths.resolve_data(str(config.user_configs or "user_configs"))
  os.makedirs(user_conf_dir, exist_ok=True)
  user_conf_path = os.path.join(user_conf_dir, values["handle"] + ".yaml")

  tz_letters, tz_hours, tz_mins = _parse_timezone(values["time_zone"] or "")

  user_settings = {
    "encoding": getattr(user, 'encoding', 'cp437'),
    "email": values["email"] or "",
    "sex": values["sex"] or "",
    "age": values["age"] or "",
    "location": values["location"] or "",
    "bio": values["bio"] or "",
    "time_zone": tz_letters,
    "time_zone_hours": tz_hours,
    "time_zone_mins": tz_mins,
  }
  with open(user_conf_path, "w") as f:
    yaml.dump(user_settings, f, default_flow_style=False)

  # Auto-login: set up the user session so they don't have to log in again
  from common import Destinations, setup_user_session, con as db_con
  db_cur = db_con.cursor()
  db_cur.execute("SELECT id, handle, time_created FROM USERS WHERE handle = ? COLLATE NOCASE LIMIT 1",
                 (values["handle"],))
  row = db_cur.fetchone()
  if row:
    setup_user_session(user, row["handle"], row["id"], row["time_created"])

  await send(user, cr + lf + "Registration successful! Welcome aboard!" + cr + lf, drain=True)

  return RetVals(status=success, next_destination=Destinations.main)
