# todo: make sure all my async functions are called using await
# todo: make sure i always have result = await function() and not await result = function()
# todo: figure out were i might need to gather or whatever special functions to group awaits or whatever.
# where should we check if the user has the 'banned' key and then log them off if they do?
# i would say in user_director, but the sysop might not necessarily make that the starting destination (settable as config.main_destination)
# or being banned could just bar them from most things on the bbs but not all, they can still navigate the menus for whatever godforsaken 
# reason they might want to. that wouldn't require any step to detect that they're banned, but it would require putting banned in the 
# black_keys for everything they can't use (or include white keys that are taken away from them) (default_options settings for menus make 
# either one a lot easier)
# todo: should i have one instantiation of each class destination for everyone
#       or should i have one instatiotion of each class destination for each user
#       or should i instantiate a class definition as soon as the user enters it???
# would there be more or fewer pros and cons to each for different classes? ugh!
# i guess i'll have to support all three. ugh.
# type: class_bbs
# type: class_user
# type: class_destination
# it's probably not necessary, different instantiations of classes can see each other easily enough, there's global_data
# ok, i'll just have one type. the last type.
# todo: we can't let the an InputField instantiation be deleted just because the user changes destinations away from it. it could still be on the same page she's on. it could have multiple input fields. 
# but how are we going to structure this? and can i manage to get input fields into its own destination with type class or maybe module?
# todo: make signing on a destination
# there are two ways i can do destinations. 
# if they're functions, that's easier, 
# but then i can't ensure that no other function is listening to their input stream by accident, because the function must call the get_input_key function from the bbs, which anything could do
# but when it's a function, i can just call it, and then when it returns it tells me where to send the user to next.
# if it's a class, i have to somehow explicitly make an instatiation of the class, and then call its get_input_key function repeatedly until it tells me it's done.
# for real, i doubt that the bbs would get into a state where two coroutines are accidentally listening for the same user. but who knows.
# wait, doesn't classes just reverse the problem? now how am I going to make sure two different coroutines aren'ttrying to send me input?
# actually, maybe that's doable. the bbs won't send me input from anything else until the current for x in get_input_key(user) yields a stop.
# todo: i think we're a little haphazard about when we go to user_director. it should be always. so it shouldn't even have to be listed as a first destination, maybe? 
# maybe the only firsts have to be (a) login and (b) main_destination?
# though main_destination can be overriden in a user's yaml.
# todo: have system, etc. messages from outside the Destination appear in a box with an x on the top right for the user to close when they're done?
#       maybe the box must span all the way across the screen to make it much easier to scroll the regular content while the box is there?
# alternate name idea: Galactic, because of the animated stars i'll have. Claude researched and said it doesn't already exist.
# okay, here's the model i've decided on. 
# there's two regions of the screen, the destination region and the bbs region for bbs-wide messages
# the destination region may have its own two regions, input and and the destination output
# but those two probably won't have to be simultaneous, so it doesn't need to remember a current cursor position for each one
# but should i have the bbs region constantly there, or open and close when there's a message? the latter would require emulating the entire screen exactly. is that even doable?

# "One gotcha: terminal behavior at the right margin is actually a little inconsistent. Some terminals wrap immediately when you write to the last column. Others do 
# "deferred wrap" —# the cursor stays in the last column and only wraps when the next character arrives. This matters if you're trying to write exactly 80 characters and then do a 
# cursor move without wanting a blank line inserted."
# "Most BBSes just avoided the problem by treating column 79 as the effective edge for text, or by explicitly sending CRLF and managing it themselves rather than relying on autowrap."
# most BBSers use SyncTERM nowadays.
# problem: some terminals use utf-8, which conflicts with high ascii.
# todo: mouse tracking: esc[?1000h
# "So basic mouse tracking is actually pretty well supported across the terminals people are likely to use. The main variations are:
#Whether they support the extended SGR mode (1006) for coordinates > 223
#Whether they support motion tracking (1002, 1003)
#How they handle modifier keys with clicks"
# todo: i think the logic for getting input from the user might be incorrect. how do we get input from every user?
# todo: find writer.write and write.write to change them to send so we can emalute the screen properly.
# todo: provide a ctrl key the user can press to redraw the screen in case of line noise, and a key they can press in case of changed screen height/width. actually, just make the same key do both. 
# todo: populate `users` with the user info of every user, and make `global_data.online_users` have the online ones?
# don't forget to add a user to `users` if they've just registered.
# todo: make a password type input field that replaces characters with *'s
# todo: confirmation emails on registration?

from email import contentmanager
from hmac import new
from lzma import FILTER_LZMA1
from pyexpat.errors import codes
from string import whitespace
import asyncio, re, sqlite3, sys, collections, os, subprocess, multiprocessing
from importlib import import_module
from xml.etree.ElementTree import QName
import telnetlib3, serial, yaml, bcrypt
from keyboardcodes import *
from config import get_config
from RetVals import *

# we should consider ruamel.yaml instead, it supports newer yaml spec and preserves formatting, but has 
# less of a userbase and a more complex api. we might want both the bbs and the sysop to be able to modify yaml files.

# todo: make the bbs a lot more robust by adding a lot more try: excepts

default_config = "DirtyFork.yaml"

config = get_config(sys.argv[1] if len(sys.argv)>1 else default_config)  

# i really want a better place to list the modules, because they need to be loaded when the bbs starts up. but i don't see a better way without being redundant.
modules = {} # todo: would be better if we could do all this with one list comprehension somehow
for module in [destination for destination in config.destinations if destination.type == "module"]:
  modules[module] = import_module(module)

