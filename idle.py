"""Idle timeout: IdleMonitor wraps a connection's reader, warns a caller who
has typed nothing for a while, and disconnects one who still doesn't.

The timeout is config.idle_timeout (config.modem.idle_timeout for modem
callers), the warning comes config.idle_warning seconds before it; 0 turns
either off.
"""

import asyncio

from config import get_config
from definitions import Disconnected, null, white, black, red
from logger import log

config = get_config()


def _get_idle_timeout(user):
  """Return the idle timeout in seconds for this user, or 0 to disable."""
  if getattr(user, 'connection_type', 'telnet') == 'modem':
    t = config.modem.idle_timeout if config.modem else null
  else:
    t = config.idle_timeout if config.idle_timeout else null
  if t and t is not null:
    try:
      return int(t)
    except (ValueError, TypeError):
      pass
  return 0


def _get_idle_warning():
  """Return seconds before timeout to show the warning, or 0 to disable."""
  t = config.idle_warning if config.idle_warning else null
  if t and t is not null:
    try:
      return int(t)
    except (ValueError, TypeError):
      pass
  return 0


class IdleMonitor:
  """Wraps a reader to track last activity and raise Disconnected on idle timeout.
  If idle_warning is configured, shows a popup before disconnecting."""

  def __init__(self, reader, user):
    self._reader = reader
    self._user = user
    self._last_activity = asyncio.get_event_loop().time()
    self._in_warning = False  # True while the warning popup is showing

  def _touch(self):
    self._last_activity = asyncio.get_event_loop().time()

  async def _disconnect(self):
    """Send disconnect message and raise Disconnected."""
    log.info("Idle timeout for user %s", getattr(self._user, 'handle', '?'))
    try:
      self._user.writer.write("\r\n*** Disconnected due to inactivity. ***\r\n")
      await self._user.writer.drain()
    except Exception:
      pass
    raise Disconnected()

  async def _show_warning_popup(self, seconds_left):
    """Show a popup warning. The popup's input loop calls read() recursively,
    which sees _in_warning=True and does a plain timed wait without nesting."""
    self._in_warning = True
    self._last_activity = asyncio.get_event_loop().time()  # reset so inner reads use warning_time
    try:
      from input_fields import show_message_box
      if self._user.screen and self._user.screen_width:
        await show_message_box(
          self._user,
          f"Are you still there?\nYou will be disconnected in {seconds_left} seconds.\nPress any key to stay connected.",
          title="Idle Warning",
          outline_fg=red, outline_fg_br=True,
          fg=white, fg_br=True, bg=black,
        )
        # User pressed a key — they're still there
        self._touch()
        return True  # user responded
      else:
        # No screen yet — fall back to raw text
        self._user.writer.write(
          f"\r\n*** Are you still there? Disconnecting in {seconds_left} seconds. Press any key. ***\r\n"
        )
        await self._user.writer.drain()
        try:
          data = await asyncio.wait_for(self._reader.read(1), timeout=seconds_left)
        except asyncio.TimeoutError:
          return False  # no response
        if data:
          self._touch()
        return True
    except Disconnected:
      # Inner read() timed out during the popup — propagate
      raise
    except Exception:
      return False
    finally:
      # (also when the popup is cancelled: a page arriving over it, say)
      self._in_warning = False

  async def read(self, n=1):
    timeout = _get_idle_timeout(self._user)
    if timeout <= 0:
      data = await self._reader.read(n)
      if data:
        self._touch()
      return data

    # If we're inside the warning popup, just do a plain timed wait
    # with the remaining timeout — no nested popups
    if self._in_warning:
      remaining = timeout - (asyncio.get_event_loop().time() - self._last_activity)
      if remaining <= 0:
        await self._disconnect()
      try:
        data = await asyncio.wait_for(self._reader.read(n), timeout=remaining)
      except asyncio.TimeoutError:
        await self._disconnect()
      if data:
        self._touch()
      return data

    # Normal path — check if we should warn or disconnect
    now = asyncio.get_event_loop().time()
    elapsed = now - self._last_activity
    remaining = timeout - elapsed
    warning_time = _get_idle_warning()

    if remaining <= 0:
      await self._disconnect()

    # If warning is configured, split the wait into pre-warning and warning phases
    if warning_time > 0 and remaining > warning_time:
      wait_until_warning = remaining - warning_time
      try:
        data = await asyncio.wait_for(self._reader.read(n), timeout=wait_until_warning)
      except asyncio.TimeoutError:
        # Time to warn — show popup
        responded = await self._show_warning_popup(warning_time)
        if not responded:
          await self._disconnect()
        # User responded to warning — popup consumed the keypress,
        # so loop back to wait for the next real key
        return await self.read(n)
      if data:
        self._touch()
      return data

    # No warning configured, or not enough time left for warning — just wait
    try:
      data = await asyncio.wait_for(self._reader.read(n), timeout=remaining)
    except asyncio.TimeoutError:
      await self._disconnect()
    if data:
      self._touch()
    return data

  async def read_raw(self, n=1):
    """Read without the idle timeout or its warning popup (a file transfer
    has its own timeouts, and a popup would land in its data); what arrives
    still counts as activity."""
    data = await self._reader.read(n)
    if data:
      self._touch()
    return data

  # The connection's text encoding belongs to the reader underneath: setting
  # it here must reach that reader (common._set_connection_encoding), not
  # just this wrapper, which is what __getattr__ alone would let happen.
  # (Calls, such as a serial reader's set_encoding, go through __getattr__.)
  @property
  def fn_encoding(self):
    return self._reader.fn_encoding

  @fn_encoding.setter
  def fn_encoding(self, fn):
    self._reader.fn_encoding = fn

  def __getattr__(self, name):
    return getattr(self._reader, name)
