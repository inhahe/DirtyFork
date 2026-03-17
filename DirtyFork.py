default_config = "DirtyFork.yaml"

import asyncio, logging, sys, traceback

import telnetlib3

# Parse --debug flag before anything else
debug_mode = "--debug" in sys.argv
config_args = [a for a in sys.argv[1:] if a != "--debug"]

from config import get_config
config = get_config(path=config_args[0] if config_args else default_config, main=True)

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

async def user_loop(reader, writer):
  user = User(reader, writer)
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
    global_data.users_logging_in.discard(user)
    handle_key = getattr(user, 'handle', None)
    if handle_key and handle_key.lower() in global_data.users:
      del global_data.users[handle_key.lower()]
    try:
      writer.close()
    except Exception:
      pass

async def main():
  server = await telnetlib3.create_server(host=config.hostname, port=config.port, shell=user_loop, encoding='cp437', timeout=0)
  log.info("BBS listening on %s:%s", config.hostname, config.port)
  await server.wait_closed()

if __name__=="__main__":
  asyncio.run(main())