line_pos_re = re.compile(b'\x1b\\[(\\d+);(\\d+)R')
email_re = re.compile(b'''(?:[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+(?:\.[a-z0-9!#$%&'*+\x2f=?^_`\x7b-\x7d~\x2d]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9\x2d]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9\x2d]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])''')
# what the hell is this? todo: does it work?
handle_re = re.compiel("[A-Za-z0-9_]") # i won't allow spaces because that could mess up door games that require a handle in the command line. should I allow any special characters?
                                       # todo: on second thought, handles with spaces is more fun. What should I do abotu the door games?

black, red, green, brown, blue, magenta, cyan, gray = range(8) 
yellow = brown
white = gray
colors = {"black": black, "red": red, "green": green, "brown": brown, "blue": blue, "magenta": magenta, "cyan": cyan, "gray": gray, "white": white, "yellow": yellow}

success, fail, new_user = 1, 2, 3

cr, lf = "\x0d", "\x0a"

def check_keys(user, item):
  r = RetVals()
  lacking_keys = (item.white_keys or set()) - user.keys
  bad_keys = (item.black_keys or set())  & user.keys
  return r(allowed=bool(lacking_keys or bad_keys), lacking_keys=lacking_keys, bad_keys=bad_keys)
 
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

      rows, cols = detect_screen_size(user)
      user.screen = [[Char() for col in cols] for row in rows]
      await send(user, Welcome to " + config.bbs_name.encode("utf-8"))
      for x in range(config.login.allowed_attempts):
        await send(lf*2+'Enter your handle or "new" to sign up.'+lf*2, drain=True)
        handle = await input_field(user, *read_cursor_position(user), user.screen_width-1) # todo: use nowrap as explained in another comment so i can take out that -1
        if handle.lower() == new_user:                                                                                 # todo: i think we have to distinguish between an input_field stand-alone and one
          return RetVals(status=new_user, next_destination=register)                                                           #       used in an input page?
          await send(user, lf*2+handle+ is not a registered user on this system")                                            # todo: do we change cur_destination to the input_field or what?
          continue
        await send(user, lf*2+Enter your password.")
        password = await input_field(user, *read_cursor_position(user), user.screen_width-1) # todo: use nowrap as explained in another comment so i can take out that -1
        r = check_handle_password(handle, password)
        if r.status==success:
          return r
      return RetVals(status=fail, err_msg="max failed attempts")

  async def user_director(user, r):
      
  
    return RetVals(next_destination=user.main_destination or config.main_destination)    

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
   
class Char: 
  def __init__(self, fg=7, bg=0, fg_br=False, bg_br=False, char=" "):
    self.fg = fg
    self.bg = bg
    self.fg_br = fg_br
    self.bg_br = bg_br
    self.char = char

async def read_input_batch(user, pause_threshold=0.03): # todo: put pause_threshold into configuration instead of hardcoding it?
                                                        # todo: with a more sophistaced approach involving 'if X characters arrive within Y time' using time.perf_counter, we could 
                                                        # avoid any unnecessary delay after the user presses a key.. 
  """Read all available input, waiting up to pause_threshold for more."""
  batch = []
    
  # Wait for at least one keypress (blocking)
  key = await os.get_input_key(user)
  batch.append(key)
    
  # Keep reading while more arrives quickly
  while True:
    try:
      key = await asyncio.wait_for(read_keypress(user), timeout=pause_threshold)
      batch.append(key)
    except asyncio.TimeoutError:
      break
  return batch

class InputBox:
  while True:
    user = self.user
    if self.height == 1: # do i really want a separate function for this special case? i just didn't want to waste the code I already had...
      if key == "left":
        if user.cur_input_col == 1:
          if user.cur_input_pos > 1:
            user.cur_input_pos -= 1
            await send(user, user.cur_input[user.cur_input_pos:user.cur_input_pos+length], in_input=True)
            await ansi_left(user.screen_width)
        else:
          ansi_left(user, 1)
          user.cur_input_pos -= 1
          user.cur_input_col -= 1
      elif key == "right":
        if user.cur_input_col == user.screen_width:
          if user.cur_input_pos < len(user.cur_input):
            user.cur_input_pos += 1
            await ansi_left(user.screen_width)
            await send(user, user.cur_input[user.cur_input_pos:user.cur_input_pos+length], in_input=True)
        else:
          ansi_right(user, 1)
          user.cur_input_pos += 1
          user.cur_input_col += 1
      elif key == "home":
        pass # todo
      elif key == "end":
        pass # todo
      elif key == "ins":  
        pass # todo
      elif key == "del":
        user.cur_input = user.cur_input[:user.cur_input_pos] + user.cur_input[user.cur_input_pos+1:]
        s = user.cur_input[user.cur_input_pos:user.cur_input_pos+length-user.cur_input_col]+" "
        await send(user, s, in_input=True)
        await ansi_left(user, len(s), in_input=True)
      elif key == ctrl_u or key == ctrl_c or key == cr: # we don't have to distinguish here, input_field looks for cr to know when editing is complete. 
        await ansi_left(user, 999)                         # ctrl_u = clear line
        user.cur_input = ""
        user.cur_input_col = 0
      elif ord(key) >= 32:
        if user.cur_input_pos <= len(user.cur_input):
          await send(user, key+user.cur_input[user.cur_input_pos:user.cur_input_pos+length-user.cur_input_col], in_input=True)
          user.cur_input = user.cur_input[:user.cur_input_pos]+key+user.cur_input[user.cur_input_pos:]
        user.cur_input_pos += 1
        user.cur_input_col += 1
        await user.writer.drain()
    else:
      if char == cr: # carriage return aka enter aka return # don't let the cursor go down if it would push text beyond the bottom of the input field and config.input_fields.scroll_inside is disabled.
      scroll_inside = scroll_inside if self.scroll_inside is None else self.scroll_inside # might we provide a way to cascade these hierarchical settings automatically? though there aren't very many of them..
      if len(self.content) < self.max_length:
        index = self.content_index_array[self.cur_row][self.cur_col]
        self.content = self.content[:index]+cr+self.content[index:]

  async def __init__(self, user, conf, r): # r is probably unnecessary. do we need destination? after all, we do have user_cur_destination. i think.
    self.user = user
    self.conf = conf
    self.r = r
    self.contents = ""
    self.cur_col == 1 # these are relative to the position of the input_field.
    self.cur_row = 1
    self.scrolled_down = 0
    self.scrolled_right = 0
    await ansi_move(conf.row, conf.col)
    if conf.box:
      self.col = conf.col+1
      self.row = conf.row+1
      self.width = conf.width-2
      self.height = conf.height-2
      await ansi_color(fg=conf.box.color.fg, fg_br=conf.box.color.fg_br, bg=conf.box.color.bg, bg_br=conf.box.color.bg_br)
      if conf.box.double:
        ords = chr(201), chr(205), chr(187), chr(186), chr(200), chr(188)
      else:
        ords = chr(218), chr(196), chr(191), chr(179), chr(192), chr(217)
      await send(user, ords[0] + ords[1]*self.width+ords[2]) # todo: don't forget when we need nowrap
      await ansi_move(self.row, conf.col)
      await send(user, ord[3])
      for l in range(self.height):
        await ansi_move(self.row+l, conf.col)
        if conf.bg_chars:
          await ansi_color(fg=conf.bg_chars.fg, fg_br=conf.bg_chars.fg_br, bg=conf.bg_chars.bg, bg_br=conf.bg_chars.bg_br)
          await send(user, bytes((conf.bg_chars.ord,) or (32,))*self.width)
          await ansi_color(fg=conf.box.color.fg, fg_br=conf.box.color.fg_br, bg=conf.box.color.bg, bg_br=conf.box.color.bg_br)
        else:
          await send(user, ords[0])
          await ansi_right(self.conf.width-1)
          await send(user, ords[0])
      await ansi_move(conf.row+conf.height-1, conf.col)
      await send(user, ords[4] + ords[1]*self.width+ords[5]) # todo: don't forget when we need nowrap
    else:
      self.col = conf.col
      self.row = conf.row
      self.width = conf.width
      self.height = conf.height
      if conf.bg_chars:
        await ansi_color(fg=conf.bg_chars.fg, fg_br=conf.bg_chars.fg_br, bg=conf.bg_chars.bg, bg_br=conf.bg_chars.bg_br)
        for l in range(conf.height):
          await ansi_move(self.conf.row+l, conf.col)
          await send(user, bytes((conf.bg_chars.ord,) or (32,))*self.width)
          await ansi_move(user, conf.row, conf.col)
          await user.writer.drain()
    self.pos_to_content_index = [[None*conf.width] for _ in range(conf.height)]
    self.content_index_to_pos = [] # probably won't need this either.
    self.content_lines = ["" for _ in range(conf.height)] # todo: might not need this one.
    # we could keep an array of all word positions plus how many spaces and how many cr's are after each word 
    # to make it easier to compute word wrap, but then we have to modify it without iterating over the whole thing 
    # every time we insert or delete a char. so it may not be worth it. hmm, let's do it.
    # should we store lines of words, or just a 1D array of words? or a 1D array of words, cr's, spaces, rows and cols?
    # hmm, you can have any combination of spaces and cr's after a word... so cr's should probably also be words. 
    # or extra spaces should. 
    self.words = []
    self.dists_from_right = [None*conf.height]
  async def recompute_word_wrap(self): # uh oh, what happens when the user pastes something into the middle of the text?
                                       # it would have to recompute word wrap for every character!
                                       # we need some kind of input buffer for this
                                       # i'll buffer it for as long as there's been more than 20 characters inputed 
                                       # per second, that should be fine because it's faster than anybody can type.
                                       # i should do it in terms of input codes, not characters.
    starting_content_index = self.pos_to_content_index[self.cur_row][self.cur_col]
    # todo: finish
  
    keyboard_code_starts = set() 
    for code in keyboardcodes:
      s = ""
      for s2 in code:
        s+=s2
        keyboard_code_starts.add(s)
  
class Subdestinations:
  def input_field(user, field_length, content_length, fg=config.input_fields.fg, bg=config.input_fields.bg, fg_br=config.input_fields.fg_br, bg_br=contfig.input_fields.bg_br,
                 fill=config.input_fields.fill, fill_fg=config.input_fields.fill_fg, fill_bg=config.input_fields.fill_bg, fill_fg_br=config.input_fields.fill_fg_br, 
                 fill_bg_br=config.input_fields.fill_bg_br, outline=None, content=""): 
    # todo: have a special case if field_length == content_length where we never worry about content_pos?
    # makes the input field starting where the cursor currently is at.
    # col = beginning col of input field
    # field_pos = position within the input field, starting at 0
    # content_pos = the current index of the content at field_pos 0
    # content = current user input
    # fill = character ascii number to fill empty space with
    # todo: support outline around input
    # todo: process buffers by doing all the calculations without writing anything yet
    # should we break up even calculating buffers so we don't disrupt the other users? how large a chunk size should we use? claude says no. 
    # content_pos+field_position==len(content) and insert_mode==True is a special case. field_pos+col_offset will actually be 1 greater than user.cur_col. this is so the cursor stays inside the edit field. 
    # field_length should never be > content_length
    # todo: constantly blink block cursor with a timer, alternating between block cursor and character at that point? claude says that's non-standard and may be confusing, but it seems familar. 
    # but also, would that cause periods of stillness followed by very rapid blinking due to network delays?
        
    field_pos = content_pos = 0
    content = ""
    insert_mode = True
    if col+field_length-1>user.screen_width:                                                    
      raise ValueError("Input field would extend beyond screen width.")
    if col_offset+field_length-1==user.screen_width:
      await ansi_wrap(user, False)
    col_offset = user.cur_col    
    while True:
      if key == "left":
        if field_pos == 0:
          if content_pos > 0: # field is scrolled to the right, cursor is at the beginning
            content_pos -= 1
            if insert_mode:
              await send(user, content[content_pos:content_pos+field_length])
            else:
              await ansi_color(user, bg, fg)
              await send(user, content[content_pos]) # write inverted color char at cursor pos
              await ansi_color(user, fg, bg)
              await send(user, content[content_pos+1:content_pos+field_length]) # write rest of content in normal colors
            await ansi_move(user, col=col_offset) 
        else:                                               
          field_pos += 1
          if insert_mode:
            await ansi_left(user)
          else:
            await send(user, content[content_pos+field_pos+1])
            await ansi_color(user, bg, fg)
            await send(user, content[content_pos+field_pos])
            await ansi_color(user, fg, bg, fg_br, bg_br)
            await ansi_left(user)
            await ansi_left(user)                                
      elif key == "right":
        if field_pos == field_length-1: # cursor is at the very right
          if field_pos+content_pos <= len(content): # make sure cursor is not at end of content already # off by one maybe?
            content_pos += 1
            await ansi_move(col=col_offset) # move the cursor the easy/cheating way, we totally optimized ansi_move() anyway. 
            if insert_mode:
              await send(user, content[content_pos:content_pos+field_length])
            else:
              await ansi_move(col=col_offset)
              await send(user, content[content_pos:content_pos+field_length-1] # send normal characters up until the inverted character
              await ansi_color(user, bg, fg)
              await send(user, content[content_pos+field_length])              # send the inverted character
              await ansi_color(user, fg, bg, fg_br, bg_br)
            await ansi_left(user)
        else:
          field_pos += 1
          if insert_mode:
            await ansi_right(user)
          else:
            await send(user, content[content_pos+field_pos-1])                 # send normal character to replace the inverted character
            await ansi_color(user, bg, fg)
            await send(user, content[content_pos+field_pos])                   # send inverted character to replace the normal character one to the right
            await ansi_color(user, fg, bg, fg_br, bg_br)
            await ansi_left(user)
      elif key == "home":
        if content_pos > 0:
          field_pos = content_pos = 0
          await ansi_move(col=col_offset)          
          if insert_mode:
            await send(user, content[:field_length])    # send <field_length> many characters of content 
            ansi_move(col=col_offset)
          else:
            await ansi_color(bg, fg)
            await send(user, content[0])    
            await ansi_color(fg, bg, fg_br, bg_br)
            await send(user, content[1:field_length])
        else:
          await ansi_color(bg, fg)
          await send(user, content[0])
          await ansi_right(user, field_pos)
          await ansi_color(fg, bg, fg_br, bg_br)
          await send(user, content[field_pos])
          await ansi_move(col=col_offset)
        await ansi_move(user, col=col_offset) 
      elif key == "end":
        if len(content) <= field_length:
          await ansi_right(user, len(content)-field_pos)
          field_pos = len(content)
        else:
          await ansi_move(user, col=col_offset)
          content_pos = field_length-len(content) 
          await send(user, content[content_pos:content_pos+field_length]) 
          await ansi_color(user, fill_bg, fill_fg, fill_bg_br, fill_fg_br)
          await send(user, fill)
          await ansi_color(user, bg, fg, bg_br, fg_br)
      elif key == "ins":  # todo
        insert_mode = not insert_mode
        if insert_mode:
          await send(user, content[content_pos+field_pos]) # insert was turned on, replace block with the content character at that col.
          await ansi_left()
        else:
          await ansi_color(user, bg, fg)
          await send(user, content[content_pos+field_pos]
          await send_color(user, fg, br, fg_br, bg_br)
          await ansi_left(user, bg, fg)
      elif key == "back":
        if field_pos==0:
          if content_pos>0:
            content_pos -= 1
            content=content[:content_pos]+content[content_pos+1:] # delete a char from content. we're at field_pos=0 so we don't have to factor in field_pos.
        else:
          content_pos -= 1          
          content=content[:content_pos+field_pos]+content[content_pos+field_pos+1:] # delete a char from content at new content_pos. factor in field_pos.
          await ansi_move(user, left)
          if insert_mode:
            await send(user, chr(217)+content[conten_pos+1:content_pos+field_length-field_pos]) # check: is this accurate?
          else:
            await send(user, content[content[conten_pos:content_pos+field_length-field_pos]) # check: is this accurate?
          if field_length>len(content)-content_pos:
            await ansi_color(user, fill_fg, fill_bg, fill_fg_br, fill_bg_br)
            await send(user, fill)
            await ansi_color(user, fg, bg, fg_br, br_br)
      elif key == "del":
        end_pos == len(content) - content_pos-1 
        if end_pos==field_pos: # if cursor is right at the end of the content
          content = content[:field_pos+content_pos-1]
          if insert_mode:
            await ansi_color(user, fill_fg, fill_bg, fill_fg_br, fill_bg_br)
            await send(user, fill)
          else:
            await ansi_color(user, fill_bg, fill_fg)
            await send(user, fill)
            await ansi_color(user, fg, bg, fg_br, bg_br)
        else:
          content = content[:content_pos]+content[field_pos+content_pos+1:]
          if end_pos < field_length + 1: # check: off by one error?
            if insert_mode:
              await send(user, content[field_pos+content_pos:field_pos+content_pos+field_length-field_pos]) # check: is this correct? and is there an off by one error?
                        
            

            

          


        content = content[:content_pos+field_pos] + content[content_pos+field_pos+1:] # delete a char from content at content_pos.
        
        if content_pos+field_pos == field_length-1:                      # cursor is at the last 



        if insert_mode:
          await send(user, chr(217)+content[content_pos+field_pos+1:]) # we already deleted the char, this +1 is for a different purpose.
        else:
          await send(user, content[content_pos+field_pos:]) 
      
      if field_length>len(content)-content_pos:
        await ansi_color(user, fill_fg, fill_bg, fill_fg_br, fill_bg_br)
        await send(user, fill)
        await ansi_color(user, fg, bg, fg_br, br_br)
      elif key == ctrl_u: # ^U = clear line
        content = ""
        field_pos = content_pos = 0
        await ansi_move(col=col_offset)
        await ansi_color(user, fill_fg, fill_bg, fill_fg_br, fill_bg_br)
        await send(user, fill*field_length)
        await ansi_color(user, fg, bg, fg_br, br_br)
      elif key == cr: 
        await send(user, cr+lf)
        return content
      elif ord(key) >= 32:
        if insert_mode:
          if len(content) < content_length: 
            content = content[:field_pos+content_pos]+key+content[field_pos+content_pos:]
            await send(user, content[content_pos+field_pos:content_pos+field_pos+field_length-field_pos])
            await ansi_move(user, col=col_offset+input_pos)
          field_pos += 1
        else:
          content[field_pos+content_pos] = key
          if field_pos < field_length-1:
            
      await user.writer.drain()
    
async def bbs_msg(user, message): # remember value of ansi_wrap and reset it afterward
  # do we pause everything else while this is showing, or let it scroll behind it simultaneously?
  pass

def emu_scroll(user): # todo: add scroll region paramaters?
  del user.screen[0]
  user.screen.append([Char() for _ in range(user.screen_width)])

def emu_clear(user):
  for x in range(len(user.screen)):
    screen[x] = [[Char() for _ in range(user.screen_width)]

async def send(user, message, word_wrap=False, drain=False): # doesn't emulate ansi for the time being, since ansi should be handled via the convenience functions.
  await user.writer.write(message)                           # todo: support word_wrap.  should we word wrap when the first word of the last send adds to the last word of the previous send? 
                                                             # that would be complicated, and probably not necessary.
  if drain:                                                  # for word wrap, be sure to include extra spaces when there is more than one space between words.
    await user.writer.drain()                                # for word wrap, might be easiest to insert crlf's into the message and then call a send2 function on each character.
  for char in message:                                       # todo: if char=="\x07" (beep), some terminals may not print the char.. SyncTERM does for some reason. if they differ, best to send esc[6u and esc[6s
    if char=="\x00": pass                                    # even that won't help us if the char is at max_height, max_width, though, because then the screen may or may not scroll.
                                                             # in that case we could just force it to scroll (if nowrap is off) so we know what it's doing.
elif char=="\x08": user.cur_col = max(user.cur_col-1, 1)     # update: apparently syncterm prints almost all of the ctrl characters, while putty prints none of them.
    elif char=="\x09": user.cur_col = (user.cur_col//8)*8+8
    elif char=="\x0a":
      if user.cur_col < user.screen_height:
        user.cur_col+=1
      else:
        emu_scroll(user)
    elif char=="\x0c":
      emu_clear(user)
      user.cur_col = user.cur_row = 1
    elif char=="\x0d": user.cur_col = 1
    else:
      screen[user.cur_row][user.cur_col] = Char(char, fg=user.cur_fg, bg=user.cur_bg, fg_br=user.cur_fg_br, bg_br=user.cur_bg_br)
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
          
async def bbs_msg(user): # todo
  if not user_cur_bbs_box:
    # make box
    pass
  # move to user.cur_bbs_row, user.cur_bbs_col
  # write message with word wrap
  # remember cur_bbs_msg contents and show them before appending?
  # have option to use ansi region scrolling instead of a manual box
  # include close button for the box that uses esc[1000h, but also allow pressing esc to close
  
async def ansi_wrap(user, wrap=True): 
  if user.cur_wrap != wrap:
    if wrap:
      await user.writer.write("\x1b[?7h") 
    else:
      await user.writer.write("\x1b[?7l") 
    user.cur_wrap = wrap

# todo: have an ansi_leftright and an ansi_updown which can take negative numbers and call the appropriate function, just for convenience?

async def ansi_left(user, val=1, drain=False): 
  assert not val < 0:
  if val > 0:
    new_col = max(user.cur_col-val, 1)
    if new_col == 1:
      user.writer.write(cr)
    else:
      if val<=3 or user.cur_col<=4:
        await user.writer.write(back*min(val, user.user_col-1)) 
      else:
        await user.writer.write(f"\x1b[{val}D")
      user.cur_col = new_col
    if drain:
      await user.writer.drain()

async def ansi_right(user, val=1, drain=False):
  assert not val < 0:
  if val > 0:
    if val==1 or user.cur_col==user.screen_width-1:                                 
      await user.writer.write("\x1b[C")         
    else:                                                 
      await user.writer.write(f"\x1b[{val}C")
    user.cur_col = min(user.cur_col+val, user.screen_width)           # should we raise an error if val is too far up, down, left or right instead of just max/mining it? to catch potential bugs?
    if drain:
      await user.writer.drain()
  
async def ansi_up(user, val=1, drain=False): 
  assert not val < 0:
  if val > 0:
    if val==1 or user.cur_col==2:
      await user.writer.write("\x1b[A")
    else:
      await user.writer.write(f"\x1b[{val}A")
    user.cur_row = max(user.cur_row-val, 1)
    if drain:
      await user.writer.drain()

async def ansi_down(user, val=1, drain=False): 
  assert not val < 0:
  if val > 0:
    if val<=3 or user.cur_row>=user.screen_height-3:
      await user.writer.write(lf*min(val, user.cur_row - user.screen_height)) # check: will this shortcut mess with our handling of ansi scroll regions?
    else:
      await user.writer.write(f"\x1b[{val}B")
    user.cur_row = min(user.cur_row+val, user.screen_height)
    if drain:
      await user.writer.drain()

async def ansi_move(user, row=None, col=None, drain=False): # we have the drain option because if we're moving the cursor in(to) an input field, the user will want to see where he's about to type.
  if row is None:                                           
    row = user.cur_row                                      
  if col is None:
    col = user.cur_col
  assert row > 0 and col > 0                      # should we raise an error if row or col exceeds the boundaries of the screen?
  if user.cur_row != row and user.cur_col != col: 
    await user.writer.write(f"\x1b[{row};{col}H")
    user.cur_row = min(row, user.screen_height)
    user.cur_col = min(col, user.screen_width) 
    if drain:
      await user.writer.drain()
  elif user.cur_row != row and user.cur_col == col: 
    if col > user.cur_col:
      await ansi_right(user, col-user.cur_col, drain)
    else:
      await ansi_left(user, user.cur_col-col, drain)
  elif user.cur_row == row and user.cur_col != col:
    if row > user.cur_row:
      await ansi_downt(user, row-user.cur_row, drain)
    else:
      await ansi_up(user, user.cur_row-row, drain)
 
async def ansi_color(user, fg=None, bg=None, fg_br=None, bg_br=None): # note that any color property not passed here will remain as it currently is rather than resetting to default.
  # note: syncterm blinks instead of bright background
  codes = []                                                                            
  if (fg is None and bg is None and fg_br is None and bg_br is None):
    if user.cur_fg != white or user.cur_bg != black or user.cur_fg_br != False or user.cur_bg_br != False:
      user.cur_fg = white
      user.cur_bg = black
      user.cur_fg_br = False
      user.cur_bg_br = False
      await user.writer.write("\x1b[m") 
  else:
    if fg_br is True:
      if not user.cur_fg_br:
        codes.append("1")
        user.cur_fg_br = True
    elif fg_br is False:
      if user.cur_fg_br:
        codes.append("22")
        user.cur_fg_br = True
    if bg_br is True:
      if not user.cur_bg_br:
        codes.append("5")
        user.cur_bg_br = True
    elif bg_br is False:
        if user.cur_fg_br:
          codes.append("25")
          user.cur_bg_br = False
    if fg is not None and fg != user.cur_fg:  
      codes.append(str(arg+30))
      new_fg = fg
    if bg is not None and bg != user.cur_bg:
      codes.append(str(arg+40))
      new_bg = bg
    if codes: 
      if user.cur_fg == white and user.cur_bg == black and user.cur_fg_br == False and user.cur_bg_br == False:
        await user.writer.write("\x1b[m") 
      else:
        await user.writer.write(f"\x1b[{+';'.join(codes)}m") 

async def ansi_cls(user, fg=None, bg=None, fg_br=None, bg_br=None):
  ansi_color(user, fg, bg, fg_br, bg_br)
  user.writer.write("\x0c")
  user.cur_col = user.cur_row = 1

async def clear_input_line(user, row, col, length):
  if user.in_input == False:
    await ansi_move(user, row, col, in_input=True)
  await send(user, " "*length)

async def read_cursor_position(user, timeout=2.0): # if this times out, that' going to suck...
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

def similarity_checker(str1, str2): # todo: fix this
  ret = RetVals()
  r = 0
  for a, b in zip(str1, str2):
    if a==b:
      r += 1
    else:
      break
  else:
    if len(a) == len(b):
      return "both"
    elif len(a) < len(b):
      return "left"
    else:
      return "right"
  return r


async def do_menu(user, menu): # todo: don't show an option if your keys are incompatible, or maybe make them dark gray
                               #       show Tel: Teleconference if there's another item that starts with Te
                               #       what to do about capitalization similarities and differences?
                               # todo: tell the user if they selected an option they don't have access to. though maybe do_destination does a good enough job of that already.
                               # todo: sort the menus by length, then separate them into bins of height enough for them to fit on the screen up and down, then 
                               #       randomize the order of each bin, then randomize the order of the bins themselves, then show them all aligned with their bins.
                               #       this will give optimal space while not making it look awkward.
                               #       or i could just use alphabetical order, or the order they're given in :P
                               #       eithe way, still separate them into bins and show the bins only as far away from each other as necessary given their longest elements
                               #       with a little extra space in between.
                               #       or would that look bad? should the bins be equally spaced according to the longest element in the whole list?
                               #       todo: see how galacticomm does it. 
  if menu.screen.path: 
    option = show_screen(user, menu.screen.path, r).input_fields["option"] 
  else:
    allowed_options = set(option for option in menu.options if check_keys(user, option).allowed)
    await ansi_color(user, *user.default_menu_color) # todo: specify a default menu color
    for option in menu.options: 
      if option2 in allowed_options: # not sure if iterating through menu.options gives me names of options ;/
        similarity = max(similarity_checker(option, option2) for option2 in menu.options if option2 in allowed_options)
        await send(user, option2[:similarity]+": "+option2)
      else:
        if not user.default_inaccessible_color is False: # todo: does false in yaml make False in Python?
          await ansi_color(user, *user.default_inaccessible_color) 
          await send(user, option) # todo: we need to distribute these things across the screen, not just make a vertical list. we also need a contigency plan in case there are too many options to fit.
          await ansi_color(user, *user.default_menu_color) 
    
  matched_options = [o for o in menu.options if o.lower() == option.tolower()]
  matched_exact = [o for o in menu.options if o == option]
  r = RetVals()
  r.input_fields = {"option": option} 
  if len(matched_options)==1:
    r.input_fields = {"option": matched_options[0]} # todo: or should we have r.option = ...
    r.next_destination = matched_options[0] # wait is this going to be the letter of the option or the data of the option? i never figured that out. 
    r.status = success
  elif len(matched_options)==0:
    def next_destination(user):
      r.next_destination = menu
      return await send(user, "You did not enter a valid option.", r)
    r.next_destination = 
  else:
    if len(matched_exact) == 1:
      r.next_destination = matched_options[0] 
      r.status = success
    elif len(matched_exact) == 0:
      r.next_destination = menu
      r.status = "too many matches" # todo: tell the user about the error
    else:
      r.next_destination = menu
      r.status = "multiple exact matches"
  return r


async def do_input_screen(user, dest, r): # todo: make it so the user can cycle through simultaneous inputs using tab, or enter, but when do we return all the values?
  # todo: this needs to be in an input_screen class.
  input_fields = {}
  if screen.path: 
    await show_screen(user, dest.screen_path, r)
  for inp in dest.inputs:
    input_fields[inp]=InputField(user, inp, r)
  user.input_fields = input_fields
  user.cur_input = input_fields[dest.inputs[0]] # todo: what to do if dest.inputs is empty?
  while True:
    for inp in get_code(user):
      r = await user.cur_input.process_input(inp, r) 
      if r.status == "submit":
        r = await getattr(validators, user.cur_destination)._submit(user, values, r)
        if r.status == success:
          r = await getattr(validators, user.cur_destination)._execute(user, values, r)
          if r.status == success:
            r.values = values
            r.next_destination = r.previous_destination
            return r
          else:
            send(user, "Submission failed because of reason: " + r.status, r) # we might need to figure out our scrolling region for sending this.
        else:                                                                   # todo: maybe _execute should return a dict of errors, too? why not?
          for input_field, err_msg in r.err_msgs.items():                       # or maybe a failed execution should bring us to some error page?
            input_field.show_err_msg(err_msg)                                   # user should always have a scroll region defined in is config for receiving messages
                                                                    # todo: wait, where's next_destination? how do we know what it is? 
                                                                    # ok, we need to call getattr(validators, user.cur_destination)._execute(user, values, r)
                                                                    # when r.status says "submitted" (we should probably also have a case in which to 
                                                                    # run validators...._submit()) and that program will know where the next destination is.
                                                                    # it will return it in return_value.next_destination.
  r = RetVals()
  lacking_keys = item.white_keys - user.keys
  bad_keys = item.black_keys & user.keys
  return r(allowed=bool(lacking_keys or bad_keys), lacking_keys=lacking_keys, bad_keys=bad_keys)

async def show_screen(user, screen_path):
  await ansi_cls()
  await send(user, open(screen_path, "r").read()) 
  return 
  # todo: this runs the risk of a zombie coroutine showing the user a screen out of nowhere. wait, could the same thing happen with other input, now that i'm using classes instead of functions?

#configuration variables can be accessed as config["a"]["] or config.a.b
con = sqlite3.connect(config.database)
cur = con.cursor()
con.row_factory = sqlite3.Row 

users_logging_in = set()
users = {}

class GlobalData: 
  def __init__(self):
    self.users = {}
    self.users_logging_in = set()
  
global_data = GlobalData()

async def do_destination(user, destination, menu_item, r): 
  r = check_keys(user, destination)
  if not r.allowed:
    status = fail
    err_msg = "Missing keys: " + str(r.lacking_keys) + "Bad keys: " + str(r.bad_keys)
    r = RetVals(next_destination=user.destination_history[-1] if user.destination_history else Destinations.user_director, status=status, err_msg=err_msg)
    # todo: this should return a function to talk to destination too, even if it's set to None, 
    # or we should change RetVals so that getting a nonexisting attribute returns something False=equivalent,
    # and so does getting a nonexisting attribute of a nonexisting attribute, etc.
  elif destination.type == "class":
    r = await getattr(Destinations, destination)(user, destination, menu_item, r)  
  elif destination.type == "menu":                                               
    r = await do_menu(user, destination, menu_item, r) # how will the menu know to render itself instead of going into an option? i guess if destination==menu_item?
  elif destination.type == "input":
    r = await do_input_screen(user, destination.target, r)
  elif destination.type == "module":
    r = await modules[destination].run(user, destination, menu_item, r)
  return r

class Disconnected(Exception):
  def __init__(self, user):
    self.user = user
  
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
      if combined in keyboardcodes:
        user.cur_input_code = ""
        return keyboardcodes[combined]
      if combined in keyboard_code_starts:
        user.cur_input_code = combined
        continue
      else:
        user.cur_input_code = ""
        continue  # unrecognized sequence, try again
    else:
      return char

async def user_loop(reader, writer): todo: r and user.destination_history should include the history of menu items, not just destinations.
  user = User(reader, writer)
  r = RetVals(next_destination=Destinations.login)  
  todo: uh oh, sometimes next_destination is treated as a string and sometimes it's treated as the destination object itself, i think. i remember seeing do_destination looking up getattr and such. 
  while True: 
    try: 
      r = await do_destination(Destinations.user_director, user, None, r) # user_director should juggle between r.next_destination, user.destination_history[-1], and config.main_destination
      user.cur_destination = Destinations.user_director(user, r.next_destination)
      user.destination_history.append(user.cur_destination)  # todo: but we can't do that, or their history will remember all their past class instances, because instance is stored under cur_destination.
     except Disconnected as e:
       global_data.users.remove(user) # i'm imagining the only reference to the instantiation of the class, menu or input destination she was in was in user.cur_destination, and i just removed that
       break
     except Exception as e:
       if "debug" in user.keys:
         send(user, "There was an error:" + traceback.format_exc(), sender="user_loop")
       else:
         send(user, "There was an error.")

async def main():
  server = await telnetlib3.create_server(host=config.hostname, port=config.port, shell=user_loop)
  await server.wait_closed()

if __name__=="__main__":
   main()

# real-time one-on-one chat where each chat is in its own space, you can see the letters being typed
# or make it support more than two people? there was a multiplayer chat in Hackers, make it like that.
# or was that The Matrix?
# show stars constantly twinkling into and out of existence with special ascii characters, 
# but make it optional. send the twinkle updates on a timer of course. twinkling would work much better for 
# dial-up than telnet.
# moving stack based system, there's a stack that defines where you are  is the menu system at any
# time, but you can jump to any other stack state, i.e., anywhere else in the menu system, and 
# the stack state determines what you can do from there and what the BBS listens to and how it responds
# e.g., there are global commands that work almost everywhere, just not in doors or real-time chat,
# and there's a line input mode that works everywhere but in doors and real-time chat
# how do I do this?
# have functions that do everything, store them in a list that represents the stack, one for each user's 
# state. and we need to somehow mix in other functions that apply more globally. the functions are all 
# input and output.
# should line input at the bottom just be the lowest function in the stack? which is replaced by another 
# function when they're in a realtime chat or in a door? or should it more describe a type of function?
# and should global commands really be mixed in with more local functions, like injected, or should they 
# just be hardcoded to be everywhere except in realtime chat and in doors? 
# should handling connects and disconnects also be a function in these stacks? arguably no, since that 
# function defines when a user goes into a stack to begin with
# maybe i'm overthinking it with the stack. e.g. if they're 5 deep in a menu, just have x of that menu item 
# point to the next higher menu. it's all on a flat landscape. 
# one process per node
# no, this is wrong. telnetlib3 is asynchronous so it's perfect more multiple users, according to claude.ai. but it says i still need
# subprocess to support door programs.
# also coroutines don't guard against cpu-intensive tasks, will i have any of those? hmm...# i guess i could just spawn a subprocess 
# if/when I do?
# redis for inter-node communication, such as tele or message boards (does redis make a good database?)
# support all door types, the various dropfiles, passing a com port via command line, fossil drivers, etc.
# maybe send ESC [ = 2 5 5 h before lfing a door, defined in the bananaansi file, but i'm not sure if it's a bananaansi thing only.
# ESC [ 2 5 5 n report screen size - how popular is support for this? claude.ai says it's not standard. 
# esc[6n to report current cursor position. reports it as e.g. esc24;80R
# use DOSBox to run doors, communicate with DOSBox via subprocesses and/or sockets
# messaging works like notepad, does word wrap, insert, etc., or at least like edit.exe.
# support avatar (ansi alternative) control codes
# "6. Avatar, as an asymetrical protocol, allows more than file transfer. It can
# handle such things as a user logon to a system, transfer of multiple files
# in either direction simultaneously with other activities, etc. Further
# details are beyond the scope of this document."
# would be nice to know how to do taht and whether terminals that support avt support that
# claude.ai said they don't support avt/1. and all the interesting codes are in avt/1, so i may not even support avatar, 
# except to read keyboard keys (in avt, they're like null plus the scan code or something like that)
# er, no, bansi.txt defines enough keys, i don't need to include a bunch of scan codes where they may conflict with the ones bansi
# defines and i'm not even sure which keyboard standard avt uses.
# if i support avatar, i should ask the user if their terminal supports it when they sign up. but i'd need to make
# the bbs in a way such that if they don't support it and it's enabled, what they see indicates clearly enough how to disable it.
# (claude.ai said that no way to detect for avatar in avt/0 is why it never became popular.)
# use colorama (on windows) to allow the sysop to emulate a user, but must set the console size to the user's screen
# dimensions
# support dial-up with pyserial
# line input modes works like you type on the bottom line, everything else happens higher up, and if you
# keep typing off the right side of the screen then your entire text moves to the left. if you hit home
# or move your arrow key all the way to the left again the text moves to the right again. end works too.
# apparently bbs's scroll down when the last character is occupied, not when one more is added after that. 
# so we can never use the last character in line input, or we'd have to disable wrap when working with the 
# input line and re-enable it when done with that for then. 
# reply to parts of a message like in gmail. provide a key to remove a whole line. ctrl-k? 
# how about beautiful squares with shading to hold the individual bbs menu commands?
# IRC interface? no, can't do that, i'd have too many connections from the host
# file libraries with zmodem and ymodem, maybe give the user an option of whether to use 8.3 filenames?
# ymodem-g is the variant that doesn't use crc checks.
# the files i got that support zmodem and ymodem-g use callbacks, not asyncio, so i'll have to figure out how to convert them
# or maybe claude.ai can do it.
# do it like windows used to, ABCDE~2.FGH for clashing filename conversions. or would that conflict with 
# their OS's naming scheme?
# don't have categories for files, have tags, and you can specify which tags have to be included or have
# to not be included when you list files, maybe even using arbitrarily nested groupings
# maybe also have an option to group files by their tags, that would involve a grouping structure that 
# holds many files and categories in redundant places. present it to the user like a collapsible tree.
# make serial port speed 192K, because 56K modems can compress repeating text up to 4X. or do I have to 
# adjust it to the available hardware/let the sysop adjust it?
# streamline the process of adding doors, unlike mbbs/wg. specify the type of door and the exe name and
# what the menu option will be called and maybe what submenus it'll be under, and voila, it's done. 
# also have an internal list of what the types of the most popular doors are to make it easier (but let
# the sysop override the default of course)
# how hard would it be to make it compatible with MBBS/WG addons?
# have protuction against +++ hacking for dialup? 
# have protection against m00fing in realtime chat? just don't hang up when the output buffer gets full?
# claude.ai says practically no users would ever be connecting without ANSI support. 
# options are case-insensitive except where there are two options in the same menu with different cases