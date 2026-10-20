# DirtyFork BBS — Documentation

## Architecture Overview

DirtyFork is an async Python BBS supporting both telnet (via `telnetlib3`) and dial-up modem (via `pyserial-asyncio`) connections. Each client connection spawns an async `user_loop` that detects the terminal, handles login/registration, then enters the main routing loop.

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

### Menu-to-Module Pattern

Features that have both a selection menu and a handler module follow a naming convention:

| Feature | Menu destination (plural) | Module destination (singular) | Python file |
|---------|--------------------------|------------------------------|-------------|
| Doors | `doors` (type: menu) | `door` (type: module) | `door.py` |
| Forums | `forums` (type: menu) | `forum` (type: module) | `forum.py` |
| Files | `files` (type: menu) | `file` (type: module) | `file.py` |
| Sysop | `sysop` (type: menu) | `sysop_module` (type: module) | `sysop_module.py` |

Menu options specify `option_defaults: {target: <module_dest>}`. When the user selects an option, the menu returns `next_destination` pointing to the module, and `next_menu_item` set to the option name (a string). The module looks up the option's config to determine the action.

### user_director (Central Routing)

All destination transitions go through `user_director`, which:
1. Resets mouse reporting and colors
2. Checks access keys (`check_keys`)
3. On denied: shows a popup and finds a fallback destination
4. On allowed: calls the destination
5. On exception: logs the error, shows a popup, finds a fallback
6. Records the visit in `user.destination_history`

---

## Configuration

### Config System

- **System config**: `DirtyFork.yaml`, loaded at startup via `get_config(path=..., main=True)`
- **Per-user config**: `user_configs/{handle}.yaml`, loaded on login into `user.conf`
- **Config** objects are defaultdict-based with lazy `{variable}` interpolation and environment variable expansion
- **ConfigView**: read-only overlay of multiple Config layers (user settings > defaults > null sentinel)
- The **`null`** sentinel (from `definitions.py`) is falsy and returns itself on attribute access, replacing None throughout the codebase

### Key Settings

```yaml
bbs_name: My BBS
hostname: 0.0.0.0
port: 23

database: DirtyFork.db
files_dir: files
user_configs: user_configs

destinations:
  door:
    dosbox_path: C:\dosbox-x\dosbox-x.exe
    base_path: doors
    max_nodes: 20
```

Top-level values like `bbs_name` are available as `{bbs_name}` placeholders anywhere in the config.

### Database vs YAML

- **SQLite database**: credentials (handle, password_hash), keys (USER_KEYS table), messages, forum posts — anything queried across users
- **User YAML** (`user_configs/{handle}.yaml`): profile (email, age, bio), preferences (encoding, scroll_step, allow_door_popups, blocked_users, start_destination, show_stars) — loaded only for the logged-in user

### Path Resolution: Project vs Data Directory

When using `--data-dir`, paths are resolved relative to either the **project directory** (where the BBS source files are) or the **data directory** (the `--data-dir` path). This allows multiple BBS instances to share the same installation but have separate databases and user data.

**Project-relative** (shared installation, same for all instances):
- `doors/` — door game binaries and configs
- `files/` — file library for download
- `files/meta.yaml` — file metadata
- `register.yaml` — registration form definition
- `input_fields.yaml` — input field styles
- ANSI/BIN screen files (`bbs_info_screen`, etc.)

**Data-relative** (per-instance, varies by `--data-dir`):
- `DirtyFork.yaml` — main config
- `DirtyFork.db` — SQLite database
- `DirtyFork.log` — log file
- `teleconference.log` — teleconference chat log (if enabled)
- `user_configs/` — per-user YAML profiles

If a path is absolute, it's used as-is regardless of the directory type.

---

## Access Control

### Keys

Users have a set of **keys** (stored in the `USER_KEYS` database table). Destinations define access rules:

- **`white_keys`**: user must have ALL listed keys
- **`black_keys`**: user must have NONE of listed keys

```yaml
destinations:
  doors:
    white_keys: [doors]    # must have "doors" key
    black_keys: [banned]   # must NOT have "banned" key
```

