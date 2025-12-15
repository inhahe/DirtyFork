import sys, sqlite3
con = sqlite3.connect(sys.argv[1] if len(sys.argv)>1 else "DirtyFork.db")
cur = con.cursor()
# include phone number in users?
# home, work, mobile? any number of numbers they want to add?
# any number of emails? 
# various social media screen names?
cur.execute("""
CREATE TABLE IF NOT EXISTS USERS ( 
  id INTEGER PRIMARY KEY AUTOINCREMENT
  handle TEXT UNIQUE NOT NULL
  email TEXT
  password_hash TEXT
  password_salt TEXT
  sex TEXT
  age INTEGER
  location TEXT 
  bio TEXT
  time_created TEXT )
CREATE TABLE IF NOT EXISTS USER_KEYS (
  key TEXT 
  FOREIGN KEY (user_id) REFERENCES users(id) )
CREATE TABLE IF NOT EXISTS PRIVATE_MESSAGES 
  id INTEGER PRIMARY KEY AUTOINCREMENT
  message TEXT
  FOREIGN KEY (from_user) REFERENCES users(id)
  FOREIGN KEY (to_user) REFERENCES users(id) 
  FOREIGN KEY (reply_to) REFERENCE messages(id)
  time_created TEXT
  time_read TEXT )
CREATE TABLE IF NOT EXISTS FORUMS (
  id INTEGER PRIMARY KEY AUTOINCREMENT
  name TEXT )
CREATE TABLE IF NOT EXISTS FORUM_MESSAGES (
  message TEXT
  FOREIGN KEY (from_user) REFERENCES users(id)
  FOREIGN KEY (reply_to) REFERENCE messages(id)
  time_created TEXT )
CREATE TABLE IF NOT EXISTS FORUM_MESSAGES_READ (
  FOREIGN KEY (user_id) REFERENCES users(id)
  FOREIGN KEY (message_id) REFERENCE messages(id) 
  time_read TEXT )
""")