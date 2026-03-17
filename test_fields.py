"""
Test harness for InputField/InputFields.
Creates a mock user and lets you inspect field state after operations.

Usage: python test_fields.py
"""

import asyncio, sys, io
sys.argv = ['DirtyFork.py', 'DirtyFork.yaml']

from config import get_config
config = get_config(path='DirtyFork.yaml', main=True)

from definitions import *
from input_fields import InputField, InputFields, Block, Line
from input_output import ansi_move, ansi_color, send


class MockWriter:
  """Captures all output without sending to a real terminal."""
  def __init__(self):
    self.buffer = []
  def write(self, data):
    self.buffer.append(data)
  async def drain(self):
    pass
  def get_output(self):
    return "".join(self.buffer)
  def clear(self):
    self.buffer = []


class MockReader:
  """Feeds pre-programmed keys."""
  def __init__(self, keys=None):
    self.keys = list(keys or [])
    self.pos = 0
  async def read(self, n):
    if self.pos < len(self.keys):
      k = self.keys[self.pos]
      self.pos += 1
      return k
    raise Exception("No more keys")


def make_mock_user(width=80, height=24):
  """Create a mock User object for testing."""
  user = type('MockUser', (), {})()
  user.writer = MockWriter()
  user.reader = MockReader()
  user.screen_width = width
  user.screen_height = height
  user.screen = [[Char() for c in range(width)] for r in range(height)]
  user.click_screen = [[None] * width for r in range(height)]
  user.cur_row = user.new_row = 1
  user.cur_col = user.new_col = 1
  user.cur_fg = user.new_fg = white
  user.cur_bg = user.new_bg = black
  user.cur_fg_br = user.new_fg_br = False
  user.cur_bg_br = user.new_bg_br = False
  user.cur_wrap = True
  user.cur_show_cursor = True
  user.scroll_region_top = None
  user.scroll_region_bottom = None
  user.scroll_region_strict = False
  user.terminal = SyncTERM
  user.encoding = 'cp437'
  user.ttype = 'test'
  user.in_door = False
  user.popup_event = None
  user.input_timestamps = []
  user.batch_mode = False
  user.cur_input_code = ""
  user.conf = null
  user.handle = "TestUser"
  user.keys = set()
  return user


def inspect_field(field, label=""):
  """Print field state for debugging."""
  print(f"\n{'='*60}")
  if label:
    print(f"  {label}")
  print(f"  row_offset={field.row_offset} col_offset={field.col_offset}")
  print(f"  width={field.width} height={field.height}")
  print(f"  row={field.row} col={field.col}")
  print(f"  scroll_offset={field.scroll_offset} cursor_line={field.cursor_line} cursor_col={field.cursor_col}")
  print(f"  outline={field.outline} allow_edit={field.allow_edit} no_cursor_margin={field.no_cursor_margin}")
  print(f"  lines ({len(field.lines)}):")
  for i, line in enumerate(field.lines):
    marker = " <-- cursor" if i == field.cursor_line else ""
    print(f"    [{i}] level={line.level} {repr(line.text)}{marker}")
  print(f"  display_rows ({len(field.display_rows)}):")
  for i, dr in enumerate(field.display_rows):
    print(f"    [{i}] line={dr.line_index} [{dr.start_col}:{dr.end_col}] prefix={repr(dr.margin_prefix)}")
  print(f"  screen rows: {field.row_offset} to {field.row_offset + field.height - 1}")
  sr, sc = field._cursor_to_screen()
  print(f"  cursor screen pos: row={sr} col={sc}")
  print(f"{'='*60}")


def inspect_form(form, label=""):
  """Print InputFields container state."""
  print(f"\n{'#'*60}")
  if label:
    print(f"  {label}")
  print(f"  {len(form.fields)} fields, {len(form._buttons)} buttons")
  for i, f in enumerate(form.fields):
    print(f"  Field {i}: row_offset={f.row_offset} col_offset={f.col_offset} "
          f"w={f.width} h={f.height} outline={f.outline} edit={f.allow_edit}")
  for i, (name, b) in enumerate(form._buttons):
    print(f"  Button '{name}': row_offset={b.row_offset} col_offset={b.col_offset} "
          f"w={b.width} h={b.height} outline={b.outline}")
  print(f"{'#'*60}")


