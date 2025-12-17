black, red, green, brown, blue, magenta, cyan, gray = range(8) 
yellow = brown
white = gray
colors = {"black": black, "red": red, "green": green, "brown": brown, "blue": blue, "magenta": magenta, "cyan": cyan, "gray": gray, "white": white, "yellow": yellow}

SyncTERM, PuTTy = 1, 2

success, fail, new_user = 1, 2, 3

cr, lf = "\x0d", "\x0a"

class RetVals:
  def __init__(self, **kwargs):
    for k, v in kwargs.items():
      self.k = v

class Disconnected(Exception):
  def __init__(self, user):
    self.user = user

class Char: 
  def __init__(self, fg=7, bg=0, fg_br=False, bg_br=False, char=" "):
    self.fg = fg
    self.bg = bg
    self.fg_br = fg_br
    self.bg_br = bg_br
    self.char = char
