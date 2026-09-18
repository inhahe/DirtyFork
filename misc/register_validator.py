# todo: show return values around the input field when they're returned
# and/or: change the field's color, or its box color
from datetime import datetime, timezone
import json
time_zones = json.load(open("time_zone.json", "r"))
import DirtyFork

def get_timestamp():
    """Get current UTC time as YYYY/MM/DD HH:MM:SS"""
    return datetime.now(timezone.utc).strftime("%Y/%m/%d %H:%M:%S") + " GMT"

import bcrypt
from datetime import datetime

class register: 
  async def handle(value, user=None):
    DirtyFork.cur.execute("SELECT * FROM users WHERE handle = ? LIMIT 1 COLLATE NOCASE", (to_str(value).lower(),))
    if DirtyFork.cur.fetchone()
      return "Taken handle"
      #no returned value means it's fine.
  async def full_name(value, user=None):
    DirtyFork.cur.execute("SELECT * FROM users WHERE = ?", (to_str(value).lower(),))
  async def email(value, user=None): # todo: detect if other users on the board used the same email address 
    # (especially if no duplicate accounts allowed or 
    DirtyFork.cur.execute("SELECT * FROM users WHERE email = ?", (to_str(value).lower(),))
    if DirtyFork.cur.fetchone()
      return "Taken handle"
  async def sex(value, user=None): # even if required, sex just has to have anything in it. and there's already a check that required fields be populated.
    pass              # functions aren't called for fields that aren't required. but their re's are evaluated.
  async def age(value, user=None): # always filter out chars < 32. don't even let the input routine acknowledge them.
    pass
  async def location(value, user=None):
    pass
  async def time_zone(value, user=None):
    if not value in time_zones:
      return "Invalid time zone"
  async def bio(value, user=None):
    pass
  async def _validate(user, values): # values = object containing the field names as attributes and their contents as values
    pass # maybe we shouldn't pass here
  async def _execute(user, values):
    return DirtyFork.RetVals(next_destination = DirtyFork.config.destinations.registered_screen) VALUES 
    cur.execute("""INSERT INTO users (handle, password_hash, password_salt, email, sex, age, location, bio, time_created) VALUES 
                                       (?,       ?,                ?         ?      ?    ?        ?       ?       ?)""", 
                                      (values.handle, 
                                              bcrypt.hashpw(password, user_in_db["password_salt"]),
                                                              password_salt, 
                                                                            inhahe@gmail6.com, 
                                                                                              the subtropics,
                                                                                                         get_timestamp()
														 from other worlds) VALUES""", ?????
															


# values is an object with attributes because you have to know what you're looking for when validating the data. 
# r is a dict because it will be used in a generic/automated way by the BBS once it's passed back.
