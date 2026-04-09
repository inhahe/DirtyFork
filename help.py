"""Help screen — shows available commands and navigation tips."""

from input_fields import show_message_box
from definitions import RetVals, success, null, white, black, cyan
from config import get_config

config = get_config()


HELP_TEXT = """\
NAVIGATION
  Type the first few letters of a menu option to select it.
  The highlighted prefix is the minimum needed, but you can
  type more letters for clarity.
  x         Exit current menu (go back)
  xx        Exit two levels, xxx three, etc.

DOTTED PATHS
  Type menu.option to jump directly into a submenu's option.
  Paths can go any number of levels deep:
    doors.lord          Open Legend of the Red Dragon
    forums.general      Open the General forum
  x.option  Exit current menu, then select from the parent.
  x.x.option  Exit two levels, then select.

SLASH COMMANDS (available from any menu)
  /jump <path>     Jump to any destination (shortcut: /j)
                   Example: /j forums.general
  /page <user> <msg>  Send a popup message to an online user
  /chat <user>     Start a one-on-one split-screen chat
  /info <user>     View a user's profile
  /quit            Log out (shortcut: /q)

TELECONFERENCE COMMANDS
  /join <channel>  Join or create a channel
  /list            List active channels
  /who             Who's in the current channel
  /msg <user> <txt>  Private message in teleconference
  /me <action>     Emote/action
  /topic <text>    Set channel topic
  /page <user>     Page a user elsewhere on the BBS
  /chat <user>     Start one-on-one chat
  /clear           Clear chat area
  /help            Show teleconference help
  /quit            Leave teleconference

ONE-ON-ONE CHAT
  Both users see each other typing in real time.
  Full editing: arrows, backspace, delete, home, end.
  Press ESC to exit the chat.

SETTINGS
  Change your profile, password, encoding, and preferences
  from the Settings menu option.
  Bio is edited via the "Edit Bio" button in Settings.

KEYBOARD
  Tab / Shift+Tab  Move between form fields
  Enter            Activate button or advance to next field
  Insert           Toggle insert/overwrite mode

MOUSE (terminals that support it)
  Click menu options, buttons, and form fields to select them.
  Click scrollbar arrows to scroll one line.
  Click or drag the scrollbar track to scroll to a position.
  Click [■] to close a popup.
"""


async def run(user, dest_conf, menu_item=None):
  from common import Destinations

  bbs_name = str(config.bbs_name) if config.bbs_name else "DirtyFork BBS"

  await show_message_box(user, HELP_TEXT, title=f"{bbs_name} Help",
                         fg=white, fg_br=True, bg=black,
                         outline_fg=cyan, outline_fg_br=True,
                         word_wrap=False)

  return RetVals(status=success, next_destination=Destinations.main)
