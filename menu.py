import math

from input_output import *
from definitions import *
from keyboard_codes import click, left


# ---------------------------------------------------------------------------
# Jump tree — built once from config.menu_system, used by /jump
# ---------------------------------------------------------------------------

class _JumpNode:
  __slots__ = ('menu_name', 'option_names', 'prefixes', 'targets', 'children')
  def __init__(self, menu_name):
    self.menu_name = menu_name
    self.option_names = []
    self.prefixes = {}
    self.targets = {}    # option_name → dest_name string
    self.children = {}   # option_name → _JumpNode (for menu-type targets)

_jump_nodes = None  # {menu_name: _JumpNode}

def _ensure_jump_tree():
  global _jump_nodes
  if _jump_nodes is not None:
    return
  from config import get_config
  cfg = get_config()
  if not cfg.menu_system:
    _jump_nodes = {}
    return

  nodes = {}
  for mn in cfg.menu_system.keys():
    mc = cfg.menu_system[mn]
    if not mc or not mc.options:
      continue
    node = _JumpNode(mn)
    opt_keys = list(mc.options.keys()) if hasattr(mc.options, 'keys') else []
    for opt_name in opt_keys:
      oc = mc.options[opt_name]
      target = (str(oc.target) if oc and oc.target else opt_name.lower()) if oc else opt_name.lower()
      node.option_names.append(opt_name)
      node.targets[opt_name] = target
    node.prefixes = _compute_min_prefixes(node.option_names)
    nodes[mn] = node

  # Link children: options whose target is itself a menu
  for node in nodes.values():
    for opt_name, target in node.targets.items():
      if target in nodes:
        node.children[opt_name] = nodes[target]

  _jump_nodes = nodes


def _resolve_path(node, parts):
  """Walk a dotted path from a given jump node.
  Supports 'x' segments to go up to parent menu before continuing.
  'xx' is expanded to 'x.x', 'xxx' to 'x.x.x', etc.
  Returns (dest_name, menu_item, parent_menu, error)."""
  # Expand multi-x segments: "xx.foo" → "x.x.foo", "xxx" → "x.x.x"
  expanded = []
  for part in parts:
    if len(part) > 1 and part.lower() == 'x' * len(part):
      expanded.extend(['x'] * len(part))
    else:
      expanded.append(part)
  parts = expanded

  for i, part in enumerate(parts):
    # Handle 'x' (exit) — go up to parent menu
    if part.lower() == 'x':
      # Find the parent menu's node
      parent_menu = None
      for name, n in _jump_nodes.items():
        for opt_name, child in n.children.items():
          if child is node:
            parent_menu = name
            break
        if parent_menu:
          break
      if not parent_menu or parent_menu not in _jump_nodes:
        remaining = ".".join(parts[i:])
        return (None, None, None, f"At {node.menu_name.title()}: can't exit further with \"{remaining}\"")
      node = _jump_nodes[parent_menu]
      # If this is the last part, return to the parent menu
      if i == len(parts) - 1:
        return (parent_menu, None, None, None)
      continue

    matched, err = _match_option(part, node.option_names, node.prefixes)
    if not matched:
      level = " > ".join(parts[:i]) if i > 0 else node.menu_name.title()
      remaining = ".".join(parts[i:])
      return (None, None, None, f"At {level}: \"{remaining}\" doesn't match any option.")

    target = node.targets[matched]
    parent = node.menu_name
    is_last = (i == len(parts) - 1)

    if is_last:
      return (target, matched, parent, None)
    else:
      if matched in node.children:
        node = node.children[matched]
      else:
        return (None, None, None, f"\"{matched}\" is not a submenu — can't go deeper.")

  return (None, None, None, "Empty path.")


