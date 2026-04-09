import math

from input_output import *
from definitions import *
from keyboard_codes import click, left


# ---------------------------------------------------------------------------
# Menu tree — built once from config.menu_system at startup
# ---------------------------------------------------------------------------

class OptionInfo:
  """Info for a leaf menu option (no sub-menu)."""
  __slots__ = ('target', 'template', 'conf')
  def __init__(self, target, template=None, conf=None):
    self.target = target        # destination name string (e.g., "forum")
    self.template = template    # menu_item template list (e.g., ["..", "."]) or None
    self.conf = conf            # raw option config from YAML

class MenuNode:
  """A node in the menu tree. Each menu (and sub-menu) is a MenuNode."""
  __slots__ = ('name', 'menu_name', 'config', 'parent', 'option_names',
               'prefixes', 'targets', 'children', 'options_info')
  def __init__(self, name, config=None, parent=None):
    self.name = name            # display name (e.g., "Spirituality & Mysticism")
    self.menu_name = name       # compat with old _JumpNode.menu_name
    self.config = config        # menu config (has .options, .screen_path, etc.)
    self.parent = parent        # parent MenuNode, or None for root
    self.option_names = []      # ordered list of option display names
    self.prefixes = {}          # {name: min_prefix_len}
    self.targets = {}           # option_name → dest_name string (for jump tree compat)
    self.children = {}          # option_name → MenuNode (sub-menus)
    self.options_info = {}      # option_name → OptionInfo (for leaf options)

_menu_nodes = None  # {menu_name: MenuNode}
# Keep _jump_nodes as alias for backward compat in resolve functions
_jump_nodes = None

def _ensure_menu_tree():
  global _menu_nodes, _jump_nodes
  if _menu_nodes is not None:
    return
  from config import get_config
  cfg = get_config()
  if not cfg.menu_system:
    _menu_nodes = _jump_nodes = {}
    return

  from config import Config

  nodes = {}

  # Pass 1: create a MenuNode per menu_system entry
  for mn in cfg.menu_system.keys():
    mc = cfg.menu_system[mn]
    if not mc or not mc.options:
      continue
    node = MenuNode(mn, config=mc)
    opt_keys = list(mc.options.keys()) if hasattr(mc.options, 'keys') else []
    for opt_name in opt_keys:
      oc = mc.options[opt_name]
      target = (str(oc.target) if oc and oc.target else opt_name.lower()) if oc else opt_name.lower()
      node.option_names.append(opt_name)
      node.targets[opt_name] = target
      # Read an explicit menu_item template if present on the option config
      tmpl = None
      if oc and oc is not null and hasattr(oc, 'menu_item') and oc.menu_item:
        mi = oc.menu_item
        tmpl = list(mi) if hasattr(mi, '__iter__') and not isinstance(mi, str) else [str(mi)]
      node.options_info[opt_name] = OptionInfo(target=target, template=tmpl, conf=oc)
    node.prefixes = _compute_min_prefixes(node.option_names)
    nodes[mn] = node

  # Pass 2: link options that target another menu as children (sub-menus)
  for node in nodes.values():
    for opt_name, target in node.targets.items():
      if target in nodes:
        node.children[opt_name] = nodes[target]
        nodes[target].parent = node

  # Pass 3: expand option_defaults.options into child nodes
  # This creates sub-menu nodes under each parent option (e.g., forums → each forum → actions)
  for mn in cfg.menu_system.keys():
    mc = cfg.menu_system[mn]
    if not mc or not mc.option_defaults or not mc.option_defaults.options:
      continue
    node = nodes.get(mn)
    if not node:
      continue
    default_sub = mc.option_defaults.options
    sub_keys = [k for k in (list(default_sub.keys()) if hasattr(default_sub, 'keys') else []) if k != 'option_defaults']
    if not sub_keys:
      continue

    # Resolve default target and template from inner option_defaults
    sub_defaults = default_sub.option_defaults if hasattr(default_sub, 'option_defaults') and default_sub.option_defaults else null
    default_target = None
    if sub_defaults and sub_defaults is not null and hasattr(sub_defaults, 'target') and sub_defaults.target:
      default_target = str(sub_defaults.target)
    elif mc.option_defaults and mc.option_defaults.target:
      default_target = str(mc.option_defaults.target)
    template = None
    if sub_defaults and sub_defaults is not null and sub_defaults.menu_item:
      mi = sub_defaults.menu_item
      template = list(mi) if hasattr(mi, '__iter__') and not isinstance(mi, str) else [str(mi)]
    if not template:
      template = ['..', '.']

    # Create a child MenuNode per parent option
    for opt_name in node.option_names:
      if opt_name in node.children:
        continue  # already links to another menu

      # If the option has its own explicit target (i.e. it's a leaf that
      # routes directly to a module), don't generate a sub-menu for it.
      own_conf = mc.options[opt_name] if mc.options else null
      if own_conf and own_conf is not null and hasattr(own_conf, 'target') and own_conf.target:
        # Override the inherited per-option target so it routes directly.
        node.targets[opt_name] = str(own_conf.target)
        # Replace the OptionInfo so user_director sees the leaf's own target/template.
        own_template = None
        if hasattr(own_conf, 'menu_item') and own_conf.menu_item:
          mi = own_conf.menu_item
          own_template = list(mi) if hasattr(mi, '__iter__') and not isinstance(mi, str) else [str(mi)]
        node.options_info[opt_name] = OptionInfo(
          target=str(own_conf.target), template=own_template, conf=own_conf)
        continue

      sub_opts = {k: default_sub[k] for k in sub_keys}
      child_config = Config({'options': Config(sub_opts)})
      child = MenuNode(opt_name, config=child_config, parent=node)

      for sk in sub_keys:
        sk_conf = default_sub[sk]
        sk_target = default_target or sk.lower()
        if sk_conf and sk_conf is not null and hasattr(sk_conf, 'target') and sk_conf.target:
          sk_target = str(sk_conf.target)
        child.option_names.append(sk)
        child.targets[sk] = sk_target
        child.options_info[sk] = OptionInfo(target=sk_target, template=template, conf=sk_conf)
      child.prefixes = _compute_min_prefixes(child.option_names)
      node.children[opt_name] = child

  _menu_nodes = _jump_nodes = nodes