async def test_basic_field():
  """Test that a basic field positions correctly."""
  user = make_mock_user()
  user.cur_row = user.new_row = 5
  user.cur_col = user.new_col = 10

  field = await InputField.create(
    parent=type('FakeParent', (), {'user': user})(),
    user=user,
    conf=config.input_fields.input_field,
    width=20,
    height=5,
    max_length=100,
  )

  inspect_field(field, "Basic field at row=5 col=10, 20x5")

  # Verify bounds
  assert field.row_offset == 5, f"Expected row_offset=5, got {field.row_offset}"
  assert field.col_offset == 10, f"Expected col_offset=10, got {field.col_offset}"
  assert field.width == 20
  assert field.height == 5
  assert field.row == 0
  assert field.col == 0
  print("  PASS: Basic field positioning")


async def test_field_with_outline():
  """Test that outline offsets row/col correctly."""
  user = make_mock_user()
  user.cur_row = user.new_row = 5
  user.cur_col = user.new_col = 10

  field = await InputField.create(
    parent=type('FakeParent', (), {'user': user})(),
    user=user,
    conf=config.input_fields.input_box,  # has outline
    width=20,
    height=5,
    max_length=100,
  )

  inspect_field(field, "Field with outline at row=5 col=10, 20x5")

  # Outline should offset by +1
  assert field.row_offset == 6, f"Expected row_offset=6 (5+1 for outline), got {field.row_offset}"
  assert field.col_offset == 11, f"Expected col_offset=11 (10+1 for outline), got {field.col_offset}"
  # Screen usage: outline top at 5, content 6-10, outline bottom at 11
  print(f"  Outline top row: {field.row_offset - 1}")
  print(f"  Content rows: {field.row_offset} to {field.row_offset + field.height - 1}")
  print(f"  Outline bottom row: {field.row_offset + field.height}")
  print("  PASS: Outline field positioning")


async def test_button():
  """Test button with no_cursor_margin."""
  user = make_mock_user()
  user.cur_row = user.new_row = 20
  user.cur_col = user.new_col = 5

  form = InputFields(user)
  btn = await form.add_button("test", content="Click Me")

  inspect_field(btn, "Button 'Click Me'")

  # no_cursor_margin should be True, width should be len("Click Me") = 8
  assert btn.no_cursor_margin == True, f"Expected no_cursor_margin=True, got {btn.no_cursor_margin}"
  assert btn.width == 8, f"Expected width=8, got {btn.width}"
  assert btn.allow_edit == False
  print("  PASS: Button sizing")


async def test_form_layout():
  """Test a form with fields and buttons, check no overlaps."""
  user = make_mock_user()
  user.cur_row = user.new_row = 3
  user.cur_col = user.new_col = 1

  form = InputFields(user)

  # Field 1: single line
  await send(user, "Label1: ", drain=False)
  f1 = await form.add_field(
    conf=config.input_fields.input_field,
    width=20, max_length=50,
  )
  await send(user, "\r\n", drain=False)

  # Field 2: single line
  await send(user, "Label2: ", drain=False)
  f2 = await form.add_field(
    conf=config.input_fields.input_field,
    width=20, max_length=50,
  )
  await send(user, "\r\n", drain=False)

  # Field 3: multi-line
  f3 = await form.add_field(
    conf=config.input_fields.input_field,
    width=40, max_length=1000,
    height=5, word_wrap=True, fill=" ",
  )
  await send(user, "\r\n", drain=False)

  # Button
  btn = await form.add_button("submit", content="Submit")

  inspect_form(form, "Form with 3 fields + button")

  # Check no overlapping screen rows
  ranges = []
  for i, f in enumerate(form.fields):
    top = f.row_offset - (1 if f.outline else 0)
    bot = f.row_offset + f.height - 1 + (1 if f.outline else 0)
    ranges.append((f"field{i}", top, bot))
  for name, b in form._buttons:
    top = b.row_offset - (1 if b.outline else 0)
    bot = b.row_offset + b.height - 1 + (1 if b.outline else 0)
    ranges.append((name, top, bot))

  print("\n  Screen row usage:")
  for name, top, bot in ranges:
    print(f"    {name}: rows {top}-{bot}")

  # Check for overlaps
  for i in range(len(ranges)):
    for j in range(i+1, len(ranges)):
      n1, t1, b1 = ranges[i]
      n2, t2, b2 = ranges[j]
      if t1 <= b2 and t2 <= b1:
        print(f"  WARNING: {n1} (rows {t1}-{b1}) overlaps with {n2} (rows {t2}-{b2})")

  # Check nothing exceeds screen
  for name, top, bot in ranges:
    if bot > user.screen_height:
      print(f"  ERROR: {name} bottom row {bot} exceeds screen height {user.screen_height}")
    if top < 1:
      print(f"  ERROR: {name} top row {top} is above screen")

  print("  PASS: Form layout")