def resolve_jump(path_str):
  """Resolve a dotted path from the main menu (for /jump).
  Returns (dest_name, menu_item, parent_menu, error)."""
  _ensure_jump_tree()
  _no_match = f'"{path_str}" doesn\'t match any destination. Usage: /j option or menu.option'
  if not _jump_nodes:
    return (None, None, None, _no_match)
  parts = [p.strip() for p in path_str.strip().split(".") if p.strip()]
  if not parts:
    return (None, None, None, "Usage: /j option or menu.option")
  # Try resolving through the menu option tree first
  root = _jump_nodes.get("main")
  if root is not None:
    result = _resolve_path(root, parts)
    if result[3] is None:  # no error
      return result
  # Single component: try matching a menu name directly (e.g. /j main)
  if len(parts) == 1:
    p = parts[0].lower()
    matches = [mn for mn in _jump_nodes if mn.lower().startswith(p)]
    if len(matches) == 1:
      return (matches[0], null, None, None)
  # No match
  return (None, None, None, _no_match)


def resolve_dotted(menu_name, path_str):
  """Resolve a dotted path relative to the given menu (for inline dotted input).
  Returns (dest_name, menu_item, parent_menu, error)."""
  _ensure_jump_tree()
  node = _jump_nodes.get(menu_name) if _jump_nodes else None
  if node is None:
    return (None, None, None, None)  # no tree for this menu, let normal matching handle it
  parts = [p.strip() for p in path_str.strip().split(".") if p.strip()]
  if not parts:
    return (None, None, None, None)
  return _resolve_path(node, parts)


# ---------------------------------------------------------------------------

def _resolve_destination(target_name, parent_menu=None):
  """Resolve a destination name string to a Destinations handler.
  If parent_menu is given, stamps it on the resolved handler."""
  from common import Destinations
  dest = getattr(Destinations, target_name, Destinations.main)
  if parent_menu is not None and hasattr(dest, 'parent_menu'):
    dest.parent_menu = parent_menu
  return dest


async def _show_text_error(user, err, can_inline, prompt_row, prompt_col, typed_len, error_row=None):
  """Show a text-menu error without re-rendering the menu.
  First error: overwrites the prompt row with the error and reprints the prompt one row lower.
  Subsequent errors: updates the error row in place.
  Returns (new_prompt_row, new_prompt_col, error_row)."""
  if can_inline and len(err) > user.screen_width:
    can_inline = False
  if typed_len > 0:
    await ansi_move(user, prompt_row, prompt_col, drain=False)
    await send(user, " " * typed_len, drain=False)
  if can_inline:
    if error_row is None:
      # First error: overwrite prompt row with error, push prompt down one row
      await ansi_move(user, prompt_row, 1, drain=False)
      ansi_color(user, fg=red, fg_br=True, bg=black)
      await send(user, err[:user.screen_width].ljust(user.screen_width), drain=False)
      ansi_color(user, fg=white, fg_br=False, bg=black)
      await send(user, cr + lf + "Enter an option: ", drain=True)
      error_row = prompt_row
      prompt_row = user.cur_row
      prompt_col = user.cur_col
    else:
      # Subsequent error: update error row in place
      await ansi_move(user, error_row, 1, drain=False)
      ansi_color(user, fg=red, fg_br=True, bg=black)
      await send(user, err[:user.screen_width].ljust(user.screen_width), drain=False)
      ansi_color(user, fg=white, fg_br=False, bg=black)
      await ansi_move(user, prompt_row, prompt_col, drain=True)
  else:
    from input_fields import show_message_box
    await ansi_move(user, prompt_row, prompt_col, drain=True)
    await show_message_box(user, err, title="Invalid Input",
                           fg=white, fg_br=True, bg=black,
                           outline_fg=red, outline_fg_br=True)
    await ansi_move(user, prompt_row, prompt_col, drain=True)
  return prompt_row, prompt_col, error_row


def _exit_menu(user, menu_name, Destinations):
  """Handle eXit: go back to parent menu, or logout from main."""
  if menu_name == "main":
    return RetVals(status=success, next_destination=Destinations.logout, next_menu_item=null)
  handler = getattr(Destinations, menu_name, None)
  parent = getattr(handler, 'parent_menu', None) if handler else None
  if parent:
    return RetVals(status=success, next_destination=getattr(Destinations, parent), next_menu_item=null)
  return RetVals(status=success, next_destination=Destinations.main, next_menu_item=null)