def get_menu_node(name):
  """Get a MenuNode by name. Builds the tree if needed."""
  _ensure_menu_tree()
  return _menu_nodes.get(name)


# Keep old name as alias
_ensure_jump_tree = _ensure_menu_tree


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
      if not node.parent:
        remaining = ".".join(parts[i:])
        return (None, None, None, f"At {node.menu_name.title()}: can't exit further with \"{remaining}\"")
      node = node.parent
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


def _resolve_greedy(node, path_str, path_so_far=()):
  """Resolve a dotted path greedily: try longest literal match first at each level.
  For 'a.b.c.d', try matching 'a.b.c.d' as one option, then 'a.b.c' + recurse on 'd',
  then 'a.b' + recurse on 'c.d', then 'a' + recurse on 'b.c.d'.
  path_so_far accumulates matched names into a tuple for multi-level menu_item.
  Returns (dest_name, menu_item_tuple, parent_menu, error)."""
  if not path_str:
    return (None, None, None, "Empty path.")

  # Find all dot positions
  dots = [i for i, ch in enumerate(path_str) if ch == '.']

  # Try longest match first: whole string, then split at last dot, second-to-last, etc.
  split_points = [len(path_str)] + list(reversed(dots))

  for sp in split_points:
    segment = path_str[:sp].strip()
    remainder = path_str[sp + 1:].strip() if sp < len(path_str) else ""

    if not segment:
      continue

    # Handle 'x' (exit) segments
    if segment.lower() == 'x' or (len(segment) > 1 and segment.lower() == 'x' * len(segment)):
      x_count = len(segment)
      current = node
      ok = True
      for _ in range(x_count):
        if not current.parent:
          ok = False
          break
        current = current.parent
      if ok:
        if not remainder:
          return (current.menu_name, None, None, None)
        result = _resolve_greedy(current, remainder, path_so_far)
        if result[3] is None:
          return result
      continue

    # Try matching this segment as an option
    matched, err = _match_option(segment, node.option_names, node.prefixes)
    if not matched:
      continue  # try a shorter segment

    target = node.targets[matched]
    parent = node.menu_name
    new_path = path_so_far + (matched,)

    if not remainder:
      # This is the last segment — return the match with accumulated path
      return (target, new_path, parent, None)

    # More segments to resolve — this must be a submenu
    if matched in node.children:
      child = node.children[matched]
      # If the child is a top-level menu destination, reset the path
      # (the menu transition is handled by user_director, path restarts)
      child_path = () if child.name in (_menu_nodes or {}) else new_path
      result = _resolve_greedy(child, remainder, child_path)
      if result[3] is None:
        return result
      # This split didn't work — try shorter segment

  # Nothing worked
  return (None, None, None, f"At {node.menu_name.title()}: \"{path_str}\" doesn't match any option.")


