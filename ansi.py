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
