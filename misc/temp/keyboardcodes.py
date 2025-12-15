cr = b"\x0d" # are these right?
tab = b"\x09"
beep = b"\x07"
lf = b"\x0a"
ctrl_u = b"\x15" # clear line
ctrl_c = b"\x03"
back = b"\x08"
cls = b"\x0c"

special_keys = {
  "cr": b"\x0d",
  "tab": b"\x09",
  "beep": b"\x07",
  "lf": b"\x0a",
  "ctrl_u": b"\x15",
  "ctrl_c": b"\x03",
  "back": b"\x08",
  "cls": b"\x0c"
}

keyboard_codes = {
  b"\x1b[D": "left",
  b"\x1b[C": "right",
  b"\x1b[A": "up",
  b"\x1b[B": "down",
  b"\x1b[H": "home",
  b"\x1b[K": "end",
  b"\x1b[L": "ctrl_home",
  b"\x1b[M": "ctrl_pgup",
  b"\x1bOP": "f1",
  b"\x1bOQ": "f2",
  b"\x1bOw": "f3",
  b"\x1bOx": "f4",

  b"\x00\x4b": "left",
  b"\x00\x4d": "right",
  b"\x00\x48": "up",
  b"\x00\x50": "down",
  b"\x00\x47": "home",
  b"\x00\x4f": "end",
  b"\x00\x4b": "left",
  
  b"\x00\x77": "ctrl_home",
  b"\x00\x84": "ctrl_pgup",
  
  b"\x00\x3b": "f1",
  b"\x00\x3c": "f2",
  b"\x00\x3d": "f3",
  b"\x00\x3e": "f4",
  b"\x00\x3f": "f5",
  b"\x00\x40": "f6",
  b"\x00\x41": "f7",
  b"\x00\x42": "f8",
  b"\x00\x42": "f9",
  b"\x00\x44": "f10",

  b"\x00\x54": "shift_f1",
  b"\x00\x55": "shift_f2",
  b"\x00\x56": "shift_f3",
  b"\x00\x57": "shift_f4",
  b"\x00\x58": "shift_f5",
  b"\x00\x59": "shift_f6",
  b"\x00\x5a": "shift_f7",
  b"\x00\x5b": "shift_f8",
  b"\x00\x5c": "shift_f9",
  b"\x00\x5d": "shift_f10",
  
  b"\x00\x5e": "ctrl_f1",
  b"\x00\x5f": "ctrl_f2",
  b"\x00\x60": "ctrl_f3",
  b"\x00\x61": "ctrl_f4",
  b"\x00\x62": "ctrl_f5",
  b"\x00\x63": "ctrl_f6",
  b"\x00\x64": "ctrl_f7",
  b"\x00\x65": "ctrl_f8",
  b"\x00\x66": "ctrl_f9",
  b"\x00\x67": "ctrl_f10",

  b"\x00\x68": "alt_f1",
  b"\x00\x69": "alt_f2",
  b"\x00\x6a": "alt_f3",
  b"\x00\x6b": "alt_f4",
  b"\x00\x6c": "alt_f5",
  b"\x00\x6d": "alt_f6",
  b"\x00\x6e": "alt_f7",
  b"\x00\x6f": "alt_f8",
  b"\x00\x70": "alt_f9",
  b"\x00\x71": "alt_f10",

  b"\x00\x49": "pgup",
  b"\x00\x51": "pgdn",
  b"\x00\x52": "ins",

  b"\x00\x76": "ctrl_pgdn",
  b"\x00\x75": "ctrl_end",
  b"\x00\x73": "ctrl_left",
  b"\x00\x74": "ctrl_right",
  b"\x00\x0f": "shift_tab",
  
  b"\x08": "back",
  b"\x0d": "enter",
  b"\x09": "tab",
  b"\x7f": "del",
  b"\x1b[3~": "del"
}