async def test_message_compose_layout():
  """Simulate the message compose layout exactly."""
  user = make_mock_user(width=80, height=24)
  user.cur_row = user.new_row = 1
  user.cur_col = user.new_col = 1

  form = InputFields(user)

  # Title row 1-2
  await send(user, "Compose Message\r\n\r\n", drain=False)

  # To field at row 3
  await send(user, "    To: ", drain=False)
  to_field = await form.add_field(conf=config.input_fields.input_field, width=30, max_length=30)
  await send(user, "\r\n", drain=False)

  # Subject field at row 4
  await send(user, "  Subj: ", drain=False)
  subj_field = await form.add_field(conf=config.input_fields.input_field, width=70, max_length=200)
  await send(user, "\r\n", drain=False)

  # Divider at row 5
  await send(user, "-" * 80 + "\r\n", drain=False)

  # Editor
  editor_top = user.cur_row
  editor_height = user.screen_height - editor_top - 4
  print(f"  editor_top={editor_top} editor_height={editor_height}")

  editor_field = await form.add_field(
    conf=config.input_fields.input_field,
    width=80, height=editor_height, max_length=10000,
    word_wrap=True, fill=" ",
  )

  # Divider
  divider_row = editor_top + editor_height
  await ansi_move(user, row=divider_row, col=1, drain=False)
  await send(user, "-" * 80, drain=False)

  # Buttons
  button_row = divider_row + 1
  await ansi_move(user, row=button_row, col=2, drain=True)
  await form.add_button("send", content=" Send ")
  send_btn = form._buttons[-1][1]
  abort_col = send_btn.col_offset + send_btn.width + (1 if send_btn.outline else 0) + 1
  abort_row = send_btn.row_offset - (1 if send_btn.outline else 0)
  await ansi_move(user, row=abort_row, col=abort_col, drain=True)
  await form.add_button("cancel", content=" Cancel ")

  inspect_form(form, "Message compose layout")

  # Check all ranges
  ranges = []
  for i, f in enumerate(form.fields):
    top = f.row_offset - (1 if f.outline else 0)
    bot = f.row_offset + f.height - 1 + (1 if f.outline else 0)
    ranges.append((f"field{i}({['to','subj','editor'][i] if i<3 else '?'})", top, bot))
  for name, b in form._buttons:
    top = b.row_offset - (1 if b.outline else 0)
    bot = b.row_offset + b.height - 1 + (1 if b.outline else 0)
    ranges.append((f"btn({name})", top, bot))

  print(f"\n  Divider at row {divider_row}")
  print(f"  Screen row usage:")
  for name, top, bot in ranges:
    overlap_divider = top <= divider_row <= bot
    print(f"    {name}: rows {top}-{bot}" + (" *** OVERLAPS DIVIDER ***" if overlap_divider else ""))

  for i in range(len(ranges)):
    for j in range(i+1, len(ranges)):
      n1, t1, b1 = ranges[i]
      n2, t2, b2 = ranges[j]
      if t1 <= b2 and t2 <= b1:
        print(f"  WARNING: {n1} (rows {t1}-{b1}) overlaps with {n2} (rows {t2}-{b2})")

  for name, top, bot in ranges:
    if bot > user.screen_height:
      print(f"  ERROR: {name} bottom row {bot} exceeds screen height {user.screen_height}")

  print("  DONE: Message compose layout test")