The rules also apply to menus entered as a submenu of another menu (e.g. a door category, or the Sysop menu from Main). A door checks the keys of the menu it is listed in, and of the menus above that, when it starts, so `/jump` or a dotted path straight to a door can't get around its category's keys. Door entries can additionally carry their own `white_keys`/`black_keys`, which the door module enforces for that door only.

New users receive default keys from `user_defaults.keys` in the config (e.g., `[doors]`).

### Key Groups

Key groups let a single key grant membership to multiple other keys, with recursive expansion. Defined in the config:

```yaml
key_groups:
  sysop:
  - doors
  - debug
```

A user with the `sysop` key automatically receives `doors` and `debug` too. Groups can include other groups — expansion is recursive via `expand_keys()` in `common.py`. Keys are expanded at login and whenever the sysop modifies keys or groups at runtime.

### Banned Users

The `banned` key is a special key. After login, if a user's expanded key set contains `banned`, they are immediately logged out with a message. This avoids needing to add `banned` to every destination's `black_keys`.

---

## Menu System

### Prefix Matching

Menus calculate the shortest unique prefix for each option. Users can type any unambiguous prefix to select an option:

- `m` for "Messages" (if no other option starts with M)
- `fo` for "Forums" (if "Files" also exists)
- Ambiguous input shows: "Ambiguous: 'f' matches Files, Forums. Type more letters."

### Navigation

- **`x`** exits the current menu (returns to parent)
- **`xx`**, **`xxx`**, etc. exit multiple levels
- **`x`** at the main menu logs out

### Jump Command

The `/jump` (or `/j`) command navigates directly to any destination using dotted paths:

```
/j forums.philosophy     → opens the Philosophy forum
/j doors                 → opens the Doors menu
/j files.search          → opens the file search
```

`resolve_jump()` walks the menu tree, matching each segment by prefix. Errors show which segment failed and what options are available.

### Start Destination

Users can set a `start_destination` in their settings (using `/jump` syntax). After login, the BBS sends them directly to that destination instead of the main menu. Configured via the Settings page.

---

## Modules

### Door Games

Door games run in DOSBox-X instances with full node management. Each session gets its own node directory with auto-generated dropfiles.

**Configuration.** A door is any menu option whose target is the `door` module, so doors can be grouped into category submenus. The `doors` menu lists the categories; each category is its own menu (with its own `destinations` entry, `type: menu`) and an optional `title` used in the breadcrumb (`Main > Doors > Most Popular`). The same door can be listed in several categories with a YAML alias; entries that share a `dir` share one set of nodes. After a door exits, the user returns to the menu it was launched from.

```yaml
destinations:
  door:
    type: module
    white_keys: [doors]
    dosbox_path: C:\dosbox-x\dosbox-x.exe
    base_path: doors          # door dirs are relative to this (under the project dir)
    tools_path: tools         # mounted as E: in every door session
    fossil_command: X00.EXE   # run from E:\ for doors with fossil: true
  doors_popular: {type: menu, white_keys: [doors]}
  doors_space:   {type: menu, white_keys: [doors]}

menu_system:
  doors:
    options:
      Most Popular: {target: doors_popular}
      Space:        {target: doors_space}
  doors_popular:
    title: Most Popular
    option_defaults: &door_defaults
      target: door
      dosbox_conf: doors/dosbox.conf
    options:
      Trade Wars 2002: &door_tw2002
        max_nodes: 4
        command: 'TW2002.EXE TWNODE={node}'
        dir: 'tw2002'
  doors_space:
    title: Space
    option_defaults: *door_defaults
    options:
      Trade Wars 2002: *door_tw2002
```

**Per-door options** (besides `command`, `dir`, `max_nodes`):

