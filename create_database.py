import sys, sqlite3
con = sqlite3.connect(sys.argv[1] if len(sys.argv)>1 else "DirtyFork.db")
cur = con.cursor()
# include phone number in users?
# home, work, mobile? any number of numbers they want to add?
# any number of emails?
# various social media screen names?
cur.execute("""
CREATE TABLE IF NOT EXISTS USERS (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  handle TEXT UNIQUE NOT NULL,
  cmd_line_handle TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  password_salt TEXT NOT NULL,
  time_created INT )
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS USER_KEYS (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INT NOT NULL,
  key TEXT,
  FOREIGN KEY (user_id) REFERENCES users(id) )
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS PRIVATE_MESSAGES (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  from_user INT NOT NULL,
  to_user INT NOT NULL,
  reply_to INT,
  subject TEXT,
  message TEXT,
  time_created INT,
  time_read INT,
  FOREIGN KEY (from_user) REFERENCES users(id),
  FOREIGN KEY (to_user) REFERENCES users(id),
  FOREIGN KEY (reply_to) REFERENCES private_messages(id) )
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS FORUMS (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT )
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS FORUM_MESSAGES (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  from_user INT NOT NULL,
  reply_to INT,
  forum INT NOT NULL,
  subject TEXT,
  message TEXT,
  time_created INT,
  FOREIGN KEY (from_user) REFERENCES users(id),
  FOREIGN KEY (reply_to) REFERENCES forum_messages(id),
  FOREIGN KEY (forum) REFERENCES forums(id) )
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS FORUM_MESSAGES_READ (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INT NOT NULL,
  message_id INT NOT NULL,
  time_read INT,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (message_id) REFERENCES forum_messages(id) )
""")
cur.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS idx_fmr_user_msg
  ON FORUM_MESSAGES_READ (user_id, message_id)
""")
con.commit()
con.close()