async def test_ansi_move_and_send():
  """Test that ansi_move and send keep cur_row/cur_col in sync."""
  from input_output import ansi_move, ansi_move_2, ansi_color, send, ansi_cls

  user = make_mock_user()
  print("\n--- ansi_move + send tests ---")

  # Test 1: initial state
  assert user.cur_row == 1 and user.cur_col == 1, f"Initial state wrong: {user.cur_row},{user.cur_col}"
  assert user.new_row == 1 and user.new_col == 1
  print("  PASS: initial state (1,1)")

  # Test 2: ansi_move stages but doesn't update cur
  await ansi_move(user, row=5, col=10)
  assert user.new_row == 5 and user.new_col == 10, f"new_ not staged: {user.new_row},{user.new_col}"
  assert user.cur_row == 1 and user.cur_col == 1, f"cur_ changed without drain: {user.cur_row},{user.cur_col}"
  print("  PASS: ansi_move stages new_ without changing cur_")

  # Test 3: ansi_move with drain updates cur
  await ansi_move(user, row=5, col=10, drain=True)
  assert user.cur_row == 5 and user.cur_col == 10, f"cur_ not updated after drain: {user.cur_row},{user.cur_col}"
  assert user.new_row == 5 and user.new_col == 10
  print("  PASS: ansi_move with drain updates cur_")

  # Test 4: send updates cur_col
  user.writer.clear()
  await send(user, "hello", drain=False)
  assert user.cur_col == 15, f"After 'hello' at col 10, expected cur_col=15, got {user.cur_col}"
  assert user.cur_row == 5, f"Row should not change, got {user.cur_row}"
  assert user.new_col == 15, f"new_col should sync to 15, got {user.new_col}"
  print("  PASS: send('hello') advances cur_col by 5")

  # Test 5: send syncs new_ to cur_ so next send doesn't reposition
  await ansi_move(user, row=5, col=20)  # stage new position
  await send(user, "X", drain=False)  # should move to 20, write X, cur_col=21
  assert user.cur_col == 21, f"Expected cur_col=21 after move+send, got {user.cur_col}"
  assert user.new_col == 21, f"Expected new_col=21 after sync, got {user.new_col}"
  print("  PASS: send after ansi_move positions correctly and syncs")

  # Test 6: cr+lf in send
  await ansi_move(user, row=5, col=10, drain=True)
  await send(user, "\r\n", drain=False)
  assert user.cur_col == 1, f"After CR, expected cur_col=1, got {user.cur_col}"
  assert user.cur_row == 6, f"After LF, expected cur_row=6, got {user.cur_row}"
  assert user.new_row == 6 and user.new_col == 1, f"new_ not synced: {user.new_row},{user.new_col}"
  print("  PASS: send('cr+lf') moves to col 1 and row+1")

  # Test 7: multiple cr+lf
  await ansi_move(user, row=1, col=1, drain=True)
  await send(user, "line1\r\nline2\r\nline3", drain=False)
  assert user.cur_row == 3, f"After 3 lines, expected row 3, got {user.cur_row}"
  assert user.cur_col == 6, f"After 'line3' (5 chars) from col 1, expected col 6, got {user.cur_col}"
  print("  PASS: multi-line send tracks correctly")

  # Test 8: ansi_move to same position doesn't send anything
  user.writer.clear()
  await ansi_move(user, row=user.cur_row, col=user.cur_col, drain=True)
  output = user.writer.get_output()
  assert output == "", f"Expected no output for same-position move, got {repr(output)}"
  print("  PASS: ansi_move to same position sends nothing")

  # Test 9: send("", drain=True) flushes pending move
  await ansi_move(user, row=10, col=20)  # stage
  user.writer.clear()
  await send(user, "", drain=True)
  assert user.cur_row == 10 and user.cur_col == 20, f"Empty send should flush move: {user.cur_row},{user.cur_col}"
  output = user.writer.get_output()
  assert "\x1b[" in output, f"Expected ANSI move in output, got {repr(output)}"
  print("  PASS: send('', drain=True) flushes pending move")

  # Test 10: ansi_cls resets everything
  await ansi_cls(user)
  assert user.cur_row == 1 and user.cur_col == 1, f"After cls, expected (1,1), got ({user.cur_row},{user.cur_col})"
  assert user.new_row == 1 and user.new_col == 1
  print("  PASS: ansi_cls resets to (1,1)")

  # Test 11: send at end of screen width wraps
  user.screen_width = 80
  await ansi_move(user, row=1, col=78, drain=True)
  await send(user, "ABC", drain=False)
  # At col 78, write A(78), B(79), C(80). At col 80 = screen_width, should wrap
  assert user.cur_row == 2, f"Expected wrap to row 2, got row {user.cur_row}"
  assert user.cur_col == 1, f"Expected wrap to col 1, got col {user.cur_col}"
  print("  PASS: send wraps at screen width")

  # Test 12: consecutive sends without ansi_move between them
  await ansi_cls(user)
  await send(user, "first", drain=False)
  assert user.cur_col == 6, f"After 'first', expected col 6, got {user.cur_col}"
  await send(user, "second", drain=False)
  assert user.cur_col == 12, f"After 'second', expected col 12, got {user.cur_col}"
  # The second send should NOT reposition — new_col was synced to cur_col by first send
  print("  PASS: consecutive sends don't reposition backward")

  print("  ALL ansi_move/send tests passed")


