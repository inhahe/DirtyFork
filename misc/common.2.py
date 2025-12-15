import asyncio
from keyboardcodes import *
import re
from config import get_config
import sqlite3
from InputFields import *
from register import register
import bcrypt

config = get_config()

con = sqlite3.connect(config.database)
con.row_factory = sqlite3.Row 
cur = con.cursor()

class RetVals:
  def __init__(self, **kwargs):
    for k, v in kwargs.items():
      self.k = v

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
black, red, green, brown, blue, magenta, cyan, gray = range(8) 
yellow = brown
white = gray
colors = {"black": black, "red": red, "green": green, "brown": brown, "blue": blue, "magenta": magenta, "cyan": cyan, "gray": gray, "white": white, "yellow": yellow}

SyncTERM, PuTTy = 1, 2

success, fail, new_user = 1, 2, 3

cr, lf = "\x0d", "\x0a"

def check_keys(user, item):
  r = RetVals()
  lacking_keys = (item.white_keys or set()) - user.keys
  bad_keys = (item.black_keys or set())  & user.keys
  return r(allowed=bool(lacking_keys or bad_keys), lacking_keys=lacking_keys, bad_keys=bad_keys)

def ansi_wrap(user, wrap=True): 
  if user.cur_wrap != wrap:
    if wrap:
      user.writer.write("\x1b[?7h") 
    else:
      user.writer.write("\x1b[?7l") 
    user.cur_wrap = wrap

# todo: have an ansi_leftright and an ansi_updown which can take negative numbers and call the appropriate function, just for convenience?

async def ansi_left(user, val=1, drain=False): 
  assert val >= 0
  new_col = max(user.new_col-val, 1)
  if drain:
    await ansi_move_2(user, drain)
  
async def ansi_right(user, val=1, drain=False):
  assert val >= 0
  user.new_col = min(user.new_col+val, user.screen_width)
  if drain:
    await ansi_move_2(user, drain)
  
async def ansi_up(user, val=1, drain=False): 
  assert val >= 0
  user.new_row = max(user.new_row-val, 1)
  if drain:
    ansi_move_2(user, drain)

async def ansi_down(user, val=1, drain=False): 
  assert val >= 0
  user.new_row = min(user.new_row+val, user.screen_height)
  if drain:
    await ansi_move_2(user, drain)

async def ansi_move(user, row=None, col=None, drain=False): # we have the drain option because if we're moving the cursor in(to) an input field, the user will want to see where he's about to type.
  user.new_row = row if row else user.new_row
  user.new_col = col if col else user.new_col
  assert user.new_row > 0 and user.new_col > 0                      # should we raise an error if row or col exceeds the boundaries of the screen?
  if drain:
    await ansi_move_2(user, drain)

async def ansi_move_2(user, drain=False):
  if user.cur_row != user.new_row and user.cur_col != user.new_col: 
    user.cur_row = min(user.new_row, user.screen_height)     # should we raise an error if val is too far up, down, left or right instead of just max/mining it? to catch potential bugs?
    user.cur_col = min(user.new_col, user.screen_width) 
    user.writer.write(f"\x1b[{user.cur_row};{user.cur_col}H")
  elif user.cur_row != user.new_row and user.cur_col == user.new_col: 
    if user.new_col > user.cur_col: # go right
      val = user.new_col-user.cur_col
      if val==1 or user.cur_col==user.screen_width-1:                                 
        user.writer.write("\x1b[C")         
      else:                                                 
        user.writer.write(f"\x1b[{val}C")
    else: # go left
      val = user.cur_col - user.new_col
      if val == 1:
        user.writer.write(cr)
      elif val<=3 or user.cur_col<=4:
        user.writer.write(back*min(val, user.user_col-1)) # if we're moving 3 or fewer to the left, send \x08's instead
      else:
        user.writer.write(f"\x1b[{val}D")
  elif user.cur_row == user.new_row and user.cur_col != user.new_col:
    if user.new_row > user.cur_row: # go up
      val = user.cur_row - user.new_row
      if val==1 or user.cur_row==2:
        user.writer.write("\x1b[A")
      else:
        user.writer.write(f"\x1b[{val}A")
    else:
      val = user.new_row - user.cur_row # go down
      if val<=3:
        user.writer.write(lf*min(val, user.cur_row - user.screen_height)) # check: will this shortcut mess with our handling of ansi scroll regions?
      else:
        user.writer.write(f"\x1b[{val}B")
  else: # user.cur_row == new_row and user.cur_col == user.new_col, so values haven't changed, don't drain
    return
  user.cur_row = user.new_row
  user.cur_col = user.new_col  
  if drain:
    await user.writer.drain()

