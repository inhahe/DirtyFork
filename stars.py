"""Ambient ANSI star animation.

Runs as a background task per user, from the login screen on. On each tick,
advances every active star one frame, then independently spawns new stars in
eligible cells with configurable per-cell probability. A cell is eligible iff
its model entry is a default-attribute space (' ', white-on-black, no brights)
and is not the user's current cursor position. This naturally excludes typed
text, input fields with non-black fills, popups, menus — anything visible.

Whether stars show is decided afresh on every poll: only if the system-wide
`stars.enabled` is on, and not for a user whose `show_stars` is off (read once
the user has logged in), and never while the user is in a door. When stars stop showing, the ones
still on screen are erased (except in a door, which owns the screen).

The animation acquires user.write_lock for the duration of each frame so
its writes don't interleave with the main coroutine's renders.
"""

import asyncio
import math
import random

from definitions import white, black, blue
from input_output import ansi_move, ansi_color, send, cursor_preserved
from logger import log
from config import get_config

_sys_config = get_config()


# CP437 frame progression:
#   chr 250 ·  small middle dot
#   chr 249 ∙  bullet operator
#   chr 42  *  asterisk
#   chr 15  ☼  sun (snowflake stand-in)
# Bytes 0x0f and similar are auto-translated to their visible Unicode glyphs
# by send() on UTF-8 terminals.
_FRAMES = [
  bytes([250]).decode('cp437'),
  bytes([249]).decode('cp437'),
  '*',
  bytes([15]).decode('cp437'),
  '*',
  bytes([249]).decode('cp437'),
  bytes([250]).decode('cp437'),
]

# Defaults. Stars are OFF by default: the sysop turns them on with the system
# yaml's `stars:` block, and a user can then turn them off with `show_stars`.
DEFAULT_ENABLED = False
DEFAULT_INTERVAL_MS = 200      # average per-star frame interval
DEFAULT_PROBABILITY = 0.0003   # per-cell spawn probability per frame interval
DEFAULT_FG = blue
DEFAULT_FG_BR = True

# Polling rate of the background task. Smaller = finer-grained per-star
# scheduling, but more CPU. 50ms is plenty for visual smoothness.
_POLL_MS = 50
# While stars aren't showing (off, in a door), it only has to notice when they
# should start again.
_IDLE_POLL_MS = 500

# A star is the tuple (row, col, frame_index, next_advance_time, fg, fg_br):
# 1-based screen position, index into _FRAMES of the frame now on screen,
# event-loop time of its next frame, and the colour it was drawn in.


def _is_default_cell(ch):
  return (ch.char == ' ' and ch.fg == white and not ch.fg_br
          and ch.bg == black and not ch.bg_br)


def _matches_star(ch, frame_char, fg, fg_br):
  return (ch.char == frame_char and ch.fg == fg and ch.fg_br == fg_br
          and ch.bg == black and not ch.bg_br)


def _read_setting(source, name, default, cast):
  if not source:
    return default
  try:
    val = getattr(source, name)
  except Exception:
    return default
  if val is None:
    return default
  # ConfigView's null sentinel is falsy and returns self on attribute access
  try:
    if not val and not isinstance(val, (int, float)):
      return default
  except Exception:
    pass
  try:
    return cast(val)
  except Exception:
    return default


def _bool_cast(v):
  if isinstance(v, bool):
    return v
  return str(v).strip().lower() not in ('false', 'no', '0', 'off', '')


