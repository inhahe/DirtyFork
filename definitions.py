black, red, green, brown, blue, magenta, cyan, gray = range(8) 
yellow = brown
white = grey = gray
colors = {"black": black, "red": red, "green": green, "brown": brown, "blue": blue, "magenta": magenta, "cyan": cyan, "gray": gray, "grey": grey, "white": white, "yellow": yellow,
          black: black, red: red, green: green, brown: brown, blue: blue, magenta: magenta, cyan: cyan, gray: gray, grey: grey, white: white, yellow: yellow}

SyncTERM, PuTTy = 1, 2

success, fail, new_user = 1, 2, 3
cr, lf = "\x0d", "\x0a"
after, invalid, margin_cell = -1, -2, -3
submit = -1
top, before_cur, cur = 1, 2, 3

class RetVals:
  def __init__(self, **kwargs):
    for k, v in kwargs.items():
      setattr(self, k, v)

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
  def __init__(self, user=None):
    self.user = user

class Char: 
  def __init__(self, char=" ", fg=7, fg_br=False, bg=0, bg_br=False):
    self.fg = fg
    self.bg = bg
    self.fg_br = fg_br
    self.bg_br = bg_br
    self.char = char

class Null:
    __slots__ = ()

    def __init__(self):
        pass

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
        return iter(())

    def __contains__(self, item):
        return False

    def __len__(self):
        return 0

    def __call__(self, *args, **kwargs):
        return self

null = Null()
