# don't forget ctrl+z. i guess we can't do ctrl+shift+z?
# todo: add color for bbs msgs, teleconference feed, etc.
# what to do when cursor is all the way to the right? edit.exe doesn't let the cursor go futher than the rightmost column, rightmost character stays there as you're inserting,
# but what would I do if i'm at the end of content_length and i hit insert?
# I guess just move the cursor one to the left and then disable insert mode.
# but what do I do if content_length==length and the cursor is at the end?  
# claude says to move the cursor to the last character and don't allow any input, but what if the user then presses del or backspace? it would be inoconsistent..
# maybe just allow the cursor to inhabit one space to the right of the input field if height==1 and length==content_length or length>=content_length?
# maybe we should just break down and let content_length be one less than input length for height==1
# todo: change length==1 to not move the cursor one to the left when it's at field_length+1
# self.row_offset, self.col_offset start at 1, every other row and col here starts at 0.

from copy import deepcopy

from common import *
from input_output import *
from config import get_config
from definitions import *
config = get_config()

class InputFields: # todo: how will I detect mouse clicks in the middle of getting user input keys?
  def __init__(self, user):
    self.input_fields = []
    self.user = user
  async def input_field(self, **kwargs):
    self.input_fields.append(await InputField.create(parent=self, allow_edit=False, **kwargs))
  async def run(self):
    pass # todo