def resolve_jump(path_str):
  """Resolve a dotted path from the main menu (for /jump).
  Uses greedy longest-match to support option names containing dots.
  Returns (dest_name, menu_item, parent_menu, error)."""
  _ensure_jump_tree()
  _no_match = f'"{path_str}" doesn\'t match any destination. Usage: /j option or menu.option'
  if not _jump_nodes:
    return (None, None, None, _no_match)
  path_str = path_str.strip()
  if not path_str:
    return (None, None, None, "Usage: /j option or menu.option")
  root = _jump_nodes.get("main")
  if root is not None:
    result = _resolve_greedy(root, path_str)
    if result[3] is None:
      return result
  # Single component: try matching a menu name directly (e.g. /j main)
  if "." not in path_str:
    p = path_str.lower()
    matches = [mn for mn in _jump_nodes if mn.lower().startswith(p)]
    if len(matches) == 1:
      return (matches[0], null, None, None)
  # No match
  if root is not None:
    result = _resolve_greedy(root, path_str)
    return (None, None, None, result[3] or _no_match)
  return (None, None, None, _no_match)


def resolve_dotted(menu_name, path_str):
  """Resolve a dotted path relative to the given menu (for inline dotted input).
  Uses greedy longest-match to support option names containing dots.
  Returns (dest_name, menu_item, parent_menu, error)."""
  _ensure_jump_tree()
  node = _jump_nodes.get(menu_name) if _jump_nodes else None
  if node is None:
    return (None, None, None, None)  # no tree for this menu, let normal matching handle it
  path_str = path_str.strip()
  if not path_str:
    return (None, None, None, None)
  return _resolve_greedy(node, path_str)


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


_EXIT_SUB = object()  # sentinel: exit from a sub-menu back to parent do_menu

def _exit_menu(user, node, Destinations, levels=1):
  """Handle eXit: go back to parent menu, or logout from main.
  For sub-menus (node has a parent that's also a menu), returns _EXIT_SUB sentinel."""
  current = node
  for _ in range(levels):
    if current.name == "main" or current.parent is None:
      return RetVals(status=success, next_destination=Destinations.logout, next_menu_item=null)
    parent = current.parent
    # If the parent is a real menu destination, navigate to it
    if parent.name in (_menu_nodes or {}):
      current = parent
    else:
      # Parent is a sub-menu node — signal to return up the recursive call stack
      return RetVals(status=success, next_destination=_EXIT_SUB, next_menu_item=null,
                     _exit_levels=levels)
  if current.name in (_menu_nodes or {}):
    return RetVals(status=success, next_destination=getattr(Destinations, current.name, Destinations.main),
                   next_menu_item=null)
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


