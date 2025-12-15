from itertools import batched

from ansi import *

def similarity_checker(str1, str2): # should this be case-sensitive or case-insensitive?
  r = 0
  for a, b in zip(str1, str2):
    if a==b:
      r += 1
    else:
      status = success
      err_msg = None
      break
  else:
    status = fail
    if len(a) == len(b):
      err_msg = "left and right are equal"
    elif len(a) < len(b):
      err_msg = "right contains left"
    else:
      err_msg = "left contains right"
  return RetVals(status=status, err_msg=err_msg, r=r)

def process_option(option, menu):
  matched_options = [o for o in menu.options if o.lower() == option.tolower()]
  matched_exact = [o for o in menu.options if o == option]
  r = RetVals()
  r.option = option
  if len(matched_options)==1:
    r.option = matched_options[0]
    r.next_destination = matched_options[0] # wait is this going to be the letter of the option or the data of the option? i never figured that out. 
    r.status = success
  elif len(matched_options)==0:
    r.next_destination = menu
    r.status = fail
    r.err_msg = "You did not enter a valid option."
  else:
    if len(matched_exact) == 1:
      r.next_destination = matched_options[0] # check: we need to pass menu and menu_item. how did we do this elsewhere?
      r.status = success
    elif len(matched_exact) == 0:
      r.next_destination = menu
      r.status = fail
      r.err_msg = "More than one item matches your input." # todo: tell the user about the error
    else:
      r.next_destination = menu
      r.status = fail
      r.status = "More than one item matches your input."
  return r

async def do_menu(user, menu): # todo: option to not show an option if your keys are incompatible
                               # todo: tell the user if they selected an option they don't have access to. though maybe do_destination does a good enough job of that already.
                               #       todo: see how galacticomm does it. 
                               # todo: enable mouse clicks with esc[1000h. how do we do this? this will be complicated. i guess call a function to associate a mouse click area rect 
                               # at the current cursor pos with a given menu item somehow. the InputField or InputFields should probably be aware of this because the click will be
                               # returned as a key while inputting. for screen.paths, we need some yaml associated with the screen to define click regions. otherwise, they should be 
                               # assigned automatically as the menu draws, maybe the menu options should be boxed?
  if menu.screen.path: 
    show_screen(user, menu.screen.path)
  else:
    options = []
    allowed_options = set(option for option in menu.options if check_keys(user, menu, option).status==success) 
    await ansi_color(user, **user.menus.color) # todo: specify a default menu color
    for option1 in menu.options: 
      r = 0
      for option2 in menu.options:
        if option1 != option2:
          similarity = similarity_checker(option1, option2) 
          if similarity.status == success:
            r = max(r, similarity.r)
          else:
            return RetVals(status=fail, err_msg=f"Options {option1} and {option2}: {r.errmsg}")
      options.append((option1, similarity))
    bins = batched(options, user.screen_height-1)
    cur_left = 1
    ansi_wrap(user, False)
    for bin in bins:
      max_len = max(map(len, bins))
      if max_len+cur_left > user.screen_width:
        ansi_move(user, user.screen_height, 1)
        send(user, "Enter an option or press <enter> for the next page: ")
        r = InputField(user, height=1, max_length=300, input_length=user.screen_height-user.cur_col) # todo: make InputField use InputField.yaml values
        if r.strip()=="":
          cur_left = 1
        else:
          ansi_wrap(user, True)
          return process_option(r, menu)
      else:
        for row, (option, similarity) in enumerate(bin, 1): # todo: what to do if there are too many options to fit on the page?
          await ansi_move(user, row, cur_left)
          if option in allowed_options:
            await ansi_color(user, **user.menus.colors.highlight)
            await send(user, bin[:similarity])
            await ansi_color(user, **user.menus.colors.normal)
            await send(user, bin[similarity:])
          else:
            await ansi_color(user, **user.menus.colors.noaccess)
            await send(user, bin)
        cur_left += max_len+3 # todo: is 3 a good value?
        send(user, "Enter an option: ")
        r = InputField(user, **config.InputFields.input_command) 
        ansi_wrap(user, True)
        return process_option(r, menu)
