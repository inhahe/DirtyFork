import asyncio, sqlite3, collections, re
from importlib import import_module
from collections import deque

import bcrypt

from output import *
from keyboardcodes import *
from config import *
from input_fields import * # todo: we have a circular import. supposedly that's a very bad thing.
import menu
from modules import *
from definitions import *

config = get_config()

con = sqlite3.connect(config.database)
con.row_factory = sqlite3.Row 
cur = con.cursor()

class Disconnected(Exception):
  def __init__(self, user):
    self.user = user

class Char: 
  def __init__(self, fg=7, bg=0, fg_br=False, bg_br=False, char=" "):
    self.fg = fg
    self.bg = bg
    self.fg_br = fg_br
    self.bg_br = bg_br
    self.char = char

class GlobalData: 
  def __init__(self):
    self.users = {}
    self.users_logging_in = set()
  
global_data = GlobalData()

class User:
  def __init__(self, reader, writer):
    for k, v in config.user_defaults:
      setattr(self, k, v)
    self.reader = reader
    self.writer = writer
    self.screen_width = None
    self.screen_height = None
    self.handle = None
    self.user_id = None
    self.keys = set()
    self.cur_input = None
    self.cur_destination = Destinations.login # may not be completely factually true
    self.cur_wrap = True
    self.cur_in_input = False
    self.failed_login_attempts = 0
    self.screen_history = collections.deque()
    self.email = None
    self.sex = None # Haha
    self.age = None
    self.location = None
    self.time_created = None
    self.login_tries = []
    self.config = None

line_pos_re = re.compile(b'\x1b\\[(\\d+);(\\d+)R')
email_re = re.compile(b'''(?:[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+(?:\.[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9\x2d]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])''')
# what the hell is this? to : does it work?
handle_re = re.compile("[A-Za-z0-9_]") # i won't allow spaces because that could mess up door games that require a handle in the command line. should I allow any special characters?
                                       # todo: on second thought, handles with spaces is more fun. What should I do abotu the door games?
def check_keys(user, destination, menu_item=None):
  r = RetVals()
  item = menu_item or destination # if no menu_item specified, check keys of destination. destination could be a menu or something else.
  lacking_keys = (item.white_keys or set()) - user.keys
  bad_keys = (item.black_keys or set())  & user.keys
  return r(status=fail if (lacking_keys or bad_keys) else success, lacking_keys=lacking_keys, bad_keys=bad_keys)

def show_screen(user, path):
  pass # todo
  # accept .bin format, 80x25, 1 byte char followed by 1 byte color. clear screen first, skip over spaces with ansi_move
  # we'll need unicode translations for every high ascii char for putty and other utf-8 clients! where do we find that!? 
  # maybe claude.ai would do a good search. 
  
async def read_cursor_position(user, timeout=2.0): # if this times out, that's going to suck...we *need* the cursor position. todo: we could ask the user if their screen size is 25x80 or what if it times out.
    """Read terminal response for cursor position query"""
    # todo: the user might be pressing keys while this is taking place, so we should scan the input for \x1b etc. 
    # this code almost accounts for that, the only problem is the user might have hit 'R' 
    buffer = b''
    try:
      while True:
        data = await asyncio.wait_for(user.reader.read(1), timeout=timeout)
        if not data:
          break
        buffer += data
        # Check if we have complete ANSI response: ESC[row;colR
        if b'R' in buffer:
          match = line_pos_re.search(buffer)
          if match:
            rows = int(match.group(1))
            cols = int(match.group(2))
            return rows, cols, buffer
          return None, None, buffer
    except asyncio.TimeoutError:
        return None, None, buffer

async def get_screen_size(user):
   # user.writer.write(Detecting screen size...\x1b[s\x1b[999;999H\x1b[6n\x1b[u") 
   user.writer.write("\x1b[s\x1b[999;999H\x1b[6n\x1b[u") 
   #save cursor position, move cursor to 999,999, send command to retrieve cursor position, restore cursor position
   await user.writer.drain()   
   return await read_cursor_position(user)

