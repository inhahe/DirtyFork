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


# CP437 visible glyphs for byte values that Python's cp437 codec preserves
# as control characters (0x01-0x1F and 0x7F). Bytes outside this set are
# decoded normally by the codec.
_CP437_LOW_GLYPHS = {
  0x01: '\u263a', 0x02: '\u263b', 0x03: '\u2665', 0x04: '\u2666',
  0x05: '\u2663', 0x06: '\u2660', 0x07: '\u2022', 0x08: '\u25d8',
  0x09: '\u25cb', 0x0a: '\u25d9', 0x0b: '\u2642', 0x0c: '\u2640',
  0x0d: '\u266a', 0x0e: '\u266b', 0x0f: '\u263c', 0x10: '\u25ba',
  0x11: '\u25c4', 0x12: '\u2195', 0x13: '\u203c', 0x14: '\u00b6',
  0x15: '\u00a7', 0x16: '\u25ac', 0x17: '\u21a8', 0x18: '\u2191',
  0x19: '\u2193', 0x1a: '\u2192', 0x1b: '\u2190', 0x1c: '\u221f',
  0x1d: '\u2194', 0x1e: '\u25b2', 0x1f: '\u25bc', 0x7f: '\u2302',
}

def cp437_glyph(n):
  """Return the visible CP437 glyph for byte value n as a Unicode string.
  Bytes 0x01-0x1F and 0x7F are remapped to their IBM PC display glyphs
  (smiley, hearts, sun, arrows, house, etc.) instead of being preserved as
  control characters by Python's standard cp437 codec. All other bytes
  (including 0x00, 0x20-0x7E, and 0x80-0xFF) are decoded normally."""
  if n in _CP437_LOW_GLYPHS:
    return _CP437_LOW_GLYPHS[n]
  return bytes([n]).decode('cp437')


# Translation table for str.translate() that maps the CP437 control-byte
# code points (0x01-0x1F, 0x7F) to their visible Unicode glyphs, EXCLUDING
# ones that have real terminal control meaning a BBS relies on:
#   0x00 NUL, 0x07 BEL, 0x08 BS, 0x09 TAB, 0x0A LF, 0x0C FF, 0x0D CR, 0x1B ESC
# Used by send() when sending to a UTF-8 terminal, so writers can use the
# byte form (e.g. '\x0f') and have it appear as the visible glyph (☼).
_CP437_CONTROL_CODES_TO_PRESERVE = {0x00, 0x07, 0x08, 0x09, 0x0a, 0x0c, 0x0d, 0x1b}
CP437_LOW_TO_UTF8_TRANSLATION = {
  n: g for n, g in _CP437_LOW_GLYPHS.items()
  if n not in _CP437_CONTROL_CODES_TO_PRESERVE
}

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
