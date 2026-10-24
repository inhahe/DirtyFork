# DirtyFork BBS — Documentation

Setting up and configuring the BBS: its config, keys, menus, modules and doors. How it works inside (architecture, door sessions, ANSI state tracking, tests, the file manifest) is in [design.md](design.md).

---

## Configuration

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

### Letting Callers In (Firewall)

Callers on other machines reach `port` only if Windows Firewall lets them, and, behind a router, only if the router forwards that port to this machine. On inhahe.com the rule is **"DirtyFork BBS telnet (TCP 23)"**: inbound TCP 23, allowed for any program (so it holds whichever Python runs the BBS), on the **Private** profile only — the home network is Private, and on a network Windows calls Public the port stays closed. The router forwards port 23, so the BBS answers at `inhahe.com:23` from the internet.

From an elevated PowerShell (change `23` if `port:` changes):

```powershell
New-NetFirewallRule -DisplayName 'DirtyFork BBS telnet (TCP 23)' -Direction Inbound -Protocol TCP -LocalPort 23 -Action Allow -Profile Private
Remove-NetFirewallRule -DisplayName 'DirtyFork BBS telnet (TCP 23)'   # to close it again
```

The web terminal needs no rule of its own: its callers come in through the web server's port, and its bridge listens on this machine only (see [Web Terminal](#web-terminal)).

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

The rules also apply to menus entered as a submenu of another menu (e.g. a door category, or the Sysop menu from Main). They hold however a menu is reached: every menu a `/jump` path, a dotted path typed at a menu prompt, or a start destination passes through must admit the user, and a menu jumped to by its bare name must be one the user could reach from Main through menus that admit them, so going straight to a door or a submenu can't get around its category's keys. Door entries can additionally carry their own `white_keys`/`black_keys`, which the door module enforces for that door only.

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

