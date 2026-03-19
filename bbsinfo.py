"""About this BBS — shows BBS info screen."""

from input_fields import show_message_box
from input_output import get_input_key
from definitions import RetVals, success, null, white, black, cyan
from config import get_config
import paths

config = get_config()


async def run(user, dest_conf, menu_item=None):
  from common import Destinations, global_data, con, show_screen

  # If an ANSI/BIN screen file is configured, show it and wait for a keypress
  if config.bbs_info_screen:
    await show_screen(user, str(config.bbs_info_screen))
    await get_input_key(user)
    return RetVals(status=success, next_destination=Destinations.main)

  # Otherwise show the auto-generated info popup
  lines = []

  # BBS name
  bbs_name = str(config.bbs_name) if config.bbs_name else "Unnamed BBS"
  lines.append(bbs_name)
  lines.append("=" * len(bbs_name))
  lines.append("")

  # Description
  if config.bbs_description:
    lines.append(str(config.bbs_description))
    lines.append("")

  # Sysop — try sysop_name, then sysop_handle, then look up who has the sysop key
  sysop_name = str(config.sysop_name) if config.sysop_name else None
  if not sysop_name and config.sysop_handle:
    sysop_name = str(config.sysop_handle)
  if not sysop_name:
    try:
      row = con.execute(
        "SELECT u.handle FROM USERS u JOIN USER_KEYS k ON u.id = k.user_id WHERE k.key = 'sysop' LIMIT 1"
      ).fetchone()
      if row:
        sysop_name = row["handle"]
    except Exception:
      pass
  if sysop_name:
    lines.append(f"Sysop:        {sysop_name}")

  # Location
  if config.bbs_location:
    lines.append(f"Location:     {config.bbs_location}")

  # Established
  if config.bbs_established:
    lines.append(f"Established:  {config.bbs_established}")

  # Connection info
  host = str(config.hostname) if config.hostname else "0.0.0.0"
  port = str(config.port) if config.port else "23"
  if host == "0.0.0.0":
    lines.append(f"Telnet:       port {port}")
  else:
    lines.append(f"Telnet:       {host}:{port}")

  # Phone
  if config.bbs_phone:
    lines.append(f"Phone:        {config.bbs_phone}")

  # Website
  if config.bbs_website:
    lines.append(f"Website:      {config.bbs_website}")

  # Stats
  lines.append("")
  try:
    user_count = con.execute("SELECT COUNT(*) FROM USERS").fetchone()[0]
    lines.append(f"Users:        {user_count} registered")
  except Exception:
    pass

  online_count = len(global_data.users)
  lines.append(f"Online now:   {online_count}")

  # Software
  lines.append("")
  lines.append("Software:     DirtyFork BBS by inhahe")
  lines.append("Source:       github.com/inhahe/DirtyFork")

  text = "\n".join(lines)
  await show_message_box(user, text, title=f" About {bbs_name} ",
                         fg=white, fg_br=True, bg=black,
                         outline_fg=cyan, outline_fg_br=True)

  return RetVals(status=success, next_destination=Destinations.main)