def _compute_min_prefixes(names):
  """Compute the minimum unique prefix length for each name in the list.
  Returns a dict of {name: min_prefix_length}.
  The prefix is the shortest start of the name that uniquely identifies it
  among all names (case-insensitive)."""
  result = {}
  lower_names = [n.lower() for n in names]
  for i, name in enumerate(names):
    ln = lower_names[i]
    min_len = 1
    while min_len <= len(ln):
      prefix = ln[:min_len]
      # Count how many other names share this prefix
      conflicts = sum(1 for j, other in enumerate(lower_names) if j != i and other.startswith(prefix))
      if conflicts == 0:
        break
      min_len += 1
    result[name] = min(min_len, len(name))
  return result


def _match_option(input_text, option_names, prefixes):
  """Match user input against option names using the prefix system.
  input_text is case-insensitive.
  Returns (matched_name, error_msg). matched_name is the option or None.
  error_msg explains what went wrong when matched_name is None."""
  inp = input_text.lower()
  # Find all options whose name starts with the input
  partial_matches = [name for name in option_names if name.lower().startswith(inp)]
  # Of those, find which ones the input is long enough to uniquely select
  full_matches = [name for name in partial_matches if len(inp) >= prefixes[name]]

  if len(full_matches) == 1:
    return full_matches[0], None
  # Check for exact match
  for name in partial_matches:
    if name.lower() == inp:
      return name, None

  if len(partial_matches) > 1:
    names = ", ".join(partial_matches)
    return None, f"Ambiguous: \"{input_text}\" matches {names}. Type more letters."
  elif len(partial_matches) == 0:
    return None, f"\"{input_text}\" doesn't match any option."
  else:
    # One partial match but input is too short
    name = partial_matches[0]
    needed = prefixes[name]
    hint = name[:needed]
    return None, f"Type at least \"{hint}\" for {name}."


def _compute_column_layout(names, screen_width, max_rows, margin=3,
                           compactness=1.0):
  """Compute a multi-column layout for menu items.

  Finds a good balance between number of columns and column height.
  Each column is as wide as its widest item + margin.

  compactness: how much to prefer shorter/wider layouts over taller/narrower.
    1.0 = balanced. >1 = prefer more columns (shorter). <1 = prefer fewer columns (taller).

  Returns (columns, col_widths) where columns is a list of lists of names,
  and col_widths is a list of pixel widths per column.
  Returns (None, None) if the items can't fit.

  The items are filled column-first (top to bottom, then next column).
  """
  if not names:
    return [[]], [0]

  # Keep original order — layout uses lengths for sizing but preserves order
  sorted_names = list(names)
  total = len(sorted_names)

  # Try increasing number of columns, score each valid layout
  # Score prefers squarish layouts (not too tall, not too wide)
  candidates = []
  for num_cols in range(1, total + 1):
    rows_needed = math.ceil(total / num_cols)
    if rows_needed > max_rows:
      continue

    # Distribute items into columns (fill top-to-bottom, left-to-right)
    columns = []
    col_widths = []
    idx = 0
    for c in range(num_cols):
      col = []
      max_w = 0
      for r in range(rows_needed):
        if idx < total:
          col.append(sorted_names[idx])
          max_w = max(max_w, len(sorted_names[idx]))
          idx += 1
      columns.append(col)
      col_widths.append(max_w + margin)

    # Check total width fits screen (last column doesn't need trailing margin)
    total_width = sum(col_widths) - margin + 2  # 2 for leading indent
    if total_width > screen_width:
      continue

    # Score: prefer fewest columns that fit. Break ties by width usage.
    score = (num_cols * 1000) + total_width
    candidates.append((score, columns, col_widths, rows_needed))

    if rows_needed <= 1:
      break

  if not candidates:
    # Last resort: single column
    max_w = max(len(n) for n in sorted_names)
    if max_w + 2 <= screen_width and total <= max_rows:
      return [sorted_names], [max_w + margin]
    return None, None

  # Pick the layout with the best (lowest) score
  candidates.sort(key=lambda x: x[0])
  best = candidates[0]
  return best[1], best[2]