def _build_breadcrumb(node_or_name, _Destinations=None):
  """Build a breadcrumb path like 'Main > Forums' by walking parent pointers.
  Accepts a MenuNode or a menu name string."""
  _ensure_menu_tree()
  if isinstance(node_or_name, str):
    node = _menu_nodes.get(node_or_name)
    if not node:
      return node_or_name.title()
  else:
    node = node_or_name
  if node.name == "main":
    return "Main"
  path = [node.name.title()]
  current = node.parent
  while current:
    path.append("Main" if current.name == "main" else current.name.title())
    current = current.parent
  if path[-1] != "Main":
    path.append("Main")
  path.reverse()
  return " > ".join(path)


def _resolve_menu_item_template(template, context):
  """Resolve a menu_item template list into a tuple.
  Template elements:
    '..'        — parent option name
    '.'         — current option name
    '..action'  — parent option's 'action' field
    '.action'   — current option's 'action' field
    '..field'   — parent option's 'field' attribute
    '.field'    — current option's 'field' attribute
    '...'       — grandparent option name
    literal str — passed as-is
  context is a dict with keys: 'parent_name', 'parent_conf', 'self_name', 'self_conf',
                                'grandparent_name', 'grandparent_conf'
  """
  result = []
  for item in template:
    item = str(item)
    if item == '..':
      result.append(context.get('parent_name', ''))
    elif item == '.':
      result.append(context.get('self_name', ''))
    elif item == '...':
      result.append(context.get('grandparent_name', ''))
    elif item.startswith('..') and len(item) > 2 and item[2] != '.':
      # ..field — attribute of parent option config
      field = item[2:]
      parent_conf = context.get('parent_conf')
      if parent_conf and parent_conf is not null and hasattr(parent_conf, field):
        val = getattr(parent_conf, field)
        result.append(str(val) if val and val is not null else '')
      else:
        result.append('')
    elif item.startswith('.') and len(item) > 1:
      # .field — attribute of current option config
      field = item[1:]
      self_conf = context.get('self_conf')
      if self_conf and self_conf is not null and hasattr(self_conf, field):
        val = getattr(self_conf, field)
        result.append(str(val) if val and val is not null else '')
      else:
        result.append('')
    else:
      result.append(item)
  return tuple(result)


async def _handle_sub_menu(user, chosen, option_conf, default_sub, menu_name, Destinations):
  """Show a sub-menu from option_defaults.options, then build the result.
  Returns RetVals on success, or None if user exited the sub-menu."""

  sub_chosen = await _show_sub_menu(user, chosen, default_sub, menu_name)
  if sub_chosen is None:
    return None

  # Find target from sub-option config, sub option_defaults, or parent option
  sub_conf = default_sub[sub_chosen] if sub_chosen in default_sub else null
  sub_defaults = default_sub.option_defaults if hasattr(default_sub, 'option_defaults') and default_sub.option_defaults else null
  target = None
  if sub_conf and sub_conf is not null and hasattr(sub_conf, 'target') and sub_conf.target:
    target = str(sub_conf.target)
  elif sub_defaults and sub_defaults is not null and hasattr(sub_defaults, 'target') and sub_defaults.target:
    target = str(sub_defaults.target)
  elif option_conf and option_conf.target:
    target = str(option_conf.target)
  else:
    target = chosen.lower()

  # Build menu_item from template or default
  template = None
  if sub_defaults and sub_defaults is not null and sub_defaults.menu_item:
    template = list(sub_defaults.menu_item) if hasattr(sub_defaults.menu_item, '__iter__') and not isinstance(sub_defaults.menu_item, str) else [str(sub_defaults.menu_item)]
  if not template:
    template = ['..', '.']
  mi = _resolve_menu_item_template(template, {
    'parent_name': chosen, 'parent_conf': option_conf,
    'self_name': sub_chosen, 'self_conf': sub_conf,
  })
  return RetVals(status=success, next_destination=_resolve_destination(target, menu_name),
                 next_menu_item=mi)