def ansi_color(user, fg=None, bg=None, fg_br=None, bg_br=None, drain=False): # note that any color property not passed here will remain as it currently is rather than resetting to default.
  if fg is None and bg is None and fg_br is None and bg_br is None:
    user.new_fg = white
    user.new_bg = black
    user.new_fg_br = False
    user.new_bg_br = False
  else:
    user.new_fg = user.cur_fg if fg is None else fg
    user.new_bg = user.cur_bg if fg is None else bg
    user.new_fg_br = user.cur_fg_br if fg_br is None else fg_br
    user.new_bg_br = user.cur_bg_br if bg_br is None else bg_br
  if drain:
    ansi_color_2(user, drain=True)
  
async def ansi_color_2(user, drain=False):
  # note: syncterm blinks instead of bright background
  codes = []                                                                            
  if (user.new_fg == white and user.new_bg == black and user.new_fg_br == False and user.new_bg_br == False) and (user.cur_fg != white or user.cur_bg != black or user.cur_fg_br != False or user.cur_bg_br != False):
    user.writer.write("\x1b[m") 
  else:
    if user.new_fg_br != user.cur_fg_br:
      if user.new_fg:
        codes.append("1")
      else:
        codes.append("22")
      user.cur_fg_br = user.new_fg_br
    if user.new_bg_br != user.cur_bg_br:
      if user.new_bg_br:
        codes.append("5")
        user.cur_bg_br = True
      else:
        codes.append("25")
      user.cur_bg_br = user.new_bg_br
    if user.new_fg != user.cur_fg:  
      codes.append(str(user.new_fg+30))
      user.cur_fg = user.new_fg
    if user.new_bg != user.cur_bg:
      codes.append(str(user.new_bg+40))
      user.cur_bg = user.new_bg
    if codes: 
      user.writer.write(f"\x1b[{+';'.join(codes)}m") 
  if drain:
    await user.writer.drain()

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

async def ansi_cls(user, fg=None, bg=None, fg_br=None, bg_br=None):
  ansi_color(user, fg, bg, fg_br, bg_br)
  user.writer.write("\x0c")
  emu_clear(user)
  
def emu_scroll(user): # todo: add scroll region paramaters?
  del user.screen[0]
  user.screen.append([Char() for _ in range(user.screen_width)])

def emu_clear(user):
  for x in range(len(user.screen)):
    user.screen[x] = [[Char() for col in range(user.screen_width)] for row in range(user.screen_height)]
  user.cur_col = user.cur_row = 1