def _build_breadcrumb(Destinations, menu_name):
  """Build a breadcrumb path like 'Main > Forums' by walking parent_menu chain."""
  if menu_name == "main":
    return "Main"
  # Walk the parent_menu chain to build the path
  path = [menu_name.title()]
  current = menu_name
  while True:
    handler = getattr(Destinations, current, None)
    parent = getattr(handler, 'parent_menu', None) if handler else None
    if not parent:
      break
    if parent == "main":
      path.append("Main")
      break
    path.append(parent.title())
    current = parent
  if path[-1] != "Main":
    path.append("Main")
  path.reverse()
  return " > ".join(path)


async def do_menu(user, menu_name):
  from input_fields import InputField
  from common import check_keys, Destinations
  from config import get_config
  config = get_config()

  menu_conf = config.menu_system[menu_name]

  if not menu_conf or not menu_conf.options:
    return RetVals(status=fail, err_msg=f"Menu '{menu_name}' not found or has no options.",
                   next_destination=Destinations.main, next_menu_item=null)

  option_keys = list(menu_conf.options.keys()) if hasattr(menu_conf.options, 'keys') else []
  option_keys.append("eXit")

  # Compute minimum unique prefixes for all option names
  prefixes = _compute_min_prefixes(option_keys)

  # For screen menus: each option may define input: to override its match string.
  # show_prompt: False (default for screen menus) → silent, immediate match on unique prefix.
  # show_prompt: True (always for text menus, opt-in for screen menus via prompt: true) → echoed input, Enter to submit.
  show_prompt = not menu_conf.screen_path or bool(menu_conf.prompt)
  effective_keys = option_keys
  effective_prefixes = prefixes
  option_for_input = {k: k for k in option_keys}
  if menu_conf.screen_path:
    effective_keys = []
    option_for_input = {}
    for opt_name in option_keys:
      if opt_name == "eXit":
        effective_keys.append("eXit")
        option_for_input["eXit"] = "eXit"
        continue
      opt_conf = menu_conf.options[opt_name]
      inp = str(opt_conf.input) if opt_conf and opt_conf.input else opt_name
      effective_keys.append(inp)
      option_for_input[inp] = opt_name
    effective_prefixes = _compute_min_prefixes(effective_keys)

  # Enable mouse click reporting
  user.writer.write("\x1b[?1000h")
  user.mouse_reporting = True
  await user.writer.drain()

  try:
    error_msg = None
    needs_render = True  # text menus: skip re-render on errors; screen menus: always renders
    can_inline = False   # text menus: whether an inline error row fits below the prompt
    error_row = None     # row where inline error is currently displayed
    pending_error = getattr(user, 'pending_menu_error', None)
    if pending_error:
      user.pending_menu_error = None
    while True:
      # Transfer access-denied errors from user_director into screen menu's popup path
      if pending_error and menu_conf.screen_path:
        error_msg = pending_error
        pending_error = None
      item_cells = {}
      if menu_conf.screen_path:
        from common import show_screen
        await show_screen(user, menu_conf.screen_path)
        for opt_name in option_keys:
          if opt_name == "eXit":
            continue
          opt_conf = menu_conf.options[opt_name]
          clk = opt_conf.click if opt_conf else null
          if not clk:
            continue
          try:
            row_s = int(clk.row)
            col_s = int(clk.col)
            w = int(clk.width)
            h = int(clk.height) if clk.height else 1
          except (TypeError, ValueError):
            continue
          for dr in range(h):
            r = row_s + dr
            item_cells.setdefault(r, []).append((col_s, col_s + w - 1, opt_name))
        if error_msg:
          from input_fields import show_message_box
          await show_message_box(user, error_msg, title="Error",
                                 fg=white, fg_br=True, bg=black,
                                 outline_fg=red, outline_fg_br=True)
          error_msg = None
        if show_prompt:
          ansi_color(user, fg=white, fg_br=False, bg=black)
          await send(user, "Enter an option: ", drain=True)
      else:
        if needs_render:
          error_row = None  # reset error state on fresh render

          # If a pending access-denied error won't fit inline, show the popup NOW
          # over the current screen (before clearing), then render the menu cleanly.
          if pending_error:
            compactness = float(config.menu_compactness) if config.menu_compactness else 1.0
            _est_start = 3  # approximate row after ansi_cls + breadcrumb
            _avail = user.screen_height - _est_start - 3
            _fit, _ = (
              _compute_column_layout(option_keys, user.screen_width,
                                     max(1, _avail), compactness=compactness)
              if _avail > 0 else (None, None)
            )
            if _fit is None:
              from input_fields import show_message_box
              await show_message_box(user, pending_error, title="Access Denied",
                                     fg=white, fg_br=True, bg=black,
                                     outline_fg=red, outline_fg_br=True)
              pending_error = None
            # else: keep pending_error for inline display after render

          await ansi_cls(user)

          # Breadcrumb path
          breadcrumb = _build_breadcrumb(Destinations, menu_name)
          ansi_color(user, fg=cyan, fg_br=False, bg=black)
          await send(user, " " + breadcrumb + cr + lf + cr + lf, drain=False)

          compactness = float(config.menu_compactness) if config.menu_compactness else 1.0

          # Try fitting with 3 rows reserved (blank + error + prompt) for inline errors.
          # Fall back to 2 rows (blank + prompt) and use a popup if it doesn't fit.
          available_rows_inline = user.screen_height - user.cur_row - 3
          available_rows_normal = user.screen_height - user.cur_row - 2
          cols_try, cw_try = (
            _compute_column_layout(option_keys, user.screen_width,
                                   max(1, available_rows_inline), compactness=compactness)
            if available_rows_inline > 0 else (None, None)
          )
          if cols_try is not None:
            can_inline = True
            columns, col_widths = cols_try, cw_try
          else:
            can_inline = False
            columns, col_widths = _compute_column_layout(
              option_keys, user.screen_width, max(1, available_rows_normal),
              compactness=compactness)

          if columns is None:
            return RetVals(status=fail, err_msg="Too many menu items to fit on screen.",
                           next_destination=Destinations.main, next_menu_item=null)

          # Pre-compute access for each option
          access = {}
          for option_name in option_keys:
            if option_name == "eXit":
              access[option_name] = True
              continue
            option_conf = menu_conf.options[option_name]
            target = option_conf.target if option_conf and option_conf.target else option_name.lower()
            target_dest = getattr(Destinations, target, None)
            r = check_keys(user, target_dest) if target_dest else RetVals(status=success)
            access[option_name] = (r.status == success)

          # Track which screen (row, col_range) maps to which option for clicks
          start_row = user.cur_row
          num_rows = max(len(col) for col in columns) if columns else 0

          # Render columns
          for row_idx in range(num_rows):
            await ansi_move_deferred(user, row=start_row + row_idx, col=1, drain=False)
            col_offset = 2  # leading indent
            for col_idx, col in enumerate(columns):
              if row_idx >= len(col):
                continue
              option_name = col[row_idx]
              min_pfx = prefixes[option_name]
              highlight_part = option_name[:min_pfx]
              rest_part = option_name[min_pfx:]
              cw = col_widths[col_idx]

              await ansi_move_deferred(user, row=start_row + row_idx, col=col_offset, drain=False)

              # Record clickable area
              screen_row = start_row + row_idx
              if screen_row not in item_cells:
                item_cells[screen_row] = []
              display_len = len("eXit (Logout)") if option_name == "eXit" and menu_name == "main" else len(option_name)
              item_cells[screen_row].append((col_offset, col_offset + display_len - 1, option_name))

              if access.get(option_name, True):
                if option_name == "eXit":
                  # Highlight the capital X
                  ansi_color(user, fg=white, fg_br=False, bg=black)
                  await send(user, "e", drain=False)
                  ansi_color(user, fg=white, fg_br=True, bg=black)
                  await send(user, "X", drain=False)
                  ansi_color(user, fg=white, fg_br=False, bg=black)
                  if menu_name == "main":
                    await send(user, "it (Logout)", drain=False)
                  else:
                    await send(user, "it", drain=False)
                else:
                  ansi_color(user, fg=white, fg_br=True, bg=black)
                  await send(user, highlight_part, drain=False)
                  ansi_color(user, fg=white, fg_br=False, bg=black)
                  await send(user, rest_part, drain=False)
              else:
                ansi_color(user, fg=black, fg_br=True, bg=black)
                await send(user, option_name, drain=False)

              col_offset += cw

            await send(user, cr + lf, drain=False)

          ansi_color(user, fg=white, fg_br=False, bg=black)
          if pending_error and can_inline:
            # blank row, then error row, then prompt — no pre-reserved empty rows
            await send(user, cr + lf, drain=False)
            error_row = user.cur_row
            ansi_color(user, fg=red, fg_br=True, bg=black)
            await send(user, pending_error[:user.screen_width].ljust(user.screen_width), drain=False)
            ansi_color(user, fg=white, fg_br=False, bg=black)
            await send(user, cr + lf + "Enter an option: ", drain=True)
            pending_error = None
          else:
            await send(user, cr + lf + "Enter an option: ", drain=True)

      # Input loop
      buf = []
      prompt_row = user.cur_row
      prompt_col = user.cur_col
      chosen = None
      screen_retval = None  # set by immediate-fire x-pattern to return after inner loop

      while True:
        key = await get_input_key(user)

        if key == click:
          btn = getattr(key, 'button', None)
          if btn == left:
            click_row = key.row
            click_col = key.col
            # Check if the click is on a menu item
            clicked_option = None
            for col_start, col_end, opt_name in item_cells.get(click_row, []):
              if col_start <= click_col <= col_end:
                clicked_option = opt_name
                break
            if clicked_option:
              chosen = clicked_option
              break
          # Ignore other mouse events
          continue

        if isinstance(key, str) and len(key) == 1 and ord(key) >= 32:
          buf.append(key)
          if show_prompt:
            await send(user, key, drain=True)
          elif menu_conf.screen_path:
            current = "".join(buf)
            partial = [k for k in effective_keys if k.lower().startswith(current.lower())]
            if not partial:
              buf.pop()
              if current.lower() == "x" * len(current):
                levels = len(current)
                dest_name = menu_name
                for _ in range(levels):
                  handler = getattr(Destinations, dest_name, None)
                  parent = getattr(handler, 'parent_menu', None) if handler else None
                  if not parent:
                    screen_retval = RetVals(status=success, next_destination=Destinations.logout, next_menu_item=null)
                    break
                  dest_name = parent
                else:
                  screen_retval = RetVals(status=success, next_destination=getattr(Destinations, dest_name), next_menu_item=null)
                break
              from input_fields import show_message_box
              await show_message_box(user, f'"{current}" doesn\'t match any option.',
                                     title="Invalid Input", fg=white, fg_br=True, bg=black,
                                     outline_fg=red, outline_fg_br=True)
            else:
              matched, _ = _match_option(current, effective_keys, effective_prefixes)
              if matched:
                chosen = option_for_input.get(matched, matched)
                break
        elif key == "\x08" or key == "\x7f":  # backspace
          if buf:
            buf.pop()
            if show_prompt:
              await send(user, "\x08 \x08", drain=True)
        elif key == "\r" or key == "\x0d":
          if show_prompt:
            if menu_conf.screen_path and buf:
              current = "".join(buf).strip()
              matched, match_err = _match_option(current, effective_keys, effective_prefixes)
              if not matched:
                if current.lower() == "x" * len(current):
                  break  # no option matched; outer loop x-pattern handler takes it
                typed_len = len(buf)
                buf.clear()
                from input_fields import show_message_box
                await show_message_box(user, match_err or f'"{current}" doesn\'t match any option.',
                                       title="Invalid Input", fg=white, fg_br=True, bg=black,
                                       outline_fg=red, outline_fg_br=True)
                await ansi_move(user, prompt_row, prompt_col, drain=False)
                await send(user, " " * typed_len, drain=False)
                await ansi_move(user, prompt_row, prompt_col, drain=True)
                continue
            break
          else:
            buf.clear()
        elif key == "esc" and menu_conf.screen_path:
          if buf:
            typed_len = len(buf)
            buf.clear()
            if show_prompt:
              await ansi_move(user, prompt_row, prompt_col, drain=False)
              await send(user, " " * typed_len, drain=False)
              await ansi_move(user, prompt_row, prompt_col, drain=True)
          else:
            return _exit_menu(user, menu_name, Destinations)
        # Ignore other keys

      if screen_retval:
        return screen_retval

      if chosen:
        if chosen == "eXit":
          return _exit_menu(user, menu_name, Destinations)
        option_conf = menu_conf.options[chosen]
        target = option_conf.target if option_conf and option_conf.target else chosen.lower()
        return RetVals(status=success, next_destination=_resolve_destination(target, menu_name),
                       next_menu_item=chosen)

      option_text = "".join(buf).strip()

      if option_text == "":
        if not menu_conf.screen_path:
          needs_render = False
        continue

      # Helper: show error and loop back without re-rendering (text menus only).
      # For screen menus, fall through to error_msg which triggers re-render.
      async def _err(msg):
        nonlocal needs_render, prompt_row, prompt_col, error_row
        if not menu_conf.screen_path:
          prompt_row, prompt_col, error_row = await _show_text_error(
            user, msg, can_inline, prompt_row, prompt_col, len(option_text), error_row)
          buf.clear()
          needs_render = False
          return True  # caller should continue
        return False

      # Slash commands
      lower = option_text.lower()

      # /quit
      if lower in ("/quit", "/q"):
        return RetVals(status=success, next_destination=Destinations.logout, next_menu_item=null)

      # /page <user> <message>
      if lower.startswith("/page ") or lower.startswith("/p "):
        rest = option_text.split(" ", 2)[1:]  # [target, message?]
        if not rest or not rest[0].strip():
          if await _err("Usage: /page <user> <message>"): continue
          else: error_msg = "Usage: /page <user> <message>"
          continue
        target_handle = rest[0].strip()
        page_msg = rest[1].strip() if len(rest) > 1 else ""
        if not page_msg:
          if await _err("Usage: /page <user> <message>"): continue
          else: error_msg = "Usage: /page <user> <message>"
          continue
        from bbs_msg import send_popup_to_user
        shown, reason = await send_popup_to_user(
          target_handle, page_msg,
          from_user=user.handle, from_handle=user.handle, sender=user)
        msg = f"Page sent to {target_handle}." if shown else reason
        if await _err(msg): continue
        else: error_msg = msg
        continue

      # /jump (or /j) command
      if lower.startswith("/jump ") or lower.startswith("/j "):
        jump_path = option_text.split(" ", 1)[1].strip()
        if not jump_path:
          if await _err("Usage: /j option or menu.option"): continue
          else: error_msg = "Usage: /j option or menu.option"
          continue
        dest_name, menu_item_name, parent_name, err = resolve_jump(jump_path)
        if err:
          if await _err(err): continue
          else: error_msg = err
          continue
        return RetVals(status=success,
                       next_destination=_resolve_destination(dest_name, parent_name),
                       next_menu_item=menu_item_name)

      # /info <user> — view user profile
      if lower.startswith("/info ") or lower.startswith("/i "):
        rest = option_text.split(" ", 1)
        if len(rest) < 2 or not rest[1].strip():
          if await _err("Usage: /info <user>"): continue
          else: error_msg = "Usage: /info <user>"
          continue
        from userinfo import show_user_info
        result_msg = await show_user_info(user, rest[1].strip())
        if result_msg:
          if await _err(result_msg): continue
          else: error_msg = result_msg
          continue
        needs_render = True
        continue

      # /crash — sysop-only test command to trigger a traceback popup
      if lower == "/crash":
        if "sysop" not in user.keys:
          if await _err("Unknown command: /crash. Try /jump, /page, /info, /quit"): continue
          else: error_msg = "Unknown command: /crash. Try /jump, /page, /info, /quit"
          continue
        raise RuntimeError("Test crash triggered by /crash command.")

      # /testpopups — sysop-only: queue several popups to test queueing
      if lower == "/testpopups":
        if "sysop" not in user.keys:
          if await _err("Unknown command. Try /jump, /page, /info, /quit"): continue
          else: error_msg = "Unknown command. Try /jump, /page, /info, /quit"
          continue
        # Queue popups 2 and 3 first, then show popup 1 (which drains the queue)
        user.popup_queue.append(dict(text="Popup 2 of 3: This is the second queued popup.", title="Test 2/3", fg=white, fg_br=True, bg=black, bg_br=False, outline_fg=yellow, outline_fg_br=True, outline_bg=black, outline_bg_br=False))
        user.popup_queue.append(dict(text="Popup 3 of 3: This is the third and final popup.", title="Test 3/3", fg=white, fg_br=True, bg=black, bg_br=False, outline_fg=magenta, outline_fg_br=True, outline_bg=black, outline_bg_br=False))
        from bbs_msg import send_popup
        await send_popup(user, "Popup 1 of 3: This is the first queued popup.", title="Test 1/3", fg=white, fg_br=True, outline_fg=cyan, outline_fg_br=True)
        needs_render = True
        continue

      # Unknown slash command
      if lower.startswith("/"):
        msg = f"Unknown command: {option_text.split()[0]}. Try /jump, /page, /info, /quit"
        if await _err(msg): continue
        else: error_msg = msg
        continue

      # Dotted path: resolve relative to current menu
      if "." in option_text:
        dest_name, menu_item_name, parent_name, err = resolve_dotted(menu_name, option_text)
        if dest_name:
          return RetVals(status=success,
                         next_destination=_resolve_destination(dest_name, parent_name),
                         next_menu_item=menu_item_name)
        if err:
          if await _err(err): continue
          else: error_msg = err
          continue

      # Match using the prefix system
      matched_input, err_msg = _match_option(option_text, effective_keys, effective_prefixes)
      chosen = option_for_input.get(matched_input) if matched_input else None
      if chosen:
        if chosen == "eXit":
          return _exit_menu(user, menu_name, Destinations)
        option_conf = menu_conf.options[chosen]
        target = option_conf.target if option_conf and option_conf.target else chosen.lower()
        return RetVals(status=success, next_destination=_resolve_destination(target, menu_name),
                       next_menu_item=chosen)

      # x, xx, xxx, etc. — go up N levels (1 x = eXit, 2 = two levels, etc.)
      if len(option_text) >= 1 and option_text.lower() == "x" * len(option_text):
        levels = len(option_text)
        dest_name = menu_name
        for _ in range(levels):
          handler = getattr(Destinations, dest_name, None)
          parent = getattr(handler, 'parent_menu', None) if handler else None
          if not parent:
            # Reached main (or beyond) — logout
            return RetVals(status=success, next_destination=Destinations.logout, next_menu_item=null)
          dest_name = parent
        return RetVals(status=success, next_destination=getattr(Destinations, dest_name), next_menu_item=null)

      if await _err(err_msg): continue
      else: error_msg = err_msg

  finally:
    # Disable mouse click reporting
    user.writer.write("\x1b[?1000l")
    user.mouse_reporting = False
    await user.writer.drain()
