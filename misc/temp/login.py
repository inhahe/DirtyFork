class login:
  async def handle(value, user=None):
    data.cur.execute("SELECT * FROM users WHERE handle = ? LIMIT 1 COLLATE NOCASE, (to_str(value),))
    if not data.cur.fetchone()
      return "Unregistered handle"
  async def password(value, user=None)
    data.cur.execute("SELECT * FROM users WHERE handle = ? LIMIT 1 COLLATE NOCASE", (to_str(user.cur_destination.inputs.handle.contents),))
    user_in_db = data.cur.fetchone()
    if not user_in_db: 
      return "Unregistered handle"
    if not user_in_db["password_hash"] == bcrypt.hashpw(value, user_in_db["password_salt"]):
      return "Invalid password" 
  async def _submit(user, values): 
    pass # values = object containing the field names as attributes and their contents as values
    # pass even if it's wrong so that the bbs will run _execute and we can pass the user onto the fail screen. wouldn't 
    # be right to lead them to believe they can keep submitting when they have 3 or so login attempts.
  async def _execute(user, values):
    return RetVals(    
 oh, i just realized this way isn't feasible at all. 
 because the user could try as many handles and passwords as they want just by flipping between inputs and seeing if they show errors

	