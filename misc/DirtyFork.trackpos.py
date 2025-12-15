import codecs
import subprocess, multiprocessing, asyncio, re
import redis, telnetlib3, serial, yaml 
from keyboardcodes import *

line_pos_re = re.compile(b'\x1b\[(\\d+);(\\d+)R')

config = yaml.load(open("DirtyFork.yaml", "r"))

#we should consider ruamel.yaml instead, it supports newer yaml spec and preserves formatting, but has 
#less of a userbase and a more complex api. we might want both the program and the user to modify yaml files.

top, bottom = 1, 2

class User:
  def __init__(self, reader, writer):
    self.reader = reader
    self.writer = writer
    self.screen_width = None
    self.screen_height = None
    self.handle = None
    self.account_num = None
    self.cur_x = None
    self.cur_y = None
    self.keys = set()

async def send(user, message, section=top):
  """Send data to user"""
  if isinstance(message, str):
    message = message.encode('utf-8')
  if section==top:
    ansi_wrap(user, True)
  else:
    ansi_wrap(user, False)  # 'Note that the next time you change the scrolling region, word wrap will be turned on again.'
  user.writer.write(message)
  await user.writer.drain() # if i understand correctly, there would never be any need to have drain be optional, because if it were then things could be sent to the user out of order?
    
async def ansi_wrap(user, wrap=True):
  if user.cur_wrap != wrap:
    if wrap:
      await user.writer.write(b"\x1b[?7h") # todo: do all clients support this? because if not, our input area will be totally fucked up. we could just be safe and not ever write to the right-most bottom column
    else:
      await user.writer.write(b"\x1b[?7l") 
    await user.writer.drain()
    user.cur_wrap = wrap

async def ansi_section(section):
         #ESC [ ? 6 h
  if section == top:

  
async def ansi_left(user, val=1): 
  if user.cur_x-val<1:            
    val = user.cur_x-1
  if val==1:
    await send(user, b"\x1b[D")
  elif val==0:
    pass
  else:
    await send(user, b"\x1b["+str(val).encode("utf-8")+"D")
  user.cur_x -= val

async def ansi_right(user, val=1):                # i hope all clients report their cursor position when asked, otherwise their screen size
  if user.cur_x+val>user.screen_width:            # could be set wrong, in which case this approach of keeping track of everything could mess it all up
    val = user.screen_width-user.cur_x            # another problem is that someone may resize their terminal. we could have a notice on the bbs that if
  if val==1:                                      # their terminal gets resized there's a key they can press to make the bbs redetect their size
    await send(user, b"\x1b[D")                   # should we raise an error if val is too far up, down, left or right instead of just reducing it? 
  elif val==0:
    pass
  else:
    await send(user, b"\x1b["+str(val).encode("utf-8")+"C")
  user.cur_x -= val

async def ansi_up(user, val=1): 
  if user.cur_y-val<1:          
    val = user.cur_y-1
  if val==1:
    await send(user, b"\x1b[A")
  elif val==0:
    pass
  else:
    await send(user, b"\x1b["+str(val).encode("utf-8")+"A")
  user.cur_y -= val

async def ansi_down(user, val=1): 
  if user.cur_y+val>user.screen_height: 
    val = user.screen_height-user.cur_y
  if val==1:
    await send(user, b"\x1b[D")
  elif val==0:
    pass
  else:
    await send(user, b"\x1b["+str(val).encode("utf-8")+"B")
  user.cur_x -= val

async def read_line_char(user):    # should we just ignore invalid inputs after null or esc, or should we process them? 
  if user.cur_input_code:        # todo: and what if the user literally presses esc? we need a timeout for anything after esc,
    char = await user.read.read(1) # unless the bbs never does anything with esc.
    user.cur_input_code += char
    if not any(x.startswith(user.cur_input_code) for x in keyboard_codes):
      user.cur_input_code = ""
  if char == b"\x00" or char == b"\x1b":
    user.cur_input_code = char
    key = keyboard_codes[user.cur_input_code]
    if key == "left":
      if user.cur_input_col == 1:
        if user.cur_input_pos > 1:
          user.cur_input_pos -= 1
          await send(user, user.cur_input[user.cur_input_pos:user.cur_input_pos+user.screen_width])
          await ansi_left(user.screen_width)
      else:
        ansi_left(user, 1)
    elif key == "right":
      if user.cur_input_col == user.screen_width:
        if user.cur_input_pos < len(user.cur_input):
          user.cur_input_pos += 1
          await ansi_left(user.screen_width)
          await send(user, user.cur_input[user.cur_input_pos:user.cur_input_pos+user.screen_width])
      else:
        ansi_right(user, 1)
        user.cur_input_pos += 1
    code = user.cur_input_code
    user.cur_input_code = ""
    return code
  elif key == ctrl_u or key == ctrl_c or key == enter:
    await ansi_left(user.cur_x-1)
    user.cur_input = ""
    await send(user, b"x\1b[2K")
  return key

async def read_line(user):
  while True:
    char = await read_line_char(user)
    if char is None:
      return None
    elif char == enter or char == linefeed:
      return user.cur_input
    
async def read_cursor_position(user, timeout=2.0):
    """Read terminal response for cursor position query"""
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
   user.writer.write(b"Detecting screen size...\x1b[s\x1b[999;999H\x1b[6n\x1b[u") 
   #save cursor position, move cursor to 999,999, send command to retrieve cursor position, restore cursor position
   await user.writer.drain()   
   return await read_cursor_position(user)

users_logging_in = set()
users = {}
async def main():
  reader, writer = await telnetlib3.open_connection(config.hostname, config.port) #hostname can be an IP address to bind to.
  user = User(reader, writer)
  users_logging_in.append(user)
  user.screen_height, user.screen_width = await get_screen_size(user)
  handle = await login(user)
  users_logging_in.remove(user)
  users[handle] = user
  users_logging_in.remove(user)
  



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
# maybe send ESC [ = 2 5 5 h before entering a door, defined in the bananaansi file, but i'm not sure if it's a bananaansi thing only.
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