async def test_draw_field_cursor_position():
  """Test that draw_field positions cursor correctly for full-width multi-line field."""
  from input_output import ansi_move, send, ansi_cls

  user = make_mock_user(width=80, height=24)
  await ansi_cls(user)

  # Position for field
  await ansi_move(user, row=6, col=1, drain=True)

  form = InputFields(user)
  editor = await form.add_field(
    conf=config.input_fields.input_field,
    width=80, height=14, max_length=10000,
    word_wrap=True, fill=" ",
    fill_fg=white, fill_fg_br=False, fill_bg=black, fill_bg_br=False,
  )

  print(f"\n--- draw_field cursor position test ---")
  print(f"  editor: row_offset={editor.row_offset} height={editor.height} width={editor.width}")
  print(f"  editor rows: {editor.row_offset} to {editor.row_offset + editor.height - 1}")

  # Draw the field
  await editor.draw_field()
  sr, sc = editor._cursor_to_screen()
  print(f"  After draw_field: cur_row={user.cur_row} cur_col={user.cur_col}")
  print(f"  After draw_field: new_row={user.new_row} new_col={user.new_col}")
  print(f"  Expected cursor: screen row={sr} col={sc}")

  assert user.cur_row == sr, f"Cursor row {user.cur_row} != expected {sr}"
  assert user.cur_col == sc, f"Cursor col {user.cur_col} != expected {sc}"
  print(f"  PASS: cursor at correct position after draw_field")

  # Simulate cursor at end of editor (add lines to fill it)
  for i in range(13):
    editor.lines.append(Line("", 0))
  editor.cursor_line = 13
  editor.cursor_col = 0
  editor._compute_display_rows()
  editor._ensure_cursor_visible()
  await editor.draw_field()
  sr, sc = editor._cursor_to_screen()
  print(f"  After draw_field with cursor at line 13: cur_row={user.cur_row}")
  assert user.cur_row == sr, f"Cursor row {user.cur_row} != expected {sr}"
  print(f"  PASS: cursor at correct row after scrolling")


async def test_char_insert():
  """Test inserting characters updates lines and cursor correctly."""
  user = make_mock_user(width=80, height=24)
  user.cur_row = user.new_row = 5
  user.cur_col = user.new_col = 1

  field = await InputField.create(
    parent=type('FakeParent', (), {'user': user})(),
    user=user, width=40, height=5, max_length=100, word_wrap=True,
  )

  print("\n--- char insert tests ---")

  # Type "hello"
  for ch in "hello":
    await field._handle_char(ch)
  assert field.lines[0].text == "hello", f"Expected 'hello', got {repr(field.lines[0].text)}"
  assert field.cursor_col == 5, f"Expected cursor_col=5, got {field.cursor_col}"
  print("  PASS: typing 'hello' inserts correctly")

  # Cursor should be at screen position row_offset, col_offset+5
  sr, sc = field._cursor_to_screen()
  assert sr == 5, f"Expected screen row 5, got {sr}"
  assert sc == 6, f"Expected screen col 6 (col_offset=1 + 5), got {sc}"
  print("  PASS: cursor screen position after typing")


