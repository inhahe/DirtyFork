# DirtyFork BBS — Design

What the BBS does and how it is built inside. For setting it up and configuring it (keys, menus, doors, modules, terminals, modems), see [DOCS.md](DOCS.md); this file covers the internals behind those features and is where to look before a change whose effects leave the file being edited.

## Features

Each links to the part of DOCS.md that describes its configuration.

- **Connections**: telnet (`telnetlib3`) and dial-up modems (`pyserial-asyncio`, several serial ports). [Modem Support](DOCS.md#modem-support-experimental)
- **Terminals**: encoding detection (CP437 or UTF-8) and screen-size detection; ANSI output with tracked cursor and colour state. [Terminal and Encoding](DOCS.md#terminal-and-encoding)
- **Login and registration**: an inline registration form whose fields and rules come from `register.yaml`. [Registration](DOCS.md#registration)
- **Menus**: prefix matching, `x` to exit levels, dotted paths, `/jump`, and a per-user start destination. [Menu System](DOCS.md#menu-system)
- **Access control**: keys (white/black lists per destination), recursive key groups, and banned users. [Access Control](DOCS.md#access-control)
- **Door games**: DOS doors in DOSBox-X over a null-modem link, and native doors over a socket or stdio. Also covers node management, the common dropfiles (DOOR.SYS, DORINFO, CHAIN.TXT, DOOR32.SYS and more), category menus, daily maintenance commands and a sysop DOS shell. [Door Games](DOCS.md#door-games)
- **Forums, private messages, teleconference, file library** (ZMODEM/YMODEM-G), **user settings, sysop panel**. [Modules](DOCS.md#modules)
- **Popups and pages** between users, queued, with per-user permissions. [Popup System](DOCS.md#popup-system)
- **Idle timeout** with an "are you still there?" warning. [Idle Timeout](DOCS.md#idle-timeout)
- **Ambient stars** twinkling in the empty parts of the screen. [Ambient Stars](DOCS.md#ambient-stars)

## Architecture Overview

DirtyFork is an async Python BBS. Each client connection spawns an async `user_loop` that detects the terminal, handles login/registration, then enters the main routing loop.

```
DirtyFork.py: main()
  ├─ telnetlib3.create_server(shell=user_loop)    — telnet listener
  ├─ modem_listener(port, baudrate, init_string)   — one per serial port (if configured)
  │
  └─ user_loop(reader, writer, connection_type) per connection:
      ├─ _IdleMonitor wraps reader for timeout/warning
      ├─ setup_terminal  — detect encoding, screen size
      ├─ login           — login or inline registration
      └─ while True:
          r = user_director(user, destination, menu_item)
          destination = r.next_destination
          menu_item   = r.next_menu_item
```

### Destination System

Every screen/feature is a **destination** — an async callable returning `RetVals(status, next_destination, next_menu_item, ...)`. Destinations are defined in `DirtyFork.yaml` under `destinations:` and auto-registered via `_DestinationRegistry.__getattr__`:

| Type | Behavior |
|------|----------|
| `menu` | Renders a menu via `menu.do_menu()` |
| `module` | Calls `modulename.run(user, dest_conf, menu_item)` |
| `func` | Calls a built-in function (login, logout, user_director) |

Modules are imported by `modules.py` for every `destinations` entry with `type: module`.

### Menu-to-Module Pattern

Features that have both a selection menu and a handler module follow a naming convention:

| Feature | Menu destination (plural) | Module destination (singular) | Python file |
|---------|--------------------------|------------------------------|-------------|
| Doors | `doors` (type: menu) | `door` (type: module) | `door.py` |
| Forums | `forums` (type: menu) | `forum` (type: module) | `forum.py` |
| Files | `files` (type: menu) | `file` (type: module) | `file.py` |
| Sysop | `sysop` (type: menu) | `sysop_module` (type: module) | `sysop_module.py` |

Menu options specify `option_defaults: {target: <module_dest>}`. When the user selects an option, the menu returns `next_destination` pointing to the module, and `next_menu_item` set to the option name. The module looks up the option's config to determine the action.

### user_director (Central Routing)

All destination transitions go through `user_director`, which:
1. Resets mouse reporting (forced: a door's output reaches the terminal untracked) and colors
2. Checks access keys: `check_keys` on the destination, and `check_menu_keys` for a submenu reached as a `MenuNode`
3. On denied: shows a popup and finds a fallback destination
4. On allowed: calls the destination
5. On exception: logs the error, shows a popup, finds a fallback
6. Records the visit in `user.destination_history`

## Configuration internals

- **System config**: `DirtyFork.yaml`, loaded at startup via `get_config(path=..., main=True)`
- **Per-user config**: `user_configs/{handle}.yaml`, loaded on login into `user.conf`
- **Config** objects are defaultdict-based with lazy `{variable}` interpolation and environment variable expansion
- **ConfigView**: read-only overlay of multiple Config layers (user settings > defaults > null sentinel)
- The **`null`** sentinel (from `definitions.py`) is falsy and returns itself on attribute access, replacing None throughout the codebase
- `paths.py` resolves each path against the project directory or the data directory (`--data-dir`); which is which is listed in [DOCS.md](DOCS.md#path-resolution-project-vs-data-directory)
- What lives in the SQLite database (anything queried across users) and what in each user's YAML (read only while they are logged in) is listed in [DOCS.md](DOCS.md#database-vs-yaml)

## Menus and key enforcement

`menu._ensure_menu_tree()` builds one `MenuNode` per `menu_system` entry (`_menu_nodes`, by menu name):

1. one node per menu, with its options, their targets and their shortest unique prefixes;
2. an option whose target is another menu links that menu as a child (`MenuNode.parent` is the last menu found linking to it; a menu can be listed in several);
3. a menu whose `option_defaults` has `options` (e.g. each forum's actions) gets a generated child node per option.

Keys live on destinations (`destinations.<menu>.white_keys/black_keys`). Navigating into a submenu goes through `user_director`, which checks them. A path skips that, so path resolution collects the menus it passes:

- `_resolve_greedy` resolves a dotted path greedily, longest literal match first, so option names may contain dots. It returns `(dest, menu_item, parent, error, route)`, where `route` is the `MenuNode`s whose options the path went through.
- `resolve_jump` (for `/jump` and start destinations) and `resolve_dotted` (for a dotted path typed at a menu) return that route. `route_denied(user, route)` checks each menu on it with `common.check_menu_keys` and returns the first refusal's message.
- A bare menu name (`/j doors_sysop`) goes through no menus of its own. `_route_to` searches every link breadth-first, from main and from menus nothing links to, for a route through menus that admit the user. If none exists, it returns a shortest route, so that `route_denied` names a menu that refuses.

The door module needs to know which menu's option was picked (two menus may list different doors under one name). `user._option_menu` records it: set by a pick in `do_menu`, and by `take_route` after a checked `/jump`, dotted path or start destination. `door._find_door_conf` looks only there.

## Door sessions

A session in `door.run()`:

1. **Find and check.** The door's option config comes from `user._option_menu`. The `door` module's keys and the entry's own `white_keys`/`black_keys` are checked.
2. **Node.** The node key is the door's normalized directory: entries sharing a `dir` share nodes. The lowest free node number is taken, within the door's `max_nodes` and the global `max_nodes`. The node directory is `doors/_nodes/<name>/node<N>`; `_node_root` names `<name>` so that no two door directories share one. A leftover directory from a crashed session is emptied first.
3. **Screen.** The launch popup, a clear screen, and a scroll region if the door has `screen_rows`.
4. **DOSBox-X.** A listener is opened on `127.0.0.1:0` before DOSBox-X starts. Then the variables and dropfiles are written, and the config is generated: C: = node directory, D: = door directory, E: = tools, COM1 = a null-modem client to the listener. The autoexec sets the clock back (`date_shift_years`), runs the FOSSIL driver, the daily commands (when due) and `pre_commands`, each `CALL`ed so batch files return, then the door command and `exit`. `_wait_for_dosbox` waits for the connection, for DOSBox-X to exit, or for 60 seconds.
5. **Bridge.** `_run_until_first_done` runs three tasks:
   - the caller-to-door pump (`_DoorInput`: Ctrl+X three times aborts; DOORWAY key translation; input pacing);
   - the door-to-caller pump, which rewrites clear-screen to clear-and-home (`_DoorOutput`), feeds the ANSI emulator (`user.screen`, so popups can restore the door's screen) and writes `session<N>.log` through `_SessionLog`, which never raises;
   - a process watch.

   Each pump reports `ENDED_BY_DOOR` or `ENDED_BY_CALLER`. When the door ends first, the output pump gets up to 2 s to deliver the last screen. The tasks are cancelled however the bridge ends, cancellation of the session included.
6. **Stop.** The door gets 1 s to exit by itself if it ended the session. If the caller hung up or aborted, the closed connection is the door's carrier drop, and it gets 10 s to save the player. After that it is terminated.
7. **Cleanup** (in a `finally`, each step even if an earlier wait was interrupted): the process is stopped and killed if need be, the node is released, the listener and logs are closed, DOSBox-X's output is logged, the daily mark is settled, and the node directory is removed. The scroll region is reset. The caller returns to the menu the door was picked from.

Native doors skip DOSBox-X. A socket door (`DOOR32.SYS`) is bridged over TCP, and a stdio door over its pipes.

**Daily mark.** `daily.stamp` in the door's node root holds the date the daily commands last ran. It is checked and written with no await in between, so two sessions starting at once can't both run them. The autoexec writes `C:\DAILYOK.FLG` once they finish. `_settle_daily_mark` keeps the stamp if that flag exists. Otherwise it removes the stamp and logs a warning: the next session runs them again, possibly after an interrupted run.

## Terminal output

### ANSI State Tracking

The BBS tracks cursor position and color state precisely:

- `cur_*` properties reflect the actual terminal state (updated only by the `input_output.py` functions that write the sequences: `send()`, `ansi_move()`, `ansi_move_2()`, `ansi_cls()`, `ansi_set_region()`, `_ansi_color_write()`, `ansi_hide_cursor()`/`ansi_show_cursor()`)
- `new_*` properties stage pending changes (set by `ansi_move_deferred()`, `ansi_color()`)
- `send()` compares new vs cur and emits minimal escape codes; `ansi_clear_line_end()` applies pending changes the same way before clearing the rest of the row
- After text that fills a row to the last column, the cursor's position differs between terminals (deferred or immediate wrap): it is tracked as the start of the next row with `_wrap_ambiguous` set, and the next move is sent as an absolute position
- Mouse reporting is switched with `ansi_mouse_reporting()`, which tracks it in `user.mouse_reporting`
- Raw ANSI writes and manual `cur_*` assignments are never used directly (the one exception, the screen-size probe in `setup_terminal`, runs before there is a screen to track)
- `user.write_lock` (re-entrant) serializes writes to `user.writer`, so background tasks such as the stars never interleave with other output

### Screen Buffer

An ANSI emulator (`ansi_emulator.py`) maintains `user.screen` — a character-by-character copy of what the terminal displays. This is used for:
- Saving/restoring screen around popups
- Tracking door game output
- Ambient stars: a star only appears in a cell the copy shows as an empty, default-colour space

### Ambient Stars

`stars.stars_loop` runs per connection. It reads the settings on every tick: the system's `stars.enabled` is the master switch, and a user's `show_stars` can only turn stars off. Stars still on screen are erased when they switch off. Each tick draws under `user.write_lock`, inside `input_output.cursor_preserved`, which saves and restores the tracked cursor, the colours (both current and pending), a staged move, the wrap state and the cursor's visibility, so the BBS's own output is undisturbed; popups (`show_message_box`) restore the same state with `save_cursor`/`restore_cursor`. New stars are sampled with geometric gaps (`_chosen_cells`) rather than with a random number per cell. `ansi_cls` calls a hook that repaints the stars still active, and nothing is drawn while the caller is in a door.

## Modem connections

1. `modem_listener()` opens the serial port and sends the init string (default `ATZ`)
2. Disables auto-answer (`ATS0=0`) so calls are answered manually
3. Waits for `RING`
4. Answers with `ATA` and waits for `CONNECT`
5. On connect, wraps the serial reader/writer in adapter classes (`SerialReader`/`SerialWriter`) that match the telnetlib3 interface
6. Spawns a `user_loop` with `connection_type="modem"`
7. On disconnect, sends `+++` pause then `ATH` to hang up
8. Returns to waiting for the next `RING`

`SerialReader` and `SerialWriter` in `modem.py` provide the same interface as telnetlib3's reader/writer: `write(data)`, `drain()`, `close()`, `get_extra_info()` on the writer and `read(n)` on the reader. Modem terminals auto-detect as `ansi-bbs` (CP437 encoding). Each configured port gets its own `modem_listener` task.

## Idle timeout

The `_IdleMonitor` class wraps the reader's `read()` method — the single entry point for all user input (menus, input fields, doors, teleconference, file transfers). This means timeouts work everywhere without any per-module code. The warning popup's own input loop calls `read()` recursively; the monitor detects this via an `_in_warning` flag and does a plain timed wait without showing another popup. If the user has no screen yet (before terminal detection), the warning falls back to raw text.

## Input Field System

The `InputFields` system provides form-based input:

- **InputField**: text input with optional outline, fill character, word wrap, and quote margins
- **InputFields**: form container managing multiple fields and named buttons
- **Buttons**: non-editable fields that return immediately on arrow keys
- **Block**: structured quoted content with text and quote level (level 0 = user text, 1+ = quoted); forum posts store their body as JSON-serialized Blocks
- **Mouse support**: click-to-focus fields and buttons, scrollbar interaction

### show_message_box

Modal popup with:
- Vertical and horizontal scrollbars
- Word wrapping (configurable, can be disabled for code/tracebacks)
- Screen save/restore
- Mouse click support (close button, scrollbars)
- Queue-aware "Abort All" option

Popups that arrive while one is showing wait in `user.popup_queue`; `check_can_page()` decides whether one may be delivered at all.

## Tests

Plain `unittest`, in `tests/`. Run from the project directory, with the BBS's Python environment:

```
python -m unittest discover -s tests
```

They load the shipped `DirtyFork.yaml` (as on a fresh clone) with a scratch data directory that is removed afterwards, and need no network, DOSBox or door files. Covered: door node directories, the generated autoexec and dropfiles, the daily mark, the door I/O pumps and process handling, menu keys on `/jump`, dotted paths and jumps to a menu by name, the text menu's prompt line, the escape-sequence helpers, and the ambient stars.

## File Manifest

| File | Purpose |
|------|---------|
| `DirtyFork.py` | Main entry point, event loop |
| `common.py` | User class, Destinations registry, user_director, login, expand_keys, check_menu_keys |
| `config.py` | Config/ConfigView, get_config() |
| `definitions.py` | Constants, RetVals, Estr/Eint, Char, Null, Disconnected |
| `input_output.py` | ANSI I/O, state tracking, send/ansi_move/ansi_color, mouse reporting, screen save/restore |
| `input_fields.py` | InputField/InputFields, show_message_box, Block |
| `keyboard_codes.py` | Key code mapping, mouse/position parsing |
| `menu.py` | Menu tree, rendering, prefix matching, resolve_jump/resolve_dotted, route checks, multi-column layout |
| `door.py` | Door games, node management, dropfiles, DOSBox-X config, I/O bridge |
| `teleconference.py` | Multi-channel chat, split-screen |
| `forum.py` | Forum module |
| `file.py` | File library, search/browse/upload/download |
| `register.py` | New user registration |
| `settings.py` | User settings page (shared with sysop) |
| `sysop_module.py` | Sysop panel: user keys, key groups, user settings |
| `bbs_msg.py` | Popup messages, permission checks, queueing |
| `ansi_emulator.py` | ANSI parser for door output, screen buffer |
| `file_transfer.py` | ZMODEM/YMODEM async wrappers |
| `lib/` | The vendored protocol libraries: `modem` (ZMODEM) and `ymodem` (YMODEM-G); where they came from is in `lib/README.md` |
| `logger.py` | Rotating file logging |
| `modem.py` | Serial/modem adapter classes and AT command handling |
| `modules.py` | Dynamic module loader |
| `paths.py` | Path resolution (project vs data directory) |
| `stars.py` | Ambient star animation |
| `tests/` | Unit tests (`python -m unittest discover -s tests`) |
