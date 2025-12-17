default_config = "DirtyFork.yaml"

import asyncio, sys, traceback

import telnetlib3, serial

from config import get_config
config = get_config(path=sys.argv[1] if len(sys.argv)>1 else default_config, main=True)   # this has to run before any other DirtyFork module is loaded.

from common import *
from modules import *

async def bbs_msg(user): # todo
  if not user.cur_bbs_box:
    # make box
    pass
  # make an InputField and pass allow_edit=False
  # remember value of ansi_wrap and reset it afterward
  # do we pause everything else while this is showing, or let it scroll behind it simultaneously?
  # move to user.cur_bbs_row, user.cur_bbs_col
  # write message with word wrap
  # remember cur_bbs_msg contents and show them before appending?
  # have option to use ansi region scrolling instead of a manual box
  # include close button for the box that uses esc[1000h, but also allow pressing esc to close

#configuration variables can be accessed as config["foo"]["bar"]["baz"] or config.foo.bar.baz. nonexistent variables return None

users_logging_in = set()
users = {}

async def user_loop(reader, writer): # todo: users will probably not be able to see the err_msg's for long enough.
  user = User(reader, writer)
  global_data.users_logging_in.add(user)
  r = RetVals(next_destination=Destinations.login)  
  # todo uh oh, sometimes next_destination is treated as a string and sometimes it's treated as the destination object itself, i think. i remember seeing do_destination looking up getattr and such. 
  next_destination, next_menu_item = login, None
  while True: 
    try: 
      r = await Destinations.user_director(user, next_destination, next_menu_item)
      next_destination = r.next_destination
      next_menu_item = r.next_menu_item
      if r.status==fail:
        await send(user, f"There was an error.\n"
                    "Destination: {r.destination}{('/'+r.menu_item) if r.menu_item else ''}\n"
                    "Error message: r.err_msg)")
        user.destination_history.append(r)
        continue
      user.destination_history.append(r)
      r = await do_destination(user, r.next_destination, next_menu_item)
      if r.status==fail:
        send(user, f"There was an error.\n"
                    "Destination: {r.destination}{('/'+r.menu_item) if r.menu_item else ''}\n"
                    "Error message: r.err_msg)")
      next_destination = r.next_destination
      next_menu_item = r.next_menu_item
    except Disconnected as e:
      global_data.users.remove(user) # i'm imagining the only reference to the instantiation of the class, menu or input destination she was in was in user.cur_destination, and i just removed that
      break
    except Exception as e:
      r.status=fail
      r.errmsg=="There was an error:" + traceback.format_exc() 
      if "debug" in user.keys:
        await send(user, "There was an error:" + traceback.format_exc())
      else:
        await send(user, "There was an error.")
    user.destination_history.append(RetVals(destination=next_destination, menu_item=next_menu_item, status=r.status, err_msg=r.err_msg))

async def main():
  server = await telnetlib3.create_server(host=config.hostname, port=config.port, shell=user_loop)
  await server.wait_closed()

if __name__=="__main__":
  asyncio.run(main())