async def test_enter_split():
  """Test Enter splits line correctly."""
  user = make_mock_user(width=80, height=24)
  user.cur_row = user.new_row = 5
  user.cur_col = user.new_col = 1

  field = await InputField.create(
    parent=type('FakeParent', (), {'user': user})(),
    user=user, width=40, height=10, max_length=1000, word_wrap=True,
  )

  # Type "hello world", then move cursor to col 5 ("hello|world"), press Enter
  for ch in "hello world":
    await field._handle_char(ch)
  field.cursor_col = 5
  await field._handle_enter()

  assert len(field.lines) == 2, f"Expected 2 lines, got {len(field.lines)}"
  assert field.lines[0].text == "hello", f"Line 0: expected 'hello', got {repr(field.lines[0].text)}"
  assert field.lines[1].text == " world", f"Line 1: expected ' world', got {repr(field.lines[1].text)}"
  assert field.cursor_line == 1, f"Expected cursor on line 1, got {field.cursor_line}"
  assert field.cursor_col == 0, f"Expected cursor_col=0, got {field.cursor_col}"
  print("  PASS: Enter splits line at cursor")


async def test_backspace():
  """Test backspace deletes character and joins lines."""
  user = make_mock_user(width=80, height=24)
  user.cur_row = user.new_row = 5
  user.cur_col = user.new_col = 1

  field = await InputField.create(
    parent=type('FakeParent', (), {'user': user})(),
    user=user, width=40, height=10, max_length=1000, word_wrap=True,
  )

  # Type "abc", backspace once
  for ch in "abc":
    await field._handle_char(ch)
  await field._handle_backspace()
  assert field.lines[0].text == "ab", f"Expected 'ab', got {repr(field.lines[0].text)}"
  assert field.cursor_col == 2
  print("  PASS: backspace deletes character")

  # Enter to make second line, then backspace to join
  await field._handle_enter()
  for ch in "de":
    await field._handle_char(ch)
  assert len(field.lines) == 2
  field.cursor_col = 0  # go to start of line 1
  await field._handle_backspace()
  assert len(field.lines) == 1, f"Expected 1 line after join, got {len(field.lines)}"
  assert field.lines[0].text == "abde", f"Expected 'abde', got {repr(field.lines[0].text)}"
  assert field.cursor_line == 0
  assert field.cursor_col == 2  # join point
  print("  PASS: backspace at line start joins lines")


async def test_quote_level_enter():
  """Test Enter on empty quoted line reduces level."""
  user = make_mock_user(width=80, height=24)
  user.cur_row = user.new_row = 5
  user.cur_col = user.new_col = 1

  field = await InputField.create(
    parent=type('FakeParent', (), {'user': user})(),
    user=user, width=40, height=10, max_length=1000, word_wrap=True,
    content=[Block("quoted text", level=1), Block("", level=1)],
  )

  # Cursor should start at line 0, col 0
  # Move to the empty quoted line (line 1)
  field.cursor_line = 1
  field.cursor_col = 0

  assert field.lines[1].level == 1, f"Expected level 1, got {field.lines[1].level}"
  assert field.lines[1].text == "", f"Expected empty text, got {repr(field.lines[1].text)}"

  # Press Enter on empty quoted line → should decrease level
  await field._handle_enter()
  assert field.lines[1].level == 0, f"Expected level 0 after Enter on empty quoted, got {field.lines[1].level}"
  print("  PASS: Enter on empty quoted line decreases level")


async def test_quote_level_backspace():
  """Test Backspace at col 0 on quoted line reduces level."""
  user = make_mock_user(width=80, height=24)
  user.cur_row = user.new_row = 5
  user.cur_col = user.new_col = 1

  field = await InputField.create(
    parent=type('FakeParent', (), {'user': user})(),
    user=user, width=40, height=10, max_length=1000, word_wrap=True,
    content=[Block("some text", level=2)],
  )

  field.cursor_line = 0
  field.cursor_col = 0
  assert field.lines[0].level == 2

  await field._handle_backspace()
  assert field.lines[0].level == 1, f"Expected level 1, got {field.lines[0].level}"
  assert field.lines[0].text == "some text"  # text unchanged
  print("  PASS: Backspace at col 0 on quoted line decreases level")