| Option | Meaning |
|--------|---------|
| `fossil: true` | Load the FOSSIL driver (`fossil_command`, from `E:\`) before the door. Doors with their own serial routines don't need it. |
| `pre_commands: [...]` | DOS commands run from `D:\` before the door (e.g. a dropfile converter, or deleting a stale lock file of a one-node door). Each is `CALL`ed, so a batch file among them returns. |
| `dosbox_settings: {cpu: {cycles: 20000}}` | Per-door DOSBox-X settings, layered over `dosbox_conf`. |
| `date_shift_years: 28` | Run the door's clock N years in the past, for doors with Y2K bugs. Multiples of 28 keep the weekdays and leap years of the real calendar, and the date still advances daily. |
| `daily_commands: [...]` | DOS commands run before the door on the first session of each day only (e.g. the door's maintenance program). Entries that share a `dir` share the once-a-day mark (`daily.stamp` in the door's `doors/_nodes` directory); if that session fails to start the door, the mark is taken back. |
| `key_translation: doorway` | Translate the caller's ANSI/VT cursor, Home/End, PgUp/PgDn, Ins/Del and F1–F12 key sequences into DOORWAY's NUL + scan code, so arrow-key driven DOS programs run through DOORWAY work from any terminal. A lone ESC still reaches the program. |
| `screen_rows: 24` | For doors written for 24-line screens: the terminal's scroll region is limited to that many rows during the door (and reset afterwards), and the dropfiles report that page length. |
| `input_pace_ms: 30` | Send the caller's keys one at a time, this many ms apart, for doors that throw away typed-ahead input. |
| `white_keys` / `black_keys` | Restrict this door only (e.g. sysop-only tools, adult doors), on top of the door module's keys. |
| `door_sys: {...}`, `dorinfo: {...}`, ... | Override individual dropfile fields (see `doors/dropfiles/*.yaml`). |

Variables available in `command` and `pre_commands`: `{node}`, `{dropfile_path}` (`C:\DOOR.SYS` by default, see `dropfile_type`), `{dropfile_dir}` (`C:\`), `{handle}`, `{baud}`, `{com}`, `{mins_remaining}`, `{secs_remaining}`, `{rows}`, `{cols}`, plus any scalar from the door's config.

**Supported dropfile formats** (all written for every session): `DOOR.SYS` (52-line GAP/PCBoard/Wildcat), `DOOR<node>.SYS`, `DORINFO1.DEF` and `DORINFO<node>.DEF` (line 13 is `-1` only when `fossil: true`), `CHAIN.TXT` (32-line WWIV), `DOOR32.SYS` (11 lines; comm type 1/COM1 for DOSBox doors, 2/telnet socket for native doors), `CALLINFO.BBS`, `SFDOORS.DAT`. Field defaults are in `doors/dropfiles/*.yaml` and can be overridden per door.

**DOSBox drive mapping:**
- `C:\` — the node directory (`doors/_nodes/<dir>/node<N>`), where the dropfiles are written. It is removed when the session ends. (`<dir>` is the door's path under `base_path` with `_` doubled and separators turned into `_`; a door outside `base_path` gets its folder name plus a hash of its path.)
- `D:\` — the door's game directory (`doors/<dir>`), where the game EXE lives. The command runs from here.
- `E:\` — `tools_path` (`doors/tools`, not included): put a FOSSIL driver there (e.g. X00.EXE, for doors with `fossil: true`) and DOORWAY (`doors/tools/doorway`, for the sysop DOS shell).
- COM1 — the caller, through DOSBox-X's null-modem serial port.

Configure doors to read their dropfile from `C:\` (e.g. `C:\DOOR.SYS`) and their data from `D:\`; never put host paths in a door's own config files. If `dropfile_dir` is set, the dropfiles are also copied there before the door starts.

**Sysop DOS shell.** With DOORWAY in `doors/tools/doorway`, the sysop-only **DOS Shell** door (commented out in the *Sysop Tools* category of `DirtyFork.yaml`) gives a remote DOS prompt (through DOORWAY, which mirrors the DOSBox screen to your terminal and feeds your keys in) with `D:\` = `doors/`. Use it to run door installers and config programs (TEDIT, LORDCFG, ...) from your terminal, since DOSBox runs hidden. A config program that stores paths should be run with the same drive mapping the door has during play: give it its own sysop entry with `dir:` set to the door's directory, e.g. `command: 'E:\DOORWAY\DOORWAY.EXE COM1 /V:D /O:T /M:999 /G:ON /P:CONFIG.EXE'` (or `/C:DOS` for a prompt). DOORWAY feeds keys through the 15-key BIOS keyboard buffer, so pasting long text into it can drop characters.

**Screen handling**: the screen is cleared before a door starts. DOS doors were written for ANSI.SYS, where `ESC[2J` (and a form feed) clears the screen *and homes the cursor*; BBS terminals do the same, but VT100-style clients (PuTTY, xterm) don't, so door output has both rewritten to `ESC[2J ESC[H`, which means the same on every terminal.

**Session log**: the raw output of the most recent session on each node is kept in `doors/_nodes/<dir>/session<N>.log`, which helps when a door misbehaves.

**Cross-platform**: DOSBox/DOSBox-X runs on Linux and macOS too. The BBS generates DOSBox configs with OS-native paths, so doors work identically on all platforms. Just set `dosbox_path` to the correct binary (e.g., `/usr/bin/dosbox-x` on Linux).

**Native 32-bit doors**: Set `native: true` to run a door directly without DOSBox. Native doors default to TCP socket communication (`communication_type: SOCKET`) and find their dropfiles in the node directory (used as the working directory). STDIO pipes are also supported (`communication_type: STDIO`).

**Batch files**: Door commands that invoke `.BAT` files use `CALL` in the DOSBox autoexec so that control returns and DOSBox can exit cleanly.

**Escape**: Press **Ctrl+X three times** within 2 seconds to exit a door session. When the caller hangs up or aborts, the connection to DOSBox is closed so the door sees its carrier drop, and it gets up to 10 seconds to save the player and exit before DOSBox is terminated (a door that exits by itself is waited for 1 second). Doors that allow only one player at a time and keep a lock file (e.g. BRE's `INUSE.FLG`) can be left locked by an aborted session; with `max_nodes: 1` it is safe to delete the lock in `pre_commands`.

**Popups during doors**: The ANSI emulator tracks the door's screen state in `user.screen`. Popups save/restore this screen. Users can disable door popups via the `allow_door_popups` setting.

### Forums

Threaded discussion forums with quoting, search, and editing. Forum posts store body text as JSON-serialized Block objects (text + quote level). Forums are defined in the config under `forum_list`.

### Private Messages

Threaded private messaging with compose, search, and new-message alerts.

### Teleconference

Multi-channel real-time chat with split-screen display. Users can join channels and see messages from other users in real time.

### File Library

File management with search, browse, list, upload (ZMODEM/YMODEM-G), and download capabilities. Files are tagged with keys and descriptions via `files/meta.yaml`.

### Registration

New user registration form with configurable fields (handle, password, age, sex, location, time zone, email, bio). Registration labels, blurbs, and validation rules are defined in `register.yaml`. Time zone accepts abbreviations (EST, PST) or UTC offsets (UTC+8, UTC-5:30).

Handle allowed characters are configured in `register.yaml` using regex character class syntax:

```yaml
handle:
  # Ranges (a-z, A-X), shortcuts (\d, \w, \s),
  # escaped literals (\-, \\, \[, \]). Brackets optional.
  allowed_chars: "a-zA-Z0-9_\\-"
  # Human-readable label shown on the registration page.
  # Auto-generated from allowed_chars if omitted.
  # allowed_chars_label: "letters, numbers, underscore, dash"
```

The spec is validated at startup — if invalid, the BBS will not start.

New users automatically receive default keys from `user_defaults.keys`.

### Color Markup in Labels

Labels and other sysop-configurable text support inline color markup using `{!...}` tags:

| Tag | Effect |
|-----|--------|
| `{!red}` | Set foreground to red |
| `{!red,br}` | Bright red foreground |
| `{!white,on_blue}` | White on blue background |
| `{!nobr}` | Turn off bright foreground |
| `{!bg_br}` / `{!nobg_br}` | Toggle bright background |
| `{!}` | Reset to default colors |

Available colors: `black`, `red`, `green`, `brown`/`yellow`, `blue`, `magenta`, `cyan`, `white`/`gray`/`grey`. Use `on_` prefix for background (e.g., `on_blue`). Add `br` for bright foreground, `bg_br` for bright background.

Example in `register.yaml`:
```yaml
handle:
  label: "Handle{!red,br}*{!}: "
```

Markup tags are invisible — they don't affect label alignment or field width calculations.

### Settings

User-editable settings page for profile and preferences. The sysop can also edit any user's settings via the sysop panel. Settings include:

- Encoding (cp437/utf-8)
- Start destination
- Allow door popups
- Profile fields (email, age, location, bio, etc.)

Changes apply immediately to the user's live session if they're online.

### Sysop Panel

The sysop panel is a menu with three management tools:

- **Keys**: Look up a user by handle, view and edit their keys (comma-separated)
- **Groups**: Edit key group definitions in the config YAML (using ruamel.yaml to preserve comments). Changes reload into the live config and re-expand all online users' keys
- **Settings**: Edit any user's settings using the same settings page code

Access requires the `sysop` key group (configured in `white_keys`).

---

## Terminal and Encoding

### Encoding Detection

During connection setup, the BBS detects the terminal type via telnet TTYPE negotiation:

- Known UTF-8 terminals (xterm, vt100, linux, kitty, tmux, etc.) default to UTF-8
- Known CP437 terminals (ansi, ansi-bbs, avatar, pcansi) default to CP437
- Unknown terminals default to CP437
- User's saved encoding preference overrides auto-detection after login

### ANSI State Tracking

The BBS tracks cursor position and color state precisely:

- `cur_*` properties reflect the actual terminal state (updated only by `send()`, `ansi_move_2()`, `_ansi_color_write()`)
- `new_*` properties stage pending changes (set by `ansi_move()`, `ansi_color()`)
- `send()` compares new vs cur and emits minimal escape codes
- Raw ANSI writes and manual `cur_*` assignments are never used directly

### Screen Buffer

An ANSI emulator (`ansi_emulator.py`) maintains `user.screen` — a character-by-character copy of what the terminal displays. This is used for:
- Saving/restoring screen around popups
- Tracking door game output
- Ambient stars (below): a star only appears in a cell the copy shows as an empty, default-colour space

### Ambient Stars

`stars.py` runs a background task per connection that twinkles dim stars in the empty parts of the screen, from the login screen on. They are off unless the `stars:` block in the main config sets `enabled: true` (see the commented example in `DirtyFork.yaml`, which also sets the animation speed, density and colour). Once logged in, a user can turn them off with `show_stars: false` in their user YAML (but not on, if the sysop has them off), and override the colour with `stars_fg` / `stars_fg_br`. Stars never appear inside doors. Whether they show is checked on every animation tick, and stars still on screen are erased when they switch off; drawing takes `user.write_lock`, so it never interleaves with other output, and a screen clear repaints the stars that are still active.

---

## Modem Support (Experimental)

Modem/serial connections are supported via `pyserial-asyncio`. The BBS listens for incoming calls using standard AT commands. Multiple serial ports can be configured for multi-line setups.

**Note:** Modem support is currently untested — the developer does not have a modem.

### How It Works

1. `modem_listener()` opens the serial port and sends the init string (default `ATZ`)
2. Disables auto-answer (`ATS0=0`) so calls are answered manually
3. Waits for `RING`
4. Answers with `ATA` and waits for `CONNECT`
5. On connect, wraps the serial reader/writer in adapter classes (`SerialReader`/`SerialWriter`) that match the telnetlib3 interface
6. Spawns a `user_loop` with `connection_type="modem"`
7. On disconnect, sends `+++` pause then `ATH` to hang up
8. Returns to waiting for the next `RING`

### Adapter Classes

`SerialReader` and `SerialWriter` in `modem.py` provide the same interface as telnetlib3's reader/writer:
- `write(data)`, `drain()`, `close()`, `get_extra_info()` on the writer
- `read(n)` on the reader
- Modem terminals auto-detect as `ansi-bbs` (CP437 encoding)

### Configuration

```yaml
modem:
  baudrate: 115200        # serial port speed — 115200 is ideal because
                          # modem compression can exceed the line rate
  init_string: ATZ        # default AT init command
  idle_timeout: 300       # modem-specific idle timeout (seconds, 0 = disabled)
  ports:
    - port: COM1
    - port: COM2
    - port: COM3
      baudrate: 9600      # per-port override
      init_string: ATZ&F  # per-port override
```

Each port gets its own `modem_listener` async task. Per-port `baudrate` and `init_string` override the defaults. The legacy single-port format (`modem.port: COM1`) is also supported.

---

## Idle Timeout

Configurable inactivity timeout with an optional "are you still there?" warning popup. Separate timeout values for telnet and modem connections.

### How It Works

The `_IdleMonitor` class wraps the reader's `read()` method — the single entry point for all user input (menus, input fields, doors, teleconference, file transfers). This means timeouts work everywhere without any per-module code.

1. User is idle for `idle_timeout - idle_warning` seconds
2. A popup appears: "Are you still there? You will be disconnected in N seconds."
3. The popup saves/restores the screen — whatever was on screen is preserved
4. If the user presses any key, the timer resets and they continue normally
5. If no response during the warning period, the user is disconnected with a message

The popup's internal input loop calls `read()` recursively. The monitor detects this via an `_in_warning` flag and does a plain timed wait without showing another popup.

If the user has no screen yet (before terminal detection), the warning falls back to raw text.

### Configuration

```yaml
idle_timeout: 300         # telnet timeout in seconds (0 = disabled)
idle_warning: 30          # seconds before timeout to show warning (0 = just disconnect)

modem:
  idle_timeout: 300       # separate modem timeout
```

---

## Popup System

Popups are modal message boxes with scrolling, word wrap, and mouse support.

### Queueing

When a popup arrives while another is already showing, it's queued in `user.popup_queue`. After the current popup is dismissed, the next one shows automatically. If multiple popups are queued, the user can press **A** ("Abort All") to clear the queue.

### Permissions

Before delivering a popup, `check_can_page()` verifies:
- User has a screen and is fully connected
- `allow_pages` and `allow_bbs_messages` settings are enabled
- If in a door, `allow_door_popups` must be true
- Sender is not in the target's `blocked_users` list

---

## Input Field System

The `InputFields` system provides form-based input:

- **InputField**: text input with optional outline, fill character, word wrap, and quote margins
- **InputFields**: form container managing multiple fields and named buttons
- **Buttons**: non-editable fields that return immediately on arrow keys
- **Block**: structured quoted content with text and quote level (level 0 = user text, 1+ = quoted)
- **Mouse support**: click-to-focus fields and buttons, scrollbar interaction

### show_message_box

Modal popup with:
- Vertical and horizontal scrollbars
- Word wrapping (configurable, can be disabled for code/tracebacks)
- Screen save/restore
- Mouse click support (close button, scrollbars)
- Queue-aware "Abort All" option

---

## Logging

Rotating file logger with configurable:
- `path`: log file location
- `split_at`: max size before rotation
- `max_length`: total size including rotated files
- `max_age`: retention period

---

## File Manifest

| File | Purpose |
|------|---------|
| `DirtyFork.py` | Main entry point, event loop |
| `common.py` | User class, Destinations registry, user_director, login, expand_keys |
| `config.py` | Config/ConfigView, get_config() |
| `definitions.py` | Constants, RetVals, Estr/Eint, Char, Null, Disconnected |
| `input_output.py` | ANSI I/O, state tracking, send/ansi_move/ansi_color |
| `input_fields.py` | InputField/InputFields, show_message_box, Block |
| `keyboard_codes.py` | Key code mapping, mouse/position parsing |
| `menu.py` | Menu rendering, prefix matching, resolve_jump, multi-column layout |
| `door.py` | Door games, node management, dropfiles, I/O bridge |
| `teleconference.py` | Multi-channel chat, split-screen |
| `forum.py` | Forum module |
| `file.py` | File library, search/browse/upload/download |
| `register.py` | New user registration |
| `settings.py` | User settings page (shared with sysop) |
| `sysop_module.py` | Sysop panel: user keys, key groups, user settings |
| `bbs_msg.py` | Popup messages, permission checks, queueing |
| `ansi_emulator.py` | ANSI parser for door output, screen buffer |
| `file_transfer.py` | ZMODEM/YMODEM async wrappers |
| `logger.py` | Rotating file logging |
| `modem.py` | Serial/modem adapter classes and AT command handling |
| `modules.py` | Dynamic module loader |
| `paths.py` | Path resolution (project vs data directory) |
| `stars.py` | Ambient star animation |
