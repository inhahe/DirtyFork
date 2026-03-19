default_config = "DirtyFork.yaml"

import asyncio, logging, os, sys, traceback

import telnetlib3

# Parse flags before anything else so paths are set before any import touches the filesystem
debug_mode = "--debug" in sys.argv

# Extract --data-dir PATH and any positional config-path argument
_remaining = [a for a in sys.argv[1:] if a != "--debug"]
data_dir_arg = None
config_path_arg = None
_i = 0
while _i < len(_remaining):
    if _remaining[_i] == "--data-dir" and _i + 1 < len(_remaining):
        data_dir_arg = _remaining[_i + 1]
        _i += 2
    elif not _remaining[_i].startswith("--"):
        config_path_arg = _remaining[_i]
        _i += 1
    else:
        _i += 1

if "--help" in sys.argv or "-h" in sys.argv:
    print(f"Usage: python DirtyFork.py [config] [--data-dir PATH] [--debug]")
    print()
    print(f"  config          Path to config file (default: {default_config} in data dir)")
    print(f"  --data-dir PATH Directory for data files: config, database, logs, user configs")
    print(f"                  (default: current working directory)")
    print(f"  --debug         Enable verbose debug logging")
    sys.exit(0)

import paths
if data_dir_arg:
    paths.data_dir = os.path.abspath(data_dir_arg)

from config import get_config
_config_path = config_path_arg if config_path_arg else paths.resolve_data(default_config)
config = get_config(path=_config_path, main=True)

from logger import log, setup_logging
setup_logging()

# Suppress telnetlib3's noisy debug logging unless --debug is passed
if not debug_mode:
  logging.getLogger("telnetlib3").setLevel(logging.WARNING)

from common import User, Destinations, global_data, user_director
from definitions import RetVals, success, fail, new_user, cr, lf, null, Disconnected, white, black, red
from input_output import send

async def bbs_msg(user): # todo
  if not user.cur_bbs_box:
    # make box
    pass


# ---------------------------------------------------------------------------
# Idle timeout
# ---------------------------------------------------------------------------

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


class _IdleMonitor:
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
        self._in_warning = False
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
          self._in_warning = False
          return False  # no response
        if data:
          self._touch()
        self._in_warning = False
        return True
    except Disconnected:
      # Inner read() timed out during the popup — propagate
      self._in_warning = False
      raise
    except Exception:
      self._in_warning = False
      return False

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

  def __getattr__(self, name):
    return getattr(self._reader, name)


# ---------------------------------------------------------------------------
# User session
# ---------------------------------------------------------------------------

async def user_loop(reader, writer, connection_type="telnet"):
  user = User(reader, writer)
  user.connection_type = connection_type

  # Wrap reader with idle monitor
  user.reader = _IdleMonitor(reader, user)

  try:
    peer = writer.get_extra_info("peername", ("?",))[0] if connection_type == "telnet" else connection_type
  except Exception:
    peer = "?"
  log.info("New %s connection from %s", connection_type, peer)

  global_data.users_logging_in.add(user)
  try:
    # Terminal setup — only once per connection
    await Destinations.setup_terminal(user)

    # Login phase — handles "new" registration internally
    try:
      r = await Destinations.login(user)
    except Disconnected:
      raise
    except Exception:
      log.error("Error during login: %s", traceback.format_exc())
      from input_fields import show_message_box
      if user.screen and user.screen_width:
        await show_message_box(user, traceback.format_exc(), title="Login Error",
                               fg=white, fg_br=True, bg=black,
                               outline_fg=red, outline_fg_br=True,
                               word_wrap=False, max_width=user.screen_width - 4)
      else:
        await send(user, "\r\nAn error occurred during login.\r\n")
      return
    if r.status != success:
      if user.screen and user.screen_width:
        from input_fields import show_message_box
        await show_message_box(user, getattr(r, 'err_msg', 'Unknown error'), title="Login Failed",
                               fg=white, fg_br=True, bg=black,
                               outline_fg=red, outline_fg_br=True)
      else:
        await send(user, f"\r\nLogin failed: {getattr(r, 'err_msg', 'Unknown error')}\r\n")
      return
    log.info("User '%s' logged in (%s)", user.handle, connection_type)
    next_destination = r.next_destination if r.next_destination else Destinations.main
    next_menu_item = getattr(r, 'next_menu_item', null)

    # Main destination loop — user_director handles key checks, errors, fallbacks, and history
    while True:
      r = await user_director(user, next_destination, next_menu_item)
      next_destination = r.next_destination
      next_menu_item = getattr(r, 'next_menu_item', null)
  except Disconnected:
    pass
  except Exception as e:
    log.error("Unhandled error for user %s: %s: %s", getattr(user, 'handle', '?'), type(e).__name__, e)
  finally:
    handle = getattr(user, 'handle', None)
    if handle:
      log.info("User '%s' logged off (%s)", handle, connection_type)
    else:
      log.info("Connection closed before login (%s)", connection_type)
    global_data.users_logging_in.discard(user)
    if handle and handle.lower() in global_data.users:
      del global_data.users[handle.lower()]

    # Modem: hang up before closing
    if connection_type == "modem":
      try:
        from modem import hangup
        await hangup(writer)
      except Exception:
        pass

    try:
      writer.close()
    except Exception:
      pass


# ---------------------------------------------------------------------------
# Modem listener
# ---------------------------------------------------------------------------

async def modem_listener(port, baudrate, init_string):
  """Listen for incoming modem calls on a single port and spawn user sessions."""
  from modem import wait_for_call

  log.info("Modem listener starting on %s at %d baud", port, baudrate)

  while True:
    try:
      result = await wait_for_call(port, baudrate, init_string)
      if result:
        reader, writer = result
        log.info("Modem: incoming call on %s, starting session", port)
        asyncio.create_task(user_loop(reader, writer, connection_type="modem"))
    except Exception as e:
      log.error("Modem listener error on %s: %s: %s", port, type(e).__name__, e)
      await asyncio.sleep(5)


def _get_modem_ports():
  """Parse modem port config. Returns list of (port, baudrate, init_string) tuples."""
  if not config.modem:
    return []

  init_string = str(config.modem.init_string) if config.modem.init_string else "ATZ"
  default_baudrate = int(config.modem.baudrate) if config.modem.baudrate else 115200

  # New format: modem.ports list
  if config.modem.ports:
    ports = []
    for p in config.modem.ports:
      port = str(p.port) if p.port else None
      if not port:
        continue
      baud = int(p.baudrate) if p.baudrate else default_baudrate
      init = str(p.init_string) if p.init_string else init_string
      ports.append((port, baud, init))
    return ports

  # Legacy format: single modem.port
  if config.modem.port:
    return [(str(config.modem.port), default_baudrate, init_string)]

  return []


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
  # Telnet server
  server = await telnetlib3.create_server(host=config.hostname, port=config.port, shell=user_loop, encoding='cp437', timeout=0)
  log.info("BBS listening on %s:%s", config.hostname, config.port)

  # Modem listeners (one task per port)
  modem_ports = _get_modem_ports()
  for port, baudrate, init_string in modem_ports:
    asyncio.create_task(modem_listener(port, baudrate, init_string))
  if modem_ports:
    log.info("Modem listeners started on %d port(s)", len(modem_ports))

  await server.wait_closed()

if __name__=="__main__":
  asyncio.run(main())
