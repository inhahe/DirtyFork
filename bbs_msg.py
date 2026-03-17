"""
BBS Messaging — send popup messages to users, including users in door sessions.

The popup overlays on top of whatever the user is currently seeing (including
door game output), waits for them to dismiss it, then restores the screen
from user.screen (which the ANSI emulator keeps up to date during door sessions).

Users can opt out via settings in their config:
  allow_door_popups: false  — blocks popups while in a door game
  allow_pages: false        — blocks /page from other users
  blocked_users: [handle1, handle2]  — blocks specific users
"""

from input_fields import show_message_box
from definitions import white, black, green, cyan, null, RetVals, success, fail


def _get_conf_bool(user, key, default=True):
  """Get a boolean config value from user.conf, defaulting if not set."""
  conf = getattr(user, 'conf', null)
  if not conf or conf is null:
    return default
  val = conf[key]
  if val is null or val is None:
    return default
  if isinstance(val, bool):
    return val
  if isinstance(val, str):
    return val.lower() in ("true", "yes", "1", "on")
  return bool(val)


def _get_blocked_users(user):
  """Get the list of blocked user handles (lowercase) from user.conf."""
  conf = getattr(user, 'conf', null)
  if not conf or conf is null:
    return set()
  blocked = conf.blocked_users
  if not blocked or blocked is null:
    return set()
  try:
    return {str(h).lower() for h in blocked}
  except (TypeError, ValueError):
    return set()


def check_can_page(target, from_handle=None):
  """Check whether a popup/page can be sent to target.

  Returns (allowed: bool, reason: str or None).
  reason is a human-readable explanation when not allowed.
  """
  # No screen set up yet
  if not target.screen or not target.screen_width:
    return False, "User is not fully connected."

  # Check if pages are allowed
  if not _get_conf_bool(target, 'allow_pages', default=True):
    return False, f"{target.handle} has paging disabled."

  # Check if BBS messages are allowed
  if not _get_conf_bool(target, 'allow_bbs_messages', default=True):
    return False, f"{target.handle} has BBS messages disabled."

  # Check if door popups are allowed (only matters if they're in a door)
  if target.in_door:
    if not _get_conf_bool(target, 'allow_door_popups', default=True):
      return False, f"{target.handle} has do-not-disturb enabled during door games."

  # Check if the sender is blocked
  if from_handle:
    blocked = _get_blocked_users(target)
    if from_handle.lower() in blocked:
      return False, f"{target.handle} is blocking you."

  return True, None


async def send_popup(user, text, title=null, from_user=null,
                     fg=white, fg_br=True, bg=black, bg_br=False,
                     outline_fg=cyan, outline_fg_br=True,
                     outline_bg=black, outline_bg_br=False,
                     from_handle=None, skip_checks=False):
  """Send a popup message to a user. Works even if they're in a door game.

  If a popup is already showing, the new one is queued and will display
  after the current popup is dismissed.

  Returns (shown: bool, reason: str or None).
  reason is set when the popup was not shown (permission denied).
  Queued popups return (True, None) — they will be shown eventually.
  """
  if not skip_checks:
    allowed, reason = check_can_page(user, from_handle=from_handle)
    if not allowed:
      return False, reason

  # Build title
  if from_user and from_user is not null:
    if title and title is not null:
      title = f"Message from {from_user}: {title}"
    else:
      title = f"Message from {from_user}"

  popup_kwargs = dict(text=text, title=title, fg=fg, fg_br=fg_br, bg=bg, bg_br=bg_br,
                      outline_fg=outline_fg, outline_fg_br=outline_fg_br,
                      outline_bg=outline_bg, outline_bg_br=outline_bg_br)

  # If already showing a popup, queue this one
  if user._in_popup:
    user.popup_queue.append(popup_kwargs)
    return True, None

  # Show this popup, then drain the queue
  user._in_popup = True

  was_in_door = user.in_door
  if was_in_door and user.popup_event:
    user.popup_event.set()

  try:
    r = await show_message_box(user, queued_count=len(user.popup_queue), **popup_kwargs)

    # Drain queued popups (unless user aborted)
    while user.popup_queue and r != "abort":
      next_kwargs = user.popup_queue.pop(0)
      r = await show_message_box(user, queued_count=len(user.popup_queue), **next_kwargs)

    # Clear any remaining if aborted
    user.popup_queue.clear()
  finally:
    user._in_popup = False
    if was_in_door and user.popup_event:
      user.popup_event.clear()

  return True, None


async def send_popup_to_all(text, title=null, from_user=null, exclude=None, **kwargs):
  """Send a popup to all logged-in users (e.g., system announcement).
  System broadcasts skip permission checks.
  """
  from common import global_data
  if exclude is None:
    exclude = set()
  elif not isinstance(exclude, set):
    exclude = {exclude}

  for handle, user in list(global_data.users.items()):
    if user not in exclude:
      await send_popup(user, text, title=title, from_user=from_user,
                       skip_checks=True, **kwargs)


async def send_popup_to_user(handle, text, title=null, from_user=null,
                             from_handle=None, **kwargs):
  """Send a popup to a specific user by handle.

  Returns (shown: bool, reason: str or None).
  """
  from common import global_data
  user = global_data.users.get(handle.lower())
  if not user:
    return False, f"User '{handle}' is not online."
  return await send_popup(user, text, title=title, from_user=from_user,
                          from_handle=from_handle, **kwargs)