async def send(user, message, word_wrap=False, drain=False): # doesn't emulate ansi for the time being, since ansi should be handled via the convenience functions.
  if message:
    ansi_move_2(user)
    ansi_color_2(user)
  user.writer.write(message)                           # todo: support word_wrap.  should we word wrap when the first word of the last send adds to the last word of the previous send? 
                                                             # that would be complicated, and probably not necessary.
  if drain:                                                  # for word wrap, be sure to include extra spaces when there is more than one space between words.
    await user.writer.drain()                                # for word wrap, might be easiest to insert crlf's into the message and then call a send2 function on each character.
  for char in message:                                       # todo: if char=="\x07" (beep), some terminals may not print the char.. SyncTERM does for some reason. if they differ, best to send esc[6u and esc[6s
    if char=="\x00":                                     # even that won't help us if the char is at max_height, max_width, though, because then the screen may or may not scroll.
      pass                                                        # in that case we could just force it to scroll (if nowrap is off) so we know what it's doing.
    elif char=="\x08": 
      user.cur_col = max(user.cur_col-1, 1)     # update: apparently syncterm prints almost all of the ctrl characters, while putty prints none of them.
    elif char=="\x09": 
      user.cur_col = (user.cur_col//8)*8+8  # update: now syncterm doesn't print the beep character.
    elif char=="\x0a":
      if user.cur_col < user.screen_height:
        user.cur_col+=1
      else:
        emu_scroll(user)
    elif char=="\x0c":
      emu_clear(user)
      user.cur_col = user.cur_row = 1
    elif char=="\x0d": 
      user.cur_col = 1
    else:
      if user.terminal == PuTTy and ord(char)<32:
        return
      user.screen[user.cur_row][user.cur_col] = Char(char, fg=user.cur_fg, bg=user.cur_bg, fg_br=user.cur_fg_br, bg_br=user.cur_bg_br)
      if not user.cur_wrap:
        user.cur_col = min(user.cur_col+1, user.screen_width)
      else:
        if user.cur_col==user.screen_width:
          if user.cur_wrap:
            if user.cur_row==user.screen_height:
              user.writer.write(cr+lf) # see quirks.txt to see why we do this
              emu_scroll(user)
            else:
              user.cur_row += 1
            user.cur_col = 1
        else:
          user.cur_col += 1  

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
          global_data.users_logging_in.remove(user)
          global_data.users[handle.lower()] = user
          return RetVals(status=success)
        else:
          await send(user, lf*2+"The password you entered is incorrect.")
          r.status = "bad password" 
          user.login_tries.append((handle, password))
          try: 
            user_conf = config.get_config(os.path.join("user_configs", user.handle+".yaml")) # todo: put user_configs in DirtyFork.yaml?
            for k, v in user_conf.items():
              setattr(user, k, v)
          except:
            # await send(user, lf*2+There was an error reading your configuration file.", r) 
            # todo: only send this if we make every user automatically have a yaml file.
            # todo: have to send it in a different way, the user wouldn't actually see this since they'll immediatly go to a different destination.
            pass
          return r
    rows, cols = get_screen_size(user)
    user.screen = [[Char() for col in cols] for row in rows]
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
    return RetVals(status=fail, err_msg="max failed attempts")

  async def user_director(user, r): # todo: check keys, check if user already went here and it errored
    result = check_keys(user, r.next_destination, r.next_menu_item)
    if not result.allowed:
      status = fail
      err_msg = "Missing keys: " + str(r.lacking_keys) + "Bad keys: " + str(r.bad_keys)
      next_destination = user.destination_history[-1]
    r = RetVals(next_destination=user.destination_history[-1] if user.destination_history else Destinations.user_director(status=status, err_msg=err_msg))


    return RetVals(next_destination=user.main_destination or config.main_destination)    

async def get_input_key(user):
  while True:
    if user.cur_input_code:
      try:
        char = await asyncio.wait_for(user.reader.read(1), timeout=0.02)
      except asyncio.TimeoutError:
        code = user.cur_input_code
        user.cur_input_code = ""
        if code == "\x1b":
          return "esc"
        continue  # incomplete NUL sequence, try again
    else:
      char = await user.reader.read(1)
    if not char:
      raise Disconnected()
    if char in "\x00\x1b":
      user.cur_input_code = char
      continue
    elif user.cur_input_code:
      if ord(char) < 32:
        user.cur_input_code = ""
        return char
      combined = user.cur_input_code + char
      if combined in keyboard_codes:
        user.cur_input_code = ""
        return keyboard_codes[combined]
      if combined in keyboard_code_starts:
        user.cur_input_code = combined
        continue
      else:
        user.cur_input_code = ""
        continue  # unrecognized sequence
    else:
      return char
