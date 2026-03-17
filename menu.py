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
  Returns (dest_name, menu_item, parent_menu, error)."""
  for i, part in enumerate(parts):
    matched, err = _match_option(part, node.option_names, node.prefixes)
    if not matched:
      level = " > ".join(parts[:i]) if i > 0 else node.menu_name.title()
      return (None, None, None, f"At {level}: {err}")

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
  if not _jump_nodes:
    return (None, None, None, "Menu system not configured.")
  parts = [p.strip() for p in path_str.strip().split(".") if p.strip()]
  if not parts:
    return (None, None, None, "No path specified. Usage: /jump menu.option")
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
    elif len(matches) > 1:
      return (None, None, None, f"Ambiguous: \"{parts[0]}\" matches {', '.join(matches)}. Type more letters.")
  # Return the original option-tree error
  if root is not None:
    return _resolve_path(root, parts)
  return (None, None, None, "Menu system not configured.")


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

  # Enable mouse click reporting
  user.writer.write("\x1b[?1000h")
  user.mouse_reporting = True
  await user.writer.drain()

  try:
    error_msg = None
    while True:
      if menu_conf.screen_path:
        from common import show_screen
        show_screen(user, menu_conf.screen_path)
      else:
        await ansi_cls(user)

        # Breadcrumb path
        breadcrumb = _build_breadcrumb(Destinations, menu_name)
        ansi_color(user, fg=cyan, fg_br=False, bg=black)
        await send(user, " " + breadcrumb + cr + lf + cr + lf, drain=False)

        # Compute multi-column layout
        # Reserve rows: 1 breadcrumb, 1 blank, then items, then 1 error line, 1 blank, 1 prompt = ~5 rows after items
        available_rows = user.screen_height - user.cur_row - 4
        compactness = float(config.menu_compactness) if config.menu_compactness else 1.0
        columns, col_widths = _compute_column_layout(
          option_keys, user.screen_width, max(1, available_rows),
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
        item_cells = {}  # row_number -> list of (col_start, col_end, option_name)
        start_row = user.cur_row
        num_rows = max(len(col) for col in columns) if columns else 0

        # Render columns
        for row_idx in range(num_rows):
          await ansi_move(user, row=start_row + row_idx, col=1, drain=False)
          col_offset = 2  # leading indent
          for col_idx, col in enumerate(columns):
            if row_idx >= len(col):
              continue
            option_name = col[row_idx]
            min_pfx = prefixes[option_name]
            highlight_part = option_name[:min_pfx]
            rest_part = option_name[min_pfx:]
            cw = col_widths[col_idx]

            await ansi_move(user, row=start_row + row_idx, col=col_offset, drain=False)

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

        # Show error from previous attempt if any
        if error_msg:
          ansi_color(user, fg=red, fg_br=True, bg=black)
          await send(user, cr + lf + error_msg + cr + lf, drain=False)
          error_msg = None

        ansi_color(user, fg=white, fg_br=False, bg=black)
        await send(user, cr + lf + "Enter an option: ", drain=True)

        # Custom input loop that handles both typing and clicks
        buf = []
        prompt_row = user.cur_row
        prompt_col = user.cur_col
        chosen = None

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
            await send(user, key, drain=True)
          elif key == "\x08" or key == "\x7f":  # backspace
            if buf:
              buf.pop()
              await send(user, "\x08 \x08", drain=True)
          elif key == "\r" or key == "\x0d":
            break
          # Ignore other keys

        if chosen:
          if chosen == "eXit":
            return _exit_menu(user, menu_name, Destinations)
          option_conf = menu_conf.options[chosen]
          target = option_conf.target if option_conf and option_conf.target else chosen.lower()
          return RetVals(status=success, next_destination=_resolve_destination(target, menu_name),
                         next_menu_item=chosen)

        option_text = "".join(buf).strip()

        if option_text == "":
          continue

        # Slash commands
        lower = option_text.lower()

        # /quit
        if lower in ("/quit", "/q"):
          return RetVals(status=success, next_destination=Destinations.logout, next_menu_item=null)

        # /page <user> <message>
        if lower.startswith("/page ") or lower.startswith("/p "):
          rest = option_text.split(" ", 2)[1:]  # [target, message?]
          if not rest or not rest[0].strip():
            error_msg = "Usage: /page <user> <message>"
            continue
          target_handle = rest[0].strip()
          page_msg = rest[1].strip() if len(rest) > 1 else ""
          if not page_msg:
            error_msg = "Usage: /page <user> <message>"
            continue
          from bbs_msg import send_popup_to_user
          shown, reason = await send_popup_to_user(
            target_handle, page_msg,
            from_user=user.handle, from_handle=user.handle)
          if shown:
            error_msg = f"Page sent to {target_handle}."
          else:
            error_msg = reason
          continue

        # /jump (or /j) command
        if lower.startswith("/jump ") or lower.startswith("/j "):
          jump_path = option_text.split(" ", 1)[1].strip()
          if not jump_path:
            error_msg = "Usage: /jump menu.option  (e.g. /j forums.philosophy)"
            continue
          dest_name, menu_item_name, parent_name, err = resolve_jump(jump_path)
          if err:
            error_msg = err
            continue
          return RetVals(status=success,
                         next_destination=_resolve_destination(dest_name, parent_name),
                         next_menu_item=menu_item_name)

        # Unknown slash command
        if lower.startswith("/"):
          error_msg = f"Unknown command: {option_text.split()[0]}. Try /jump, /page, /quit"
          continue

        # Dotted path: resolve relative to current menu
        if "." in option_text:
          dest_name, menu_item_name, parent_name, err = resolve_dotted(menu_name, option_text)
          if dest_name:
            return RetVals(status=success,
                           next_destination=_resolve_destination(dest_name, parent_name),
                           next_menu_item=menu_item_name)
          if err:
            error_msg = err
            continue

        # Match using the prefix system
        chosen, err_msg = _match_option(option_text, option_keys, prefixes)
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

        error_msg = err_msg

  finally:
    # Disable mouse click reporting
    user.writer.write("\x1b[?1000l")
    user.mouse_reporting = False
    await user.writer.drain()
