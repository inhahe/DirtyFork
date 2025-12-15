# todo: store time_zone_hour and time_zone_minute in users table
# todo: we're going to store time as INT. then when we show it, 
# we just apply the time zone hours and minutes to the INT stamp
# i want to show it in this format: "%Y/%m/%d %H:%M:%S" and maybe the 3-4-letter code for the time zone
#  or the GMT offset like -3:45, is that a thing, to display the negatives that way? and to display minutes that way?
# todo: show return values around the input field when they're returned
# and/or: change the field's color, or its box color
# todo: add an option to input GMT+x time zone as opposed to time zone code?

import time, json, re
time_zones = json.load(open("time_zone.json", "r"))
import DirtyFork

#def get_timestamp():
#    """Get current UTC time as YYYY/MM/DD HH:MM:SS"""
#    return datetime.now(timezone.utc).strftime("%Y/%m/%d %H:%M:%S") + " GMT"

import bcrypt
from datetime import datetime

class register: 
  async def handle(value, user=None):
    DirtyFork.cur.execute("SELECT * FROM users WHERE handle = ? LIMIT 1 COLLATE NOCASE", (value.lower(),))
    if DirtyFork.cur.fetchone()
      return "Taken handle"
      #no returned value means it's fine.
  async def full_name(value, user=None):
    DirtyFork.cur.execute("SELECT * FROM users WHERE = ?", (value.lower(),))
  async def email(value, user=None): # todo: detect if other users on the board used the same email address 
    # (especially if no duplicate accounts allowed or 
    DirtyFork.cur.execute("SELECT * FROM users WHERE email = ?", (value.lower(),))
    if DirtyFork.cur.fetchone():
      return "Taken handle"
  async def sex(value, user=None): # even if required, sex just has to have anything in it. and there's already a check that required fields be populated.
    pass              # functions aren't called for fields that aren't required. but their re's are evaluated.
  async def age(value, user=None): # always filter out chars < 32. don't even let the input routine acknowledge them.
    pass
  async def location(value, user=None):
    pass
  async def time_zone(value, user=None):
    if not value.upper() in time_zones:
      return "Invalid time zone"
  async def bio(value, user=None):
    pass
  async def _validate(user, values): # values = object containing the field names as attributes and their contents as values
    pass # maybe we shouldn't pass here
  async def _execute(user, values):
    bytes_ = values.password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash_ = bcrypt.hashpw(bytes_, salt)
    cmd_line_handle = re.sub(r" ,\.\-", "_", values.handle)
    DirtyFork.cur_execute("SELECT cmd_line_handle from users WHERE cmd_line_handle LIKE ? ESCAPE '$' COLLATE NOCASE", (cmd_line_handle.replace("_", "$_")+"%",))
    results = [row[0].lower() for row in DirtyFork.cur]
    n = 1
    while True:
      if not cmd_line_handle.lower()+str(n) in results:
        break
      n += 1
    time_zone_hours, time_zone_mins = time_zones[values.time_zone.upper()]
    cmd_line_handle = cmd_line_handle+str(n)
    DirtyFork.cur.execute("""INSERT INTO users (handle,          cmd_line_handle, password_hash, password_salt, email,          sex,        age,         location,           bio,        time_created,     time_zone_letters, time_zone_hours, time_zone_mins) VALUES 
                                               (?,               ?,               ?              ?              ?               ?           ?            ?                   ?           ?,                ?,                 ?,               ?)""", 
                                               (values.handle,   cmd_line_handle, hash_,         salt,          values.email,   values.sex, values.age,  values.location,    values.bio, int(time.time()), values.time_zone,  time_zone_hours, time_zone_mins))
    return DirtyFork.RetVals(next_destination = DirtyFork.config.destinations.registered_destination) 
															
# values is an object with attributes because you have to know what attributes you're looking for when validating the data, whereas 
# r is a dict because it will be used in a generic/automated way by the BBS once it's passed back, so it will be using variables for keys.