Each segment matches an option by prefix (option names may themselves contain dots), and a single word may also name a menu (`/j doors_sysop`). Every menu a path passes through must admit the user, and a menu named directly must be one they could reach from Main (see [Keys](#keys)). Errors show which segment failed and what options are available, or which menu refused the user and the keys missing.

### Start Destination

Users can set a `start_destination` in their settings (using `/jump` syntax). After login, the BBS sends them directly to that destination instead of the main menu; one that no longer resolves, or that passes through a menu the user's keys don't admit, is skipped, and the main menu says why. Configured via the Settings page, which refuses a destination the user's own keys don't admit (a sysop setting another user's isn't checked against that user's keys).

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
| `daily_commands: [...]` | DOS commands run before the door on the first session of each day only (e.g. the door's maintenance program). Entries that share a `dir` share the once-a-day mark (`daily.stamp` in the door's `doors/_nodes` directory). The mark stands only once the commands have run to the end (the autoexec then writes `C:\DAILYOK.FLG`); if the session ends sooner (DOSBox never connects, the caller hangs up or aborts during them) it is taken back, so the next session runs them, and the log warns that they were cut off (a maintenance program that isn't safe to rerun after being stopped part-way needs a look). Like `pre_commands`, each is `CALL`ed. |
| `key_translation: doorway` | Translate the caller's ANSI/VT cursor, Home/End, PgUp/PgDn, Ins/Del and F1–F12 key sequences into DOORWAY's NUL + scan code, so arrow-key driven DOS programs run through DOORWAY work from any terminal. A lone ESC still reaches the program. |
| `screen_rows: 24` | For doors written for 24-line screens: the terminal's scroll region is limited to that many rows during the door (and reset afterwards), and the dropfiles report that page length. |
| `input_pace_ms: 30` | Send the caller's keys one at a time, this many ms apart, for doors that throw away typed-ahead input. |
| `white_keys` / `black_keys` | Restrict this door only (e.g. sysop-only tools, adult doors), on top of the door module's keys. |
| `door_sys: {...}`, `dorinfo: {...}`, ... | Override individual dropfile fields (see `doors/dropfiles/*.yaml`). |

Variables available in `command` and `pre_commands`: `{node}`, `{dropfile_path}` (`C:\DOOR.SYS` by default, see `dropfile_type`), `{dropfile_dir}` (`C:\`), `{handle}`, `{baud}`, `{com}`, `{mins_remaining}`, `{secs_remaining}`, `{rows}`, `{cols}`, plus any scalar from the door's config.

**Supported dropfile formats** (all written for every session): `DOOR.SYS` (52-line GAP/PCBoard/Wildcat), `DOOR<node>.SYS`, `DORINFO1.DEF` and `DORINFO<node>.DEF` (line 13 is `-1` only when `fossil: true`), `CHAIN.TXT` (32-line WWIV), `DOOR32.SYS` (11 lines; comm type 1/COM1 for DOSBox doors, 2/telnet socket for native doors), `CALLINFO.BBS`, `SFDOORS.DAT`. Field defaults are in `doors/dropfiles/*.yaml` and can be overridden per door.

**DOSBox drive mapping:**
- `C:\` — the node directory (`doors/_nodes/<dir>/node<N>`), where the dropfiles are written. It is removed when the session ends. (`<dir>` is the door's folder name when the door sits directly in `base_path` and the name uses only lowercase letters, digits, `.`, `_` and `-`; any other door gets its folder name plus `~` and a hash of its full path, e.g. `pit~3f2a…`, and a door whose `dir` is `base_path` itself gets `~base`.)
- `D:\` — the door's game directory (`doors/<dir>`), where the game EXE lives. The command runs from here.
- `E:\` — `tools_path` (`doors/tools`, not included): put a FOSSIL driver there (e.g. X00.EXE, for doors with `fossil: true`) and DOORWAY (`doors/tools/doorway`, for the sysop DOS shell).
- COM1 — the caller, through DOSBox-X's null-modem serial port.

Configure doors to read their dropfile from `C:\` (e.g. `C:\DOOR.SYS`) and their data from `D:\`; never put host paths in a door's own config files. If `dropfile_dir` is set, the dropfiles are also copied there before the door starts.

**Sysop DOS shell.** With DOORWAY in `doors/tools/doorway`, the sysop-only **DOS Shell** door (commented out in the *Sysop Tools* category of `DirtyFork.yaml`) gives a remote DOS prompt (through DOORWAY, which mirrors the DOSBox screen to your terminal and feeds your keys in) with `D:\` = `doors/`. Use it to run door installers and config programs (TEDIT, LORDCFG, ...) from your terminal, since DOSBox runs hidden. A config program that stores paths should be run with the same drive mapping the door has during play: give it its own sysop entry with `dir:` set to the door's directory, e.g. `command: 'E:\DOORWAY\DOORWAY.EXE COM1 /V:D /O:T /M:999 /G:ON /P:CONFIG.EXE'` (or `/C:DOS` for a prompt). DOORWAY feeds keys through the 15-key BIOS keyboard buffer, so pasting long text into it can drop characters.

**Screen handling**: the screen is cleared before a door starts. DOS doors were written for ANSI.SYS, where `ESC[2J` (and a form feed) clears the screen *and homes the cursor*; BBS terminals do the same, but VT100-style clients (PuTTY, xterm) don't, so door output has both rewritten to `ESC[2J ESC[H`, which means the same on every terminal.

**Session log**: the raw output of the most recent session on each node is kept in `doors/_nodes/<dir>/session<N>.log`, which helps when a door misbehaves. If it can't be written (a full disk, say), the session goes on without it.

**Cross-platform**: DOSBox/DOSBox-X runs on Linux and macOS too. The BBS generates DOSBox configs with OS-native paths, so doors work identically on all platforms. Just set `dosbox_path` to the correct binary (e.g., `/usr/bin/dosbox-x` on Linux).

**Native 32-bit doors**: Set `native: true` to run a door directly without DOSBox. Native doors default to TCP socket communication (`communication_type: SOCKET`) and find their dropfiles in the node directory (used as the working directory). STDIO pipes are also supported (`communication_type: STDIO`).

**Batch files**: Door commands that invoke `.BAT` files use `CALL` in the DOSBox autoexec so that control returns and DOSBox can exit cleanly.

**Escape**: Press **Ctrl+X three times** within 2 seconds to exit a door session. When the caller hangs up or aborts, the connection to DOSBox is closed so the door sees its carrier drop, and it gets up to 10 seconds to save the player and exit before DOSBox is terminated (a door that exits by itself is waited for 1 second). Doors that allow only one player at a time and keep a lock file (e.g. BRE's `INUSE.FLG`) can be left locked by an aborted session; with `max_nodes: 1` it is safe to delete the lock in `pre_commands`.

**Popups during doors**: The ANSI emulator tracks the door's screen state in `user.screen`. Popups save/restore this screen. Users can disable door popups via the `allow_door_popups` setting.

### Forums

Threaded discussion forums with quoting, search, and editing. Forums are defined in the config under `forum_list`.

### Private Messages

Threaded private messaging with compose, search, and new-message alerts.

### Teleconference

Multi-channel real-time chat with split-screen display. Users can join channels and see messages from other users in real time.

### File Library

File management with search, browse, list, upload, and download capabilities. Files are tagged with keys and descriptions via `files/meta.yaml`.

**Transfers** use ZMODEM (`zmodem.py`, DirtyFork's own) or YMODEM-G (`lib/ymodem`). A caller is asked which only when their terminal can run both; the web terminal runs ZMODEM only, so it is used without asking. A download starts by itself in terminals that watch for ZMODEM (SyncTERM, the web terminal); in others the caller starts receiving. For an upload the BBS waits (up to two minutes) for the caller's terminal to start sending. Pressing **Ctrl+X five times** cancels either. Afterwards the screen is redrawn as it was.

**Uploads** go into the library only whole and under a safe name:

- The name the caller's terminal sends is cut to its last part (no folders), without characters Windows forbids, leading dots or device names (`CON`, `NUL`, `COM1` ...), and at most 120 characters.
- A file never replaces another: a name already in the library (or the catalogue's own, `meta.yaml`) is refused, and the caller is told why.
- A file is received under a temporary name (`.upload-*.part`, never listed) and published only when it has arrived whole; an interrupted one is deleted (and any left by a crash, at the next start).
- `upload_max_size` (default `100 MB`) is the largest file taken, and `upload_keep_free` (default `500 MB`) the free disk space an upload must leave (`0`: none); sizes take B, KB, MB or GB. Both are checked as the data arrives, not only against the size the caller's terminal announces. An upload takes at most 20 files.

A download can only be a file the library lists: a name typed at Download is looked up there, never joined to a folder.

After an upload the caller is asked for a description and keys for each file saved.

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

The terminal type also decides how bright backgrounds are asked for: the blink attribute for BBS terminals (CP437, SyncTERM), the codes for bright background colours for xterm-family ones (which would blink instead); and which file transfer protocols are offered (the web terminal, `XTERMJS`, runs ZMODEM only).

### Mouse

Menus, forms and popups take clicks. The BBS asks for mouse reports in SGR form (`ESC[?1006h`), which carries any column, and still reads the older X10 form from terminals without it. The wheel is never taken for a click.

### Ambient Stars

`stars.py` runs a background task per connection that twinkles dim stars in the empty parts of the screen, from the login screen on. They are off unless the `stars:` block in the main config sets `enabled: true` (see the commented example in `DirtyFork.yaml`, which also sets the animation speed, density and colour). Once logged in, a user can turn them off with `show_stars: false` in their user YAML (but not on, if the sysop has them off), and override the colour with `stars_fg` / `stars_fg_br`. Stars appear only in empty, default-coloured cells, so they never cover text, and never inside doors; stars still on screen are erased when they switch off.

---

## Web Terminal

Callers without a telnet program can use the BBS from a web page: a full terminal in the browser (xterm.js, with the IBM VGA font) that reaches the BBS on its ordinary telnet port, with the mouse, file transfers (ZMODEM, by zmodem.js) and a choice of screen sizes. A browser cannot open a telnet connection itself, so the page talks WebSocket to a small bridge, `web/terminal_bridge.py`, which telnets to the BBS for it. To the BBS, a web caller is one more telnet caller.

```
browser (bbs.html: xterm.js, zmodem.js) --wss://host/bbs-ws--> nginx --> web/terminal_bridge.py (127.0.0.1:8023) --telnet--> BBS (127.0.0.1:23)
```

**On inhahe.com** (the sysop's own setup):

- **The page**: `https://inhahe.com/bbs.html`. Its files live in this project, `web/site/` (the page, `bbs-term/` with its script, style sheet, font and vendored libraries, and `bbs-term/README.txt` on where each came from), and `web\deploy-site.ps1` copies them into the site, `D:\mypage\inhahe.com`; run it again after changing them. The page works only as the web server serves it: it connects to `/bbs-ws` on the server it came from, so a copy opened from the disk (`file://`) says so instead of connecting.
- **The libraries**: `bbs.html` loads xterm.js and zmodem.js from the jsDelivr CDN (with integrity hashes). `bbs-local.html` is the same page using the copies in `bbs-term/vendor/` instead, for when the CDN is unwanted or unreachable; copy it over `bbs.html` to switch. (`tests/test_web_site.py` checks that the two stay the same page, that the copies are the CDN's files, and how `bbs.js` starts, in Node.)
- **nginx** (in WSL, `/etc/nginx/sites-enabled/inhahe.com`) passes `/bbs-ws` to the bridge, upgrading it to a WebSocket, so the page works over both `https` (as `wss://`) and `http`, through the site's own certificate and port.
- **The bridge** runs from logon as the Task Scheduler task "DirtyFork web bridge", registered (and started) by `web\register-bridge.ps1` with the project's own Python (`env\`); the task also fires every 5 minutes, so a bridge that stopped is back within 5 minutes. It runs independently of the BBS: while the BBS is down, web callers are told so. It accepts pages from inhahe.com and www.inhahe.com only. It logs to `web\terminal_bridge.log`, why it stopped included.
- **Trying changes** to the page without nginx: `python web/preview.py --bbs 127.0.0.1:23` serves `web/site` and the bridge on one port, `http://127.0.0.1:8099/bbs.html`.

**To set it up elsewhere:**

1. `pip install -r requirements.txt` (the bridge needs `websockets` 13 or later).
2. Run the bridge: `powershell -NoProfile -ExecutionPolicy Bypass -File web\register-bridge.ps1 -Origins https://your.site` (it uses `env\`'s Python when there is one, else the `python` on PATH; also `-Listen 127.0.0.1:8023 -Bbs 127.0.0.1:23`; re-running it applies new settings to the running bridge), or by hand: `python web/terminal_bridge.py --listen ... --bbs ... [--origin URL ...] [--max-clients 50] [--max-per-address 4] [--log path]`.
3. Proxy a path to it in the web server, as a WebSocket:

   ```nginx
   location = /bbs-ws {
       proxy_pass http://127.0.0.1:8023;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_read_timeout 1h;   # the bridge pings every 30 s
       proxy_send_timeout 1h;
   }
   ```

4. Run `web\deploy-site.ps1 -Root <the site's folder>` (or copy `web/site/` there). The page connects to `/bbs-ws` on its own host, and only there: an address taken from the page's URL would let a crafted link send a caller's typing, password included, to someone else's server.

**What callers get**:

- An xterm-compatible terminal reporting its type as `XTERMJS`, which the BBS reads as UTF-8 (so any character can be typed and shown), with bright backgrounds as colours, and ZMODEM as its only transfer protocol. Keys are an xterm's; Ctrl+V pastes, and Ctrl+C copies when text is selected (shift-drag selects while the BBS has the mouse).
- **Mouse**: clicks in menus, forms and popups, as in SyncTERM.
- **Screen size**: 80x25 (the default), 80x43, 80x50, 132x37, 132x52, or *Fill the window* (as many rows and columns as fit, at least 80x25). The size is fixed for a connection, since the BBS reads it at login: changing it offers to reconnect. The font is scaled to fill the window whenever it changes size, in whole screen pixels when *Sharp pixels* is on (the default). The choices are remembered in the browser.
- **File transfers**: a download is saved by the browser as soon as it arrives. For an upload a panel opens to choose the files (or drop them on it). The panel shows progress and can cancel; so can Ctrl+X five times.
- **Full screen** button; the bar above says whether it is connected and offers to connect again after a disconnect.

**Limits**: the BBS sees every web caller as coming from the bridge (see `known-issues.md`); the bridge's log records their real addresses. A download is held in the browser's memory until saved whole, so the upload limit is a sensible bound for files offered too.

**What the bridge guards against**: it connects only to the BBS it was started for, so it relays nowhere else, and a page must use its WebSocket subprotocol (`dirtyfork-terminal`) and send a screen size within limits first. It takes at most `--max-clients` web callers at once (default 50) and `--max-per-address` from one address (default 4; behind nginx the address is `X-Real-IP`, trusted only from this machine); the next is asked to try later. A socket that says nothing for 10 seconds is closed, so idle sockets cannot hold every slot. With `--origin` given, pages from other sites are refused, so they cannot use their visitors' browsers to fill it.

---

## Modem Support (Experimental)

Callers can dial in to a Hayes-compatible modem on a serial port (by `pyserial-asyncio`); each configured port is a line, answering one call at a time. The BBS answers calls itself: it sets the modem up, answers on `RING` with `ATA`, and once the call ends hangs up by dropping DTR (falling back to `+++` and `ATH` for a modem that ignores DTR), then sets the modem up again for the next call. Modem callers are treated as `ansi-bbs` terminals (CP437). Output is paced to the line's speed (from the modem's `CONNECT` message), so that cancelling a file transfer, or its repair of a damaged stretch, does not wait behind minutes of queued data.

**What the modem needs.** After your `init_string` (sent first, each time a port is set up: `ATZ` by default, to load the modem's stored profile, or `AT&F` for its factory settings), the BBS sends `ATE0V1Q0S0=0&C1&D2`: no echo, results in words, no auto-answer, carrier detect (DCD) following the carrier, and a hang-up when DTR drops. RTS/CTS (hardware) flow control is on at the port; most modems have it on by default, otherwise add it to the init string (`&K3` on many, `&H1&R2` on US Robotics). The cable must carry DCD, DTR and RTS/CTS (a full modem cable, not three wires); a USB modem has them built in. Without DCD the BBS cannot tell when a caller hangs up, and the line stays busy until the idle timeout (`modem.idle_timeout`).

**The log says** when the modem does not answer a command (no modem on the port, switched off, or at a different speed), answers `ERROR`, answers a call but does not connect, shows no carrier during a call, or when a port cannot be opened or fails (retried every 10 seconds, logged once until it works again).

**Over VoIP.** A phone line that is really VoIP (a cable or fibre provider's phone port, an analogue telephone adapter) carries modem signals poorly: the high speeds (V.90/V.92, V.34) mostly fail there, and lower ones (V.32bis, 14,400 bps and below) are likelier to hold. If the adapter offers it, use the G.711 codec and turn off silence suppression; limiting the modem's top speed in the init string (vendor-specific) can help.

**Testing:** `tests/test_modem.py` runs the modem code against a simulated modem (on the real serial transport), including a ZMODEM download over the line; it has not yet been used with real hardware.

### Configuration

```yaml
modem:
  baudrate: 115200        # serial port speed — 115200 is ideal because
                          # modem compression can exceed the line rate
  init_string: ATZ        # default AT init command (the BBS's own settings follow it)
  idle_timeout: 300       # modem-specific idle timeout (seconds, 0 = disabled)
  ports:
    - port: COM1
    - port: COM2
    - port: COM3
      baudrate: 9600      # per-port override
      init_string: ATZ&F  # per-port override
```

Each port answers calls independently. Per-port `baudrate` and `init_string` override the defaults. The legacy single-port format (`modem.port: COM1`) is also supported.

---

## Idle Timeout

Configurable inactivity timeout with an optional "are you still there?" warning popup. Separate timeout values for telnet and modem connections.

### How It Works

The timeout covers every kind of input: menus, forms, doors, teleconference and file transfers.

1. User is idle for `idle_timeout - idle_warning` seconds
2. A popup appears: "Are you still there? You will be disconnected in N seconds."
3. The popup saves/restores the screen — whatever was on screen is preserved
4. If the user presses any key, the timer resets and they continue normally
5. If no response during the warning period, the user is disconnected with a message

Before the terminal has been detected, the warning is plain text.

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

When a popup arrives while another is already showing, it waits; after the current popup is dismissed, the next one shows automatically. If multiple popups are queued, the user can press **A** ("Abort All") to clear the queue.

### Permissions

A popup is delivered only if:
- User has a screen and is fully connected
- `allow_pages` and `allow_bbs_messages` settings are enabled
- If in a door, `allow_door_popups` must be true
- Sender is not in the target's `blocked_users` list

---

## Logging

Rotating file logger with configurable:
- `path`: log file location
- `split_at`: max size before rotation
- `max_length`: total size including rotated files
- `max_age`: retention period