class Destinations:
  async def login(user, r):
    async def check_handle_password(handle, password):
      cur.execute("SELECT * FROM users WHERE handle = ? LIMIT 1 COLLATE NOCASE", (handle,))
      r = RetVals()
      user_in_db = cur.fetchone()
      if user_in_db is None:
        user.login_tries.append((handle,))
        return RetVals(status = "bad handle")
      else:
        if user_in_db["password_hash"] == bcrypt.hashpw(password, user_in_db["password_salt"]):
          user.id = user_in_db["id"]
          user.handle = user_in_db["handle"] # correct capitalization here
          user.email = user_in_db["email"]
          user.age = user_in_db["age"]
          user.sex = user_in_db["sex"]
          user.location = user_in_db["location"]
          user.time_created = user_in_db["time_created"]
          cur.execute("SELECT key FROM USER_KEYS WHERE user_id = ?", (user.id,))
          rows = cur.fetchall()
          user.keys.add(r["key"] for r in rows)
          user.input_timestamps = deque()
          user.batch_mode = False
          global_data.users_logging_in.remove(user)
          global_data.users[handle.lower()] = user
          conf1 = get_config(os.path.join(config.user_configs, user.handle))
          conf2 = get_config(config.user_defaults)
          conf3 = get_config()
          user.conf = config.ConfigView(conf1, conf2, conf3)
          return RetVals(status=success)
        else:
          r.status = fail
          r.err_msg = "The password you entered is incorrect."
          user.login_tries.append((handle, password))
          return r
    rows, cols = get_screen_size(user)
    user.screen = [[Char() for col in cols] for row in rows]
    user.click_screen = [[None*rows] for row in rows] # this will store arbitrary objects associated with cells to be returned when they're clicked on (set by a rect defining function)
    await send(user, "Welcome to " + config.bbs_name)
    for x in range(config.login.allowed_attempts):
      await send(lf*2+'Enter your handle or "new" to sign up.'+lf*2, drain=True)
      handle = await InputField(user, *read_cursor_position(user), user.screen_width-1) # todo: use nowrap as explained in another comment so i can take out that -1
      if handle.lower() == "new":                                                                                 # todo: i think we have to distinguish between an input_field stand-alone and one
        return RetVals(status=new_user, next_destination=register)                                                           #       used in an input page?
        await send(user, lf*2+handle+" is not a registered user on this system")                                            # todo: do we change cur_destination to the input_field or what?
        continue
      await send(user, lf*2+"Enter your password.")
      password = await InputField(user, *read_cursor_position(user), user.screen_width-1) # todo: use nowrap as explained in another comment so i can take out that -1
      r = check_handle_password(handle, password)
      if r.status==success:
        return r
      else:
        await send(user, lf*2+r.err_msg)
    return RetVals(status=fail, err_msg="max failed attempts", next_destination=logout, next_menu_item=None)

  async def do_destination(user, destination, menu_item=None): 
      # todo: this should return a function to talk to destination too, even if it's set to None, 
      # or we should change RetVals so that getting a nonexisting attribute returns something False=equivalent,
      # and so does getting a nonexisting attribute of a nonexisting attribute, etc.
    if destination.type == "func":
      r = await getattr(Destinations, destination)(user, destination, menu_item)  
    elif destination.type == "menu":                                               
      r = await menu.do_menu(user, destination, menu_item, r) # how will the menu know to render itself instead of going into an option? i guess if destination==menu_item?
    elif destination.type == "module":
      r = await modules[destination].run(user, destination, menu_item)
    r.destination = destination.type # todo: fix
    return r

  async def user_director(user, next_destination, next_menu_item=None): # todo: first we have to login
    result = check_keys(user, next_destination, next_menu_item)
    if not result.allowed:
      status=fail
      err_msg=f"Destination: {next_destination}{('/'+next_menu_item if next_menu_item else ''}\n"
               "Missing keys: {r.lacking_keys}\n"
               "Bad keys: {r.bad_keys}")
        
      if user.destination_history[-1].r != fail:
        next_destination = user.destination_history[-1].destination
        next_menu_item = user.destination_history[-1].menu_item
      else:
        next_destination = user.main.destination # depends on get_config having been called with user as a parameter, so that the first lookup is user.main_destination
        next_menu_item = user.main.menu_item
        for x in user.destination_history[::-1]:
          if next_destination == x.destination and next_menu_item == x.menu_item:
            if x.r.status==fail:
              next_destination = config.main.destination # depends on get_config having been called with user as a parameter, so that the first lookup is user.main_destination
              next_menu_item = config.main.menu_item
              for x in user.destination_history[::-1]:
                if next_destination = x.destination and next_menu_item = x.menu_item:
                  if x.r.status==fail:
                    next_destination = logout
                    next_menu_item = None
                    err_msg += "\n\nCould not find a destination for you. Man, this is really messed up."
                    next_destination = logout
                  break
            break
      return RetVals(status=status, err_msg=err_msg, next_destination=next_destination, next_menu_item=menu_item)
    
    async def logout(user)
      user.writer.close()
      del global_data.users[user.handle.lower()]