async def _show_sub_menu(user, parent_chosen, sub_options, parent_menu_name):
  """Show a sub-menu from option_defaults.options. Returns (chosen_sub, action) or None if exited."""
  from input_output import get_input_key
  from common import Destinations

  sub_keys = [k for k in (list(sub_options.keys()) if hasattr(sub_options, 'keys') else []) if k != 'option_defaults']
  sub_keys.append("eXit")
  sub_prefixes = _compute_min_prefixes(sub_keys)

  while True:
    await ansi_cls(user)
    ansi_color(user, fg=cyan, fg_br=False, bg=black)
    breadcrumb = _build_breadcrumb(parent_menu_name)
    await send(user, f" {breadcrumb} > {parent_chosen}" + cr + lf + cr + lf, drain=False)

    # Render sub-menu options (same style as text menus: 1 space indent)
    for sk in sub_keys:
      prefix_len = sub_prefixes.get(sk, 1)
      ansi_color(user, fg=white, fg_br=True, bg=black)
      await send(user, " " + sk[:prefix_len], drain=False)
      ansi_color(user, fg=white, fg_br=False, bg=black)
      await send(user, sk[prefix_len:] + cr + lf, drain=False)

    await send(user, cr + lf, drain=False)
    ansi_color(user, fg=white, fg_br=False, bg=black)
    await send(user, "Option: ", drain=True)

    # Read input
    buf = []
    while True:
      key = await get_input_key(user)
      if key == cr:
        break
      if key == back:
        if buf:
          buf.pop()
          user.writer.write(back + " " + back)
          await user.writer.drain()
        continue
      if isinstance(key, str) and len(key) == 1 and ord(key) >= 32:
        buf.append(key)
        await send(user, key, drain=True)
        # Auto-submit on unambiguous single-char match
        text = "".join(buf)
        matched, _ = _match_option(text, sub_keys, sub_prefixes)
        if matched:
          await send(user, cr + lf, drain=False)
          break
        continue

    text = "".join(buf).strip()
    if not text:
      continue

    if text.lower() == "x":
      return None

    matched, err = _match_option(text, sub_keys, sub_prefixes)
    if matched:
      if matched == "eXit":
        return None
      return matched
    # Show error and loop
    ansi_color(user, fg=red, fg_br=True, bg=black)
    await send(user, cr + lf + "  " + (err or "No match.") + cr + lf, drain=True)
    await get_input_key(user)