def _settings(user):
  """The star settings in force for *user* right now.

  Returns (enabled, fg, fg_br, interval_ms, probability).  enabled is the
  system-wide `stars.enabled`, and false for a user whose show_stars is off:
  a user can turn stars off, not on.  fg and fg_br are the system-wide values,
  overridden by the user's stars_fg / stars_fg_br.  The user settings apply
  once they have logged in (before login user.conf doesn't exist).
  interval_ms and probability are system-only.
  """
  sys_stars = getattr(_sys_config, 'stars', None)
  conf = getattr(user, 'conf', None)
  sys_enabled = _read_setting(sys_stars, 'enabled', DEFAULT_ENABLED, _bool_cast)
  sys_fg = _read_setting(sys_stars, 'fg', DEFAULT_FG, int)
  sys_fg_br = _read_setting(sys_stars, 'fg_br', DEFAULT_FG_BR, _bool_cast)
  return (
    sys_enabled and _read_setting(conf, 'show_stars', True, _bool_cast),
    _read_setting(conf, 'stars_fg', sys_fg, int),
    _read_setting(conf, 'stars_fg_br', sys_fg_br, _bool_cast),
    _read_setting(sys_stars, 'interval', DEFAULT_INTERVAL_MS, int),
    _read_setting(sys_stars, 'probability', DEFAULT_PROBABILITY, float),
  )


def _showing(user, enabled):
  """True if stars may be drawn now: *enabled* (from _settings), the user is
  not in a door, and the screen size is known."""
  return bool(enabled and not user.in_door and user.screen and user.screen_width)


async def _draw(user, r, c, char, fg, fg_br):
  """Write *char* at (r, c) in fg on black.  Caller holds the write lock."""
  await ansi_move(user, r, c, drain=False)
  ansi_color(user, fg=fg, fg_br=fg_br, bg=black, bg_br=False)
  await send(user, char, drain=False)


def _in_bounds(user, r, c):
  height = len(user.screen)
  width = len(user.screen[0]) if height else 0
  return 1 <= r <= height and 1 <= c <= width


async def _repaint_after_cls(user):
  """Post-cls hook: repaint active stars onto the freshly-cleared screen.
  Called from ansi_cls inside its lock, so no extra locking is needed."""
  active = getattr(user, '_stars_active', None)
  if not active or not user.screen:
    return
  # The settings may have changed since the last poll (e.g. logging in loads
  # the user's show_stars): only repaint if stars are still to be shown.
  if not _showing(user, _settings(user)[0]):
    active.clear()  # the screen was just cleared, so there is nothing to erase
    return

  height = len(user.screen)
  width = len(user.screen[0]) if height else 0
  surviving = []
  async with cursor_preserved(user):
    for star in active:
      r, c, idx, next_at, star_fg, star_fg_br = star
      if not _in_bounds(user, r, c) or (r == height and c == width) or idx >= len(_FRAMES):
        continue  # (never write the bottom-right cell: it can scroll on autowrap)
      await _draw(user, r, c, _FRAMES[idx], star_fg, star_fg_br)
      surviving.append(star)
    active[:] = surviving


async def _erase(user, active):
  """Erase the stars in *active* that are still on screen, then forget them all.
  A cell that no longer shows its star's frame was overwritten by something
  else and is left alone.  Caller holds the write lock."""
  async with cursor_preserved(user, hide_cursor=True):
    for r, c, idx, next_at, star_fg, star_fg_br in active:
      if (_in_bounds(user, r, c) and idx < len(_FRAMES)
          and _matches_star(user.screen[r-1][c-1], _FRAMES[idx], star_fg, star_fg_br)):
        await _draw(user, r, c, ' ', white, False)
  active.clear()


async def stars_loop(user):
  """Background task that animates ambient stars on the user's screen.
  Cancel this task to stop the animation cleanly."""
  if not hasattr(user, '_stars_active') or user._stars_active is None:
    user._stars_active = []  # list of stars (see the tuple layout above)
  active = user._stars_active
  user._post_cls_hook = _repaint_after_cls
  showing = False
  try:
    while True:
      await asyncio.sleep((_POLL_MS if showing else _IDLE_POLL_MS) / 1000.0)
      enabled, fg, fg_br, interval_ms, probability = _settings(user)
      showing = _showing(user, enabled)

      if not showing:
        if active:
          if user.in_door or not user.screen:
            active.clear()  # the door owns the screen (and clears it when it starts)
          else:
            async with user.write_lock:
              await _erase(user, active)
        continue

      # Per-poll spawn probability is scaled so the per-frame-interval
      # spawn rate matches the configured `probability`.
      spawn_p = probability * (_POLL_MS / max(1, interval_ms))

      try:
        async with user.write_lock:
          await _tick(user, active, fg, fg_br, spawn_p, interval_ms)
      except asyncio.CancelledError:
        raise
      except Exception as e:
        log.error("stars: tick error for user %s: %s", getattr(user, 'handle', '?'), e)
        await asyncio.sleep(1.0)
  except asyncio.CancelledError:
    pass