class InputField:
  def __init__(self):
    pass

  @classmethod
  async def create(cls, parent=null, conf=null, height=null, length=null, length_from_end=null, height_from_end=null, max_length=null, max_lines=null, fg=null, fg_br=null, bg=null, bg_br=null, fill=null,
                     fill_fg_br=null, fill_fg=null, fill_bg=null, fill_bg_br=null, outline=null, outline_double=null, outline_fg=null, outline_fg_br=null, outline_bg=null, outline_bg_br=null, insert_mode=null,
                     scroll_vert=null, scroll_horiz=null, content="", allow_edit=null):
    self = cls()
    self.row_offset = self.user.cur_row
    self.col_offset = self.user.cur_col
    self.row = self.col = 0
    self.outline = conf.outline if outline is null else outline
    if self.outline:
      self.col_offset = self.col_offset+1
      self.row_offset = self.row_offset+1
    self.height = height or conf.height # height shouldn't be 0, so we can do this
    self.length = length or conf.length # length shouldn't be 0
    self.height_from_end = conf.height_from_end if height_from_end is null else height_from_end
    self.length_from_end = conf.length_from_end if length_from_end is null else length_from_end
    if self.height is null and self.height_from_end is not null:
      self.height = self.user.screen_height-self.row_offset+1-self.height_from_end
    if self.length is null and self.length_from_end is not null:
      self.length = self.user.screen_height-self.row_offset+1-self.length_from_end
    self.max_length = max_length or conf.max_length # max_length shouldn't be zero
    self.max_lines = conf.max_lines if max_lines is null else max_lines
    assert self.content_length
    self.parent = parent
    self.fg = colors[conf.content.fg] if fg is null else fg
    self.fg_br = conf.content.fg_br if fg_br is null else fg_br
    self.bg = colors[conf.content.bg] if bg is null else bg
    self.bg_br = conf.content.bg_br if bg_br is null else bg_br
    self.fill = conf.blank.char if fill is null else conf.blank.char
    self.fill = self.fill or " " # not using 'if ... is null' because character 0 doesn't show anyway
    if type(self.fill) is int:
      self.fill = chr(self.fill)
    self.fill_fg = colors[conf.content.blank.fg] if fill_fg is null else fill_fg
    self.fill_fg_br = conf.content.blank.fg_br if fill_fg_br is null else fill_fg_br
    self.fill_bg = colors[conf.content.blank.bg] if fill_bg is null else fill_bg
    self.fill_bg_br = conf.content.blank.bg_br if fill_bg_br is null else fill_bg_br
    self.scroll_vert = conf.scroll_vert if scroll_vert is null else scroll_vert
    self.scroll_horiz = conf.scroll_horiz if scroll_horiz is null else scroll_horiz
    self.insert_mode = conf.insert_mode if insert_mode is null else insert_mode
    self.outline = conf.outline if outline is null else outline
    self.content = content
    self.allow_edit = conf.allow_edit if allow_edit is null else allow_edit
    self.words = [Estr("", content_row=0, content_col=0), Estr("", content_row=0, content_col=0)]
    if self.height==1:
      self.content=""
    else:
      self.content=[]
    self.word_indices = [[invalid for y in range(self.height)] for x in range(self.width)]
    self.word_indices[0][0]=1
    if self.outline:
      await self.draw_outline()
    if parent==null:
      return await self.run()
    self.col = self.content_col_offset = 0
    if self.col+self.length-1>self.user.screen_width:
      raise ValueError("Input field would extend beyond screen width.")
    if self.col_offset+self.length-1==self.user.screen_width:
      await ansi_wrap(self.user, False)
    self.col_offset = self.user.cur_col
    self.content_length = 0

  async def run(self):
    # makes the input field starting where the cursor currently is at.
    # col = beginning col of input field
    # field_pos = position within the input field, starting at 0
    # content_pos = the current index of the content at field_pos 0
    # content = current user input
    # fill = character ascii number to fill empty space with
    # todo: support outline around input
    # todo: process buffers by doing all the calculations without writing anything yet
    # should we break up even calculating buffers so we don't disrupt the other users? how large a chunk size should we use? claude says no.
    # content_pos+field_position==len(content) and self.insert_mode==True is a special case. field_pos+col_offset will actually be 1 greater than user.cur_col. this is so the cursor stays inside the edit field.
    # field_length should never be > content_length
    # todo: constantly blink block cursor with a timer, alternating between block cursor and character at that point? claude says that's non-standard and may be confusing, but it seems familar.
    # but also, would that cause periods of stillness followed by very rapid blinking due to network delays?
    if self.height==1:
      while True:
        key = await get_input_key(self.user)
        if key == "left":
          if self.col == 0:
            if self.content_col_offset > 0: # field is scrolled to the right, cursor is at the beginning
              self.content_col_offset -= 1
              if self.insert_mode:
                await send(self.user, self.content[self.content_col_offset:self.content_col_offset+self.length])
              else:
                await ansi_color(self.user, self.bg, self.fg, False, False)
                await send(self.user, self.content[self.content_col_offset]) # write inverted color char at cursor pos
                await ansi_color(self.user, self.fg, self.bg, self.fg_br, self.bg_br)
                await send(self.user, self.content[self.content_col_offset+1:self.content_col_offset+self.length]) # write rest of self.content in normal colors
              await ansi_move(self.user, col=self.col_offset)
          else:
            self.col -= 1
            if self.insert_mode:
              await ansi_left(self.user)
            else:
              await send(self.user, self.content[self.content_col_offset+self.col+1])
              await ansi_color(self.user, self.bg, self.fg, False, False)
              await send(self.user, self.content[self.content_col_offset+self.col])
              await ansi_color(self.user, self.fg, self.bg, self.fg_br, self.bg_br)
              await ansi_left(self.user)
              await ansi_left(self.user)
        elif key == "right":
          if self.col == self.length-1: # cursor is at the very right
            if self.col+self.content_col_offset <= len(self.content): # make sure cursor is not at end of self.content already # off by one maybe?
              self.content_col_offset += 1
              await ansi_move(col=self.col_offset) # move the cursor the easy/cheating way, we totally optimized ansi_move() anyway.
              if self.insert_mode:
                await send(self.user, self.content[self.content_col_offset:self.content_col_offset+self.length])
              else:
                await ansi_move(col=self.col_offset)
                await send(self.user, self.content[self.content_col_offset:self.content_col_offset+self.length-1]) # send normal characters up until the inverted character
                await ansi_color(self.user, self.bg, self.fg, False, False)
                await send(self.user, self.content[self.content_col_offset+self.length])              # send the inverted character
                await ansi_color(self.user, self.fg, self.bg, self.fg_br, self.bg_br)
              await ansi_left(self.user)
          else:
            self.col += 1
            if self.insert_mode:
              await ansi_right(self.user)
            else:
              await send(self.user, self.content[self.content_col_offset+self.col-1])                 # send normal character to replace the inverted character
              await ansi_color(self.user, self.bg, self.fg, False, False)
              await send(self.user, self.content[self.content_col_offset+self.col])                   # send inverted character to replace the normal character one to the right
              await ansi_color(self.user, self.fg, self.bg, self.fg_br, self.bg_br)
              await ansi_left(self.user)
        elif key == "home":
          if self.content_col_offset > 0:
            self.col = self.content_col_offset = 0
            await ansi_move(col=self.col_offset)
            if self.insert_mode:
              await send(self.user, self.content[:self.length])    # send <field_length> many characters of self.content
              await ansi_move(col=self.col_offset)
            else:
              await ansi_color(self.bg, self.fg, False, False)
              await send(self.user, self.content[0])
              await ansi_color(self.fg, self.bg, self.fg_br, self.bg_br)
              await send(self.user, self.content[1:self.length])
          else:
            await ansi_color(self.bg, self.fg, False, False)
            await send(self.user, self.content[0])
            await ansi_right(self.user, self.col)
            await ansi_color(self.fg, self.bg, self.fg_br, self.bg_br)
            await send(self.user, self.content[self.col])
            await ansi_move(col=self.col_offset)
          await ansi_move(self.user, col=self.col_offset)
        elif key == "end":
          if len(self.content) <= self.length:
            await ansi_right(self.user, len(self.content)-self.col)
            self.col = len(self.content)
          else:
            await ansi_move(self.user, col=self.col_offset)
            self.content_col_offset = len(self.content)-self.length+1
            await send(self.user, self.content[self.content_col_offset:self.content_col_offset+self.length])
            await ansi_color(self.user, self.fill_self.bg, self.fill_self.fg, self.fill_self.bg_br, self.fill_self.fg_br)
            await send(self.user, self.fill)
            await ansi_color(self.user, self.bg, self.fg, self.bg_br, self.fg_br)
        elif key == "ins":  # todo
          self.insert_mode = not self.insert_mode
          if self.insert_mode:
            await send(self.user, self.content[self.content_col_offset+self.col]) # insert was turned on, replace block with the self.content character at that col.
            await ansi_left()
          else:
            await ansi_color(self.user, self.bg, self.fg, False, False)
            await send(self.user, self.content[self.content_col_offset+self.col])
            await ansi_color(self.user, self.fg, self.br, self.fg_br, self.bg_br)
            await ansi_left(self.user, self.bg, self.fg)
        elif key == "back":
          if self.col==0:
            if self.content_col_offset>0:
              self.content_col_offset -= 1
              self.content=self.content[:self.content_col_offset]+self.content[self.content_col_offset+1:] # delete a char from self.content. we're at self.col=0 so we don't have to factor in self.col.
          else:
            self.col -= 1
            self.content_col_offset -= 1
            self.content=self.content[:self.content_col_offset+self.col]+self.content[self.content_col_offset+self.col+1:] # delete a char from self.content at new self.content_col_offset. factor in self.col.
            await ansi_left(self.user)
            if self.insert_mode:
              await send(self.user, chr(217)+self.content[self.content_col_offset+1:self.content_col_offset+self.length-self.col]) # check: is this accurate?
            else:
              await send(self.user, self.content[self.content_col_offset:self.content_col_offset+self.length-self.col]) # check: is this accurate?
            if self.length>len(self.content)-self.content_col_offset:
              await ansi_color(self.user, self.fill_self.fg, self.fill_self.bg, self.fill_self.fg_br, self.fill_self.bg_br)
              await send(self.user, self.fill)
              await ansi_color(self.user, self.fg, self.bg, self.fg_br, self.br_br)
        elif key == "del":
          end_pos = len(self.content) - self.content_col_offset-1
          if end_pos==self.col: # if cursor is right at the end of the self.content
            self.content = self.content[:self.col+self.content_col_offset-1]
            if self.insert_mode:
              await ansi_color(self.user, self.fill_self.fg, self.fill_self.bg, self.fill_self.fg_br, self.fill_self.bg_br)
              await send(self.user, self.fill)
            else:
              await ansi_color(self.user, self.fill_self.bg, self.fill_self.fg)
              await send(self.user, self.fill)
              await ansi_color(self.user, self.fg, self.bg, self.fg_br, self.bg_br)
          else:
            if end_pos < self.length + 1: # if there are multiple self.fill characters after the self.content # check: off by one error?
              self.content = self.content[:self.content_col_offset]+self.content[self.col+self.content_col_offset+1:]
              if self.insert_mode:
                await send(self.user, self.content[self.col+self.content_col_offset:self.col+self.content_col_offset+self.length-self.col]) # check: is this correct? and is there an off by one error?
                await ansi_color(self.fill_self.fg, self.fill_self.bg, self.fill_self.fg_br, self.fill_self.bg_br)
                await send(self.user, self.fill)
                await ansi_move(self.user, col=self.col_offset+self.col) # move cursor back to where it belongs
              else:
                await ansi_color(self.user, self.bg, self.fg, False, False)
                await send(self.content[self.col+self.content_col_offset])
                await ansi_color(self.user, self.fill_self.fg, self.fill_self.bg, self.fill_self.fg_br, self.fill_self.bg_br)
                await send(self.user, self.fill)    # print the rest of the self.fill characters to the end of the input field in normal self.fill colors.
            else: # if self.content takes up the entire field
              self.content = self.content[:self.content_col_offset]+self.content[self.col+self.content_col_offset+1:] # delete a char from self.content.
              if self.insert_mode:
                await send(self.user, self.content[self.col+self.content_col_offset:self.col+self.content_col_offset+-self.length-self.col]) # print self.content from self.col to end of input starting with the appropriate self.content pos for the horizontal scroll
              else:
                await ansi_color(self.user, self.bg, self.fg, False, False)
                await send(self.user, self.content[self.col+self.content_col_offset]) # send current char in reverse colors
                await ansi_color(self.user, self.fg, self.bg, self.fg_br, self.bg_br)
                await send(self.user, self.content[self.col+self.content_col_offset+1:self.col+self.content_col_offset+self.length-self.col]) # send rest of chars in normal colors
        elif key == ctrl_u: # ^U = clear line
          self.content = ""
          self.col = self.content_col_offset = 0
          await ansi_move(col=self.col_offset)
          await ansi_color(self.user, self.fill_self.fg, self.fill_self.bg, self.fill_self.fg_br, self.fill_self.bg_br)
          await send(self.user, self.fill*self.length)
          await ansi_color(self.user, self.fg, self.bg, self.fg_br, self.br_br)
        elif key == cr:
          await send(self.user, cr+lf)
          return self.content
        elif len(key)==1 and ord(key) >= 32:
          if self.insert_mode:
            if len(self.content) < self.content_length:
              self.content = self.content[:self.col+self.content_col_offset]+key+self.content[self.col+self.content_col_offset:]
              await send(self.user, self.content[self.content_col_offset+self.col:self.content_col_offset+self.col+self.length-self.col])
              await ansi_move(self.user, col=self.col_offset+self.input_pos)
            self.col += 1
          else:
            self.content=self.content[:self.col+self.content_col_offset]+key+self.content[self.col_self.content_col_offset+1:]
            end_pos = len(self.content)-self.content_col_offset
            self.content.append(key)
            await send(self.user, key)
            await ansi_color(self.user, self.fg, self.bg, self.fg_br, self.bg_br)
            await send(self.user, key)
            if self.col == end_pos: # cursor is one to the right of the self.content, self.fill char is currently inverted
              if self.col < self.length-1: # self.col better not be > field_length-1, so if it's not < then it's ==, in which case we wouldn't send a new inverted self.fill char
                await ansi_color(self.user, self.fill_self.bg, self.user_self.fill_self.fg, False, False)
                await send(self.user, self.fill)
                await ansi_left(self.user)
            else: # self.col had better be < end_pos, because self.col>end_pos is an invalid state, the cursor would be in the middle of self.fill characters
              await ansi_color(self.user, self.bg, self.fg, False, False)
              await send(self.user, key)
              await ansi_color(self.user, self.fg, self.bg, self.fg_br, self.bg_br)
              await ansi_left(self.user)
        await self.user.writer.drain()
    else:
      while True:
        key = await get_input_key(self.user)
        if key == cr: # carriage return aka enter aka return # don't let the cursor go down if it would push text beyond the bottom of the input field and config.input_fields.scroll_inside is disabled.
          if self.allow_edit:
            if self.content_length >= self.max_length:
              continue
            if (not self.scroll_vert) and len(self.content) >= self.height:
              continue
            if len(self.content) == self.max_lines and self.max_lines is not null:
              continue
            self.content_length += 1
            if self.row==self.height:
              if self.scroll_vert:
                if self.col_offset==0 and self.width==self.user.screen_width: # if we can just terminal scroll a region of the screen
                  if self.row_offset>0 or self.height<self.user.screen_height: # if that region is not the entire screen
                    await ansi_set_region(self.user, self.row_offset, self.user.screen_height)
                    await ansi_set_region_strict(self.user, True) # check: does clearing the screen reset the terminal's scroll region policy to lax?
                  await send(self.user, cr+lf, drain=True)
                self.content_row_offset += 1
              else:
                continue
            i = self.word_indices[self.row+self.content_row_offset][self.col+self.content_col_offset]
            if i==invalid:
              raise Exception("Input field was in an invalid state: cursor outside text content")
            if self.words[i]=="":
              self.words[i]=cr

            elif i.index_into_word==len(self.words[i]):
              self.words.insert(i+1, cr)
            elif i.index_into_word==0:
              self.words.insert(i, cr)
            else:
              self.words[i]=self.words[i][:i.index_into_word]
              self.words.insert(i+1, cr)
              self.words.insert(i+2, self.words[i][i.index_into_word:])
            await self.redraw_field() # todo: make this function update self.word_indices too. # todo: make this more efficient so we don't always recompute the word wrapping for the entire field and also check each character when redrawing it.
        elif key==tab:
          if self.parent:
            return key
        elif key=="left":
          i = self.words[self.row][self.col]
          word = self.words[i]
          # should we return if cursor goes past beginning or end of content?
          if self.col>0:
            self.col -= 1
            if word.index_into_word>0:
              word.index_into_word -= 1
              await ansi_left(self.user)
            else:
              if i>0:
                previous_word = self.words[i-1]
                if previous_word==cr:
                  if self.col>0:
                    if row









        index = self.content_index_array[self.cur_row][self.cur_col]
        self.content = self.content[:index]+cr+self.content[index:]
      for l in range(conf.height):
          await ansi_move(self.conf.row+l, conf.col)
          await send(user, bytes((conf.bg_chars.ord,) or (32,))*self.width)
          await ansi_move(user, conf.row, conf.col)
          await user.writer.drain()
    self.col_to_content_index = [[null*conf.width] for _ in range(conf.height)]
    self.content_index_to_pos = [] # probably won't need this either.
    # we could keep an array of all word positions plus how many spaces and how many cr's are after each word
    # to make it easier to compute word wrap, but then we have to modify it without iterating over the whole thing
    # every time we insert or delete a char. so it may not be worth it. hmm, let's do it.
    # should we store lines of words, or just a 1D array of words? or a 1D array of words, cr's, spaces, rows and cols?
    # hmm, you can have any combination of spaces and cr's after a word, and they should be preserved... so cr's should probably also be words.
    # or extra spaces should.
    self.words = []
    self.dists_from_right = [null*conf.height]
  async def recompute_word_wrap(self): # uh oh, what happens when the user pastes something into the middle of the text?
                                       # it would have to recompute word wrap for every character!
                                       # we need some kind of input buffer for this
                                       # i'll buffer it for as long as there's been more than 20 characters inputed
                                       # per second, that should be fine because it's faster than anybody can type.
                                       # i should do it in terms of input codes, not characters.
    starting_content_index = self.col_to_content_index[self.cur_row][self.cur_col]
    # todo: finish
  async def draw_outline(self):
    if self.outline:
      ansi_color(self.user, fg=self.outline_fg, fg_br=self.outline_fg_br, bg=self.outline_bg, bg_br=self.outline_bg_br)
      if self.outline_double: # todo: use unicode if user.terminal == PuTTy
        ords = chr(201), chr(205), chr(187), chr(186), chr(200), chr(188)
      else:
        ords = chr(218), chr(196), chr(191), chr(179), chr(192), chr(217)
      await send(self.user, ords[0] + ords[1]*self.width+ords[2]) # todo: don't forget when we need nowrap
      await ansi_move(self.user, self.row_offset, self.col_offset)
      for l in range(self.height):
        await ansi_color(self.user, self.outline_fg, self.outline_bg, False, False)
        await ansi_move(self.user, self.row_offset+l, self.col_offset-1)
        await send(self.user, ords[3])
        await ansi_color(self.user, self.fill_fg, self.fill_bg, self.fill_fg_br, self.fill_bg_br)
        await send(self.user, self.fill*self.width)
        await ansi_color(self.user, self.outline_fg, self.outline_bg, False, False)
        await send(self.user, ords[3])
      await ansi_move(self.user, self.row_offset+self.height+1)
      await send(self.user, ords[4] + ords[1]*self.width + ords[5]) # todo: don't forget when we need nowrap
    await ansi_move(self.user, self.row_offset, self.col_offset)

  async def redraw_field(self): # todo: this will recompute word wrap first, but how do we not recompute the entire word wrap for each character during a paste if word_indices is only changed by recomputing the word wrap?
                                # we should store content_row and content_col in self.words entries to help us solve this.