async def do_menu(user, menu_name_or_node):
  from input_fields import InputField
  from common import check_keys, Destinations
  from config import get_config
  config = get_config()

  _ensure_menu_tree()

  # Accept either a string menu name or a MenuNode
  if isinstance(menu_name_or_node, MenuNode):
    node = menu_name_or_node
    menu_name = node.name
    menu_conf = node.config
  else:
    menu_name = menu_name_or_node
    node = _menu_nodes.get(menu_name)
    menu_conf = config.menu_system[menu_name]
    if node is None:
      # Fallback: create a temporary node
      node = MenuNode(menu_name, config=menu_conf)

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
  user.writer.write("\x1b[?1000h\x1b[?1002h")
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
          breadcrumb = _build_breadcrumb(node)
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
                screen_retval = _exit_menu(user, node, Destinations, levels=len(current))
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
            return _exit_menu(user, node, Destinations)
        # Ignore other keys

      if screen_retval:
        return screen_retval

      if chosen:
        if chosen == "eXit":
          return _exit_menu(user, node, Destinations)
        # Sub-menu? Return the child node as destination for user_director
        child_node = node.children.get(chosen)
        if child_node and child_node.option_names:
          return RetVals(status=success, next_destination=child_node, next_menu_item=null)
        # Leaf option — remember source menu and return target + menu_item tuple
        user._source_menu = node
        info = node.options_info.get(chosen)
        if info and info.template:
          mi = _resolve_menu_item_template(info.template, {
            'parent_name': node.name, 'parent_conf': None,
            'self_name': chosen, 'self_conf': info.conf,
          })
        else:
          mi = (chosen,)
        target = info.target if info else chosen.lower()
        return RetVals(status=success, next_destination=_resolve_destination(target, menu_name),
                       next_menu_item=mi)

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

      # /chat <user> — run one-on-one chat as an overlay so the menu is
      # restored when the chat ends.
      if lower.startswith("/chat "):
        rest = option_text.split(" ", 1)
        if len(rest) < 2 or not rest[1].strip():
          if await _err("Usage: /chat <user>"): continue
          else: error_msg = "Usage: /chat <user>"
          continue
        target_handle = rest[1].strip()
        from oneonone import chat_with
        from input_output import push_screen, pop_screen
        await push_screen(user)
        try:
          chat_err = await chat_with(user, target_handle)
        finally:
          try:
            await pop_screen(user)
          except Exception:
            pass
        if chat_err:
          if await _err(chat_err): continue
          else: error_msg = chat_err
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
        user._source_menu = node  # return to the menu they were viewing
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

      # /shutdown — sysop-only: graceful BBS shutdown
      if lower == "/shutdown":
        if "sysop" not in user.keys:
          if await _err("Unknown command. Try /jump, /page, /chat, /info, /quit"): continue
          else: error_msg = "Unknown command. Try /jump, /page, /chat, /info, /quit"
          continue
        from common import shutdown_bbs
        await shutdown_bbs(f"Shutdown by sysop {user.handle}")
        return RetVals(status=success, next_destination=Destinations.logout, next_menu_item=null)

      # /crash — sysop-only test command to trigger a traceback popup
      if lower == "/crash":
        if "sysop" not in user.keys:
          if await _err("Unknown command: /crash. Try /jump, /page, /chat, /info, /quit"): continue
          else: error_msg = "Unknown command: /crash. Try /jump, /page, /chat, /info, /quit"
          continue
        raise RuntimeError("Test crash triggered by /crash command.")

      # /testpopups — sysop-only: queue several popups to test queueing
      if lower == "/testpopups":
        if "sysop" not in user.keys:
          if await _err("Unknown command. Try /jump, /page, /chat, /info, /quit"): continue
          else: error_msg = "Unknown command. Try /jump, /page, /chat, /info, /quit"
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
        msg = f"Unknown command: {option_text.split()[0]}. Try /jump, /page, /chat, /info, /quit"
        if await _err(msg): continue
        else: error_msg = msg
        continue

      # Dotted path: resolve relative to current menu
      if "." in option_text:
        dest_name, menu_item_name, parent_name, err = resolve_dotted(menu_name, option_text)
        if dest_name:
          # Set source menu: walk from the parent menu node through the path
          parent_node = _menu_nodes.get(parent_name, node) if parent_name else node
          if isinstance(menu_item_name, tuple) and len(menu_item_name) > 1:
            walk = parent_node
            for part in menu_item_name[:-1]:
              if part in walk.children:
                walk = walk.children[part]
            user._source_menu = walk
          else:
            user._source_menu = parent_node
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
          return _exit_menu(user, node, Destinations)
        # Sub-menu? Return the child node as destination for user_director
        child_node = node.children.get(chosen)
        if child_node and child_node.option_names:
          return RetVals(status=success, next_destination=child_node, next_menu_item=null)
        # Leaf option — remember source menu and return target + menu_item tuple
        user._source_menu = node
        info = node.options_info.get(chosen)
        if info and info.template:
          mi = _resolve_menu_item_template(info.template, {
            'parent_name': node.name, 'parent_conf': None,
            'self_name': chosen, 'self_conf': info.conf,
          })
        else:
          mi = (chosen,)
        target = info.target if info else chosen.lower()
        return RetVals(status=success, next_destination=_resolve_destination(target, menu_name),
                       next_menu_item=mi)

      # x, xx, xxx, etc. — go up N levels (1 x = eXit, 2 = two levels, etc.)
      if len(option_text) >= 1 and option_text.lower() == "x" * len(option_text):
        return _exit_menu(user, node, Destinations, levels=len(option_text))

      if await _err(err_msg): continue
      else: error_msg = err_msg

  finally:
    # Disable mouse click reporting
    user.writer.write("\x1b[?1002l\x1b[?1000l")
    user.mouse_reporting = False
    await user.writer.drain()
