import re, asyncio

from definitions import *

cr = "\x0d" # are these right?
tab = "\x09"
beep = "\x07"
lf = "\x0a"
ctrl_u = "\x15" # clear line
ctrl_c = "\x03"
back = "\x08"
cls = "\x0c"

special_keys = {
  "cr": "\x0d",
  "ta": "\x09",
  "beep": "\x07",
  "lf": "\x0a",
  "ctrl_u": "\x15",
  "ctrl_c": "\x03",
  "back": "\x08",
  "cls": "\x0c"
}

left, right, up, down, home, end, ctrl_home, ctrl_pgup, \
f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, \
shift_f1, shift_f2, shift_f3, shift_f4, shift_f5, shift_f6, shift_f7, shift_f8, shift_f9, shift_f10, \
ctrl_f1, ctrl_f2, ctrl_f3, ctrl_f4, ctrl_f5, ctrl_f6, ctrl_f7, ctrl_f8, ctrl_f9, ctrl_f10, \
alt_f1, alt_f2, alt_f3, alt_f4, alt_f5, alt_f6, alt_f7, alt_f8, alt_f9, alt_f10, \
pgup, pgdn, insert, ctrl_pgdn, ctrl_end, ctrl_left, ctrl_right, shift_tab, delete, \
click, position, middle, release, partial_code = range(1, 63)

keyboard_codes = {
  "\x1b[D": left,
  "\x1b[C": right,
  "\x1b[A": up,
  "\x1b[B": down,
  "\x1b[H": home,
  "\x1b[K": end,
  "\x1b[L": ctrl_home,
  "\x1b[M": ctrl_pgup,
  "\x1bOP": f1,
  "\x1bOQ": f2,
  "\x1bOw": f3,
  "\x1bOx": f4,

  "\x00\x4b": left,
  "\x00\x4d": right,
  "\x00\x48": up,
  "\x00\x50": down,
  "\x00\x47": home,
  "\x00\x4f": end,

  "\x00\x77": ctrl_home,
  "\x00\x84": ctrl_pgup,
  
  "\x00\x3b": f1,
  "\x00\x3c": f2,
  "\x00\x3d": f3,
  "\x00\x3e": f4,
  "\x00\x3f": f5,
  "\x00\x40": f6,
  "\x00\x41": f7,
  "\x00\x42": f8,
  "\x00\x43": f9,
  "\x00\x44": f10,

  "\x00\x54": shift_f1,
  "\x00\x55": shift_f2,
  "\x00\x56": shift_f3,
  "\x00\x57": shift_f4,
  "\x00\x58": shift_f5,
  "\x00\x59": shift_f6,
  "\x00\x5a": shift_f7,
  "\x00\x5b": shift_f8,
  "\x00\x5c": shift_f9,
  "\x00\x5d": shift_f10,
  
  "\x00\x5e": ctrl_f1,
  "\x00\x5f": ctrl_f2,
  "\x00\x60": ctrl_f3,
  "\x00\x61": ctrl_f4,
  "\x00\x62": ctrl_f5,
  "\x00\x63": ctrl_f6,
  "\x00\x64": ctrl_f7,
  "\x00\x65": ctrl_f8,
  "\x00\x66": ctrl_f9,
  "\x00\x67": ctrl_f10,

  "\x00\x68": alt_f1,
  "\x00\x69": alt_f2,
  "\x00\x6a": alt_f3,
  "\x00\x6b": alt_f4,
  "\x00\x6c": alt_f5,
  "\x00\x6d": alt_f6,
  "\x00\x6e": alt_f7,
  "\x00\x6f": alt_f8,
  "\x00\x70": alt_f9,
  "\x00\x71": alt_f10,

  "\x00\x49": pgup,
  "\x00\x51": pgdn,
  "\x00\x52": insert,

  "\x00\x76": ctrl_pgdn,
  "\x00\x75": ctrl_end,
  "\x00\x73": ctrl_left,
  "\x00\x74": ctrl_right,
  "\x00\x0f": shift_tab,
  
  "\x08": back,
  "\x0d": cr,
  "\x0a": lf,
  "\x09": tab,
  "\x7f": delete,
  "\x07": beep,
  "\x03": ctrl_c,
  "\x1b[3~": delete,
  "\x0c": cls
}

# "\x15": "ctrl_u" # delete from cursor to start of line / clear the entire input buffer on BBSs
# "\x0": "ctrl_k" # delete from cursor to end of line
# "\x17": "ctrl_w" # delete word before cursor
# "\x04": "ctrl_d" # end of input / logout
# "\x01": "ctrl_a" # move to start of line
# "\x05": "ctrl_e" # move to end of line

partial_R = re.compile("\x1b(?:\\[(?:[1-9](?:\\d{0,2}(?:;(?:[1-9](?:\\d{0,2}(?:R)?)?)?)?)?)?)?")
R = re.compile("\x1b\\[([1-9]\\d{0,3});([1-9]\\d{0,2})R")

partial_M = re.compile("\x1b(?:\\[(?:M(?:[ -\xff](?:[ -\xff](?:[ -\xff])?)?)?)?)?")
M = re.compile("\x1b\\[M[ -\xff][ -\xff][ -\xff]")

# takes a long time...

# i think the clicks are about 4.1 million entries, the codestart entries for it would be about 20,000,000
# codestart entries for positions would be about 10,000,000.

# for row in range(1, 1000):
#   for col in range(1, 1000):
#     keyboard_codes[f"\x1b[{row};{col}R"] = Key("position", row=row, col=col)

# for button_n, button in enumerate(("left", "middle", "right", "release")):
#   for shift in (False, True):
#     for alt in (False, True):
#       for ctrl in (False, True):
#         for wheel_n, wheel in enumerate((None, "up", "down")):
#           for row in range(1, 256-32):
#             for col in range(1, 256-32): 
#               char1 = chr(32+button_n+(shift<<2)+(alt<<3)+(ctrl<<4)+(wheel_n<<6))
#               char2 = chr(row+32)
#               char3 = chr(col+32)
#               keyboard_codes["\x1b"+char1+char2+char3] = Key("click", button=button, shift=shift, alt=alt, ctrl=ctrl, wheel=wheel)

keyboard_code_starts = {}
for code, key in keyboard_codes.items():
  s = ""
  for s2 in code[:-1]:
    s+=s2
    keyboard_code_starts[s] = partial_code

keyboard_codes.update(keyboard_code_starts)
del keyboard_code_starts

def check_partial(k):
  return k in keyboard_codes or partial_R.fullmatch(k) or partial_M.fullmatch(k)

def check(k):
  # Check for complete mouse sequence first (takes priority over ESC[M = ctrl_pgup)
  r = M.fullmatch(k)
  if r:
    Cb = ord(r.group(0)[3])-32
    return Eint(click, button=[left, middle, right, release][Cb & 3],
                shift=bool(Cb & 4), alt=bool(Cb & 8), ctrl=bool(Cb & 16),
                wheel=[None, up, down, None][(Cb >> 6) & 3],
                col=ord(r.group(0)[4])-32, row=ord(r.group(0)[5])-32)
  # If this is ESC[M, treat it as partial — could be start of a mouse sequence
  if k == "\x1b[M":
    return False
  r = keyboard_codes.get(k, False)
  if r and not r==partial_code:
    return r
  r = R.fullmatch(k)
  if r:
    return Eint(position, row=int(r.group(1)), col=int(r.group(2)))
  
