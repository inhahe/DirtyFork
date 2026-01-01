black, red, green, brown, blue, magenta, cyan, gray = range(8) 
yellow = brown
white = grey = gray
colors = {"black": black, "red": red, "green": green, "brown": brown, "blue": blue, "magenta": magenta, "cyan": cyan, "gray": gray, "grey": grey, "white": white, "yellow": yellow,
          black: black, red: red, green: green, brown: brown, blue: blue, magenta: magenta, cyan: cyan, gray: gray, grey: grey, white: white, yellow: yellow}

SyncTERM, PuTTy = 1, 2

success, fail, new_user = 1, 2, 3

cr, lf = "\x0d", "\x0a"

invalid = -1

class RetVals:
  def __init__(self, **kwargs):
    for k, v in kwargs.items():
      self.k = v

Eobj = RetVals

class Estr(str):
  def __new__(cls, content, **kwargs): 
    instance = super().__new__(cls, content)
    for k, v in kwargs.items():
      setattr(instance, k, v)
    return instance

class Eint(int):
  def __new__(cls, content, **kwargs): 
    instance = super().__new__(cls, content)
    for k, v in kwargs.items():
      setattr(instance, k, v)
    return instance

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

class Null:
    __slots__ = ()

    def __init__(self, exists=False):
        self.exists = exists

    def __getattr__(self, name):
        return self

    def __getitem__(self, key):
        return self

    def __bool__(self):
        return False

    def __repr__(self):
        return "null"

    def __str__(self):
        return "null"

    def __iter__(self):
        return range(0)

null = Null()