async def test_word_wrap_display_rows():
  """Test word wrap generates correct display rows."""
  user = make_mock_user(width=80, height=24)
  user.cur_row = user.new_row = 1
  user.cur_col = user.new_col = 1

  field = await InputField.create(
    parent=type('FakeParent', (), {'user': user})(),
    user=user, width=20, height=10, max_length=1000, word_wrap=True,
  )

  # Width=20, no_cursor_margin=False → usable=19
  # Type a long line that should wrap
  text = "the quick brown fox jumps over"
  field.lines[0].text = text
  field.cursor_col = len(text)
  field._compute_display_rows()

  print(f"\n--- word wrap test (width=20, usable=19) ---")
  print(f"  text: {repr(text)} ({len(text)} chars)")
  for i, dr in enumerate(field.display_rows):
    slice_text = text[dr.start_col:dr.end_col]
    print(f"  row {i}: [{dr.start_col}:{dr.end_col}] = {repr(slice_text)}")

  assert len(field.display_rows) >= 2, f"Expected >=2 display rows for wrapped text, got {len(field.display_rows)}"
  # Verify no display row exceeds usable width
  for dr in field.display_rows:
    row_len = len(dr.margin_prefix) + (dr.end_col - dr.start_col)
    assert row_len <= 19, f"Display row exceeds usable width: {row_len} > 19"
  print("  PASS: word wrap generates correct display rows")


async def test_cursor_screen_position_multiline():
  """Test cursor screen position is correct across multiple lines."""
  user = make_mock_user(width=80, height=24)
  user.cur_row = user.new_row = 3
  user.cur_col = user.new_col = 5

  field = await InputField.create(
    parent=type('FakeParent', (), {'user': user})(),
    user=user, width=40, height=10, max_length=1000, word_wrap=True,
  )

  # Add a few lines
  field.lines = [Line("first", 0), Line("second", 0), Line("third", 0)]
  field._compute_display_rows()

  # Cursor on line 2, col 3
  field.cursor_line = 2
  field.cursor_col = 3
  sr, sc = field._cursor_to_screen()
  assert sr == 5, f"Expected screen row 5 (3+2), got {sr}"
  assert sc == 8, f"Expected screen col 8 (5+3), got {sc}"
  print("  PASS: cursor position on line 2 col 3")

  # Cursor on line 0, col 0
  field.cursor_line = 0
  field.cursor_col = 0
  sr, sc = field._cursor_to_screen()
  assert sr == 3, f"Expected screen row 3, got {sr}"
  assert sc == 5, f"Expected screen col 5, got {sc}"
  print("  PASS: cursor position on line 0 col 0")


async def test_get_blocks_roundtrip():
  """Test content roundtrip through blocks."""
  user = make_mock_user(width=80, height=24)
  user.cur_row = user.new_row = 1
  user.cur_col = user.new_col = 1

  blocks_in = [Block("Hello", level=0), Block("Quoted reply", level=1), Block("My response", level=0)]
  field = await InputField.create(
    parent=type('FakeParent', (), {'user': user})(),
    user=user, width=40, height=10, max_length=1000, word_wrap=True,
    content=blocks_in,
  )

  blocks_out = field.get_blocks()
  assert len(blocks_out) == 3, f"Expected 3 blocks, got {len(blocks_out)}"
  assert blocks_out[0].text == "Hello" and blocks_out[0].level == 0
  assert blocks_out[1].text == "Quoted reply" and blocks_out[1].level == 1
  assert blocks_out[2].text == "My response" and blocks_out[2].level == 0
  print("  PASS: block roundtrip preserves content and levels")


async def main():
  print("Running InputField tests...\n")
  await test_basic_field()
  await test_field_with_outline()
  await test_button()
  await test_form_layout()
  await test_message_compose_layout()
  await test_ansi_move_and_send()
  await test_draw_field_cursor_position()
  await test_char_insert()
  await test_enter_split()
  await test_backspace()
  await test_quote_level_enter()
  await test_quote_level_backspace()
  await test_word_wrap_display_rows()
  await test_cursor_screen_position_multiline()
  await test_get_blocks_roundtrip()
  print("\nAll tests complete.")


if __name__ == "__main__":
  asyncio.run(main())