def _chosen_cells(n, p):
  """Yield, in increasing order, the indices in range(n) that a Bernoulli(p)
  trial per index would pick, without drawing a random number per index:
  the gap to the next pick is geometrically distributed.  A p that is not a
  positive number (0, negative, NaN) picks nothing."""
  if not p > 0:
    return
  if p >= 1:
    yield from range(n)
    return
  log_q = math.log1p(-p)
  i = -1
  while True:
    # 1 - random() is in (0, 1]; a tiny p makes the gap huge or infinite
    gap = math.log(1.0 - random.random()) / log_q
    if not gap < n - i:
      return
    i += 1 + int(gap)
    if i >= n:
      return
    yield i


def _first_advance_time(now, frame_interval_ms):
  """Random first-advance time uniformly within one frame interval, so
  newly-spawned stars get phases uniformly distributed across the cycle."""
  return now + random.uniform(0.0, frame_interval_ms / 1000.0)


def _next_advance_time(now, frame_interval_ms):
  """Subsequent per-star advance time — fixed at one frame interval.
  The initial random offset (from _first_advance_time) preserves phase
  diversity across all subsequent advances."""
  return now + frame_interval_ms / 1000.0


async def _tick(user, active, fg, fg_br, spawn_p, frame_interval_ms):
  """Run one polling tick. Caller holds user.write_lock.
  Each star has its own next_advance_at; only stars whose time has come
  actually advance this tick. Spawn probability is per-cell-per-poll."""
  height = len(user.screen)
  width = len(user.screen[0]) if height else 0
  if width == 0 or height == 0:
    return

  now = asyncio.get_event_loop().time()
  cur_row, cur_col = user.cur_row, user.cur_col

  async with cursor_preserved(user, hide_cursor=True):
    # --- 1) Advance stars whose time has come ---
    survivors = []
    for star in active:
      r, c, idx, next_at, star_fg, star_fg_br = star
      if not _in_bounds(user, r, c):
        continue

      if now < next_at:
        survivors.append(star)
        continue

      if not _matches_star(user.screen[r-1][c-1], _FRAMES[idx], star_fg, star_fg_br):
        continue  # cell was overwritten by something else; abandon

      next_idx = idx + 1
      if next_idx >= len(_FRAMES):
        # Star is done — restore the cell to a default-attr space
        await _draw(user, r, c, ' ', white, False)
      else:
        await _draw(user, r, c, _FRAMES[next_idx], star_fg, star_fg_br)
        survivors.append((r, c, next_idx, _next_advance_time(now, frame_interval_ms),
                          star_fg, star_fg_br))

    # --- 2) Spawn new stars: every eligible cell independently with spawn_p ---
    first_char = _FRAMES[0]
    for i in _chosen_cells(height * width, spawn_p):
      r, c = divmod(i, width)
      r += 1
      c += 1
      # Skip the bottom-right cell (writing there can scroll on autowrap)
      # and the user's current cursor cell
      if (r == height and c == width) or (r == cur_row and c == cur_col):
        continue
      if not _is_default_cell(user.screen[r-1][c-1]):
        continue
      await _draw(user, r, c, first_char, fg, fg_br)
      survivors.append((r, c, 0, _first_advance_time(now, frame_interval_ms), fg, fg_br))

    # Replace active list in place so the caller's reference stays valid
    active[:] = survivors
