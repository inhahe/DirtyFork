# DirtyFork BBS — Design

What the BBS does and how it is built inside. For setting it up and configuring it (keys, menus, doors, modules, terminals, modems), see [DOCS.md](DOCS.md); this file covers the internals behind those features and is where to look before a change whose effects leave the file being edited.

## Features

Each links to the part of DOCS.md that describes its configuration.

- **Connections**: telnet (`telnetlib3`) and dial-up modems (`pyserial-asyncio`, several serial ports). [Modem Support](DOCS.md#modem-support-experimental)
- **Web terminal**: xterm.js in the browser, with zmodem.js for transfers, reaching the telnet port through a WebSocket bridge outside the BBS process. [Web Terminal](DOCS.md#web-terminal)
- **Terminals**: encoding detection (CP437 or UTF-8), what the terminal type implies (transfer protocols, how to show bright backgrounds) and screen-size detection; ANSI output with tracked cursor and colour state; mouse reports in SGR and X10 form. [Terminal and Encoding](DOCS.md#terminal-and-encoding)
- **File transfers**: ZMODEM (our own, `zmodem.py`) and YMODEM-G, both directions, cancellable with five Ctrl+X; uploads published whole under safe names, within size limits. [File Library](DOCS.md#file-library)
- **Login and registration**: an inline registration form whose fields and rules come from `register.yaml`. [Registration](DOCS.md#registration)
- **Menus**: prefix matching, `x` to exit levels, dotted paths, `/jump`, and a per-user start destination. [Menu System](DOCS.md#menu-system)
- **Access control**: keys (white/black lists per destination), recursive key groups, and banned users. [Access Control](DOCS.md#access-control)
- **Door games**: DOS doors in DOSBox-X over a null-modem link, and native doors over a socket or stdio. Also covers node management, the common dropfiles (DOOR.SYS, DORINFO, CHAIN.TXT, DOOR32.SYS and more), category menus, daily maintenance commands and a sysop DOS shell. [Door Games](DOCS.md#door-games)
- **File library**: a catalogue of millions of files, uploaded, zipped from websites, webpages and GitHub repositories, or listed where they are (pictures, videos, samples, modules); a search language with fields, wildcards, and/or/not; browsing by tag; uploads vetted by a sysop unless the uploader holds a key; a sync tool on a schedule. [File Library](DOCS.md#file-library)
- **Forums, private messages, teleconference, user settings, sysop panel**. [Modules](DOCS.md#modules)
- **Popups and pages** between users, queued, with per-user permissions. [Popup System](DOCS.md#popup-system)
- **Idle timeout** with an "are you still there?" warning. [Idle Timeout](DOCS.md#idle-timeout)
- **Ambient stars** twinkling in the empty parts of the screen. [Ambient Stars](DOCS.md#ambient-stars)

## Architecture Overview

DirtyFork is an async Python BBS. Each client connection spawns an async `user_loop` that detects the terminal, handles login/registration, then enters the main routing loop.

```
DirtyFork.py: main()
  ├─ telnetlib3.create_server(shell=user_loop)    — telnet listener
  ├─ modem.listen(port, baudrate, init_string, …)  — one per serial port (if configured), a call at a time
  │
  └─ user_loop(reader, writer, connection_type) per connection:
      ├─ idle.IdleMonitor wraps reader for timeout/warning
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
1. Resets mouse reporting (forced: a door's output reaches the terminal untracked), the cursor's visibility and colors
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
7. **Cleanup** (in a `finally`, each step even if an earlier wait was interrupted): the process is stopped and killed if need be, the node is released, the listener and logs are closed, DOSBox-X's output is logged, the daily mark is settled, and the node directory is removed. Then `ansi_reset_modes` puts the terminal's modes back (no scroll region, origin mode off, autowrap on, cursor shown, mouse reporting off), whatever the door left set. The caller returns to the menu the door was picked from.

Native doors skip DOSBox-X. A socket door (`DOOR32.SYS`) is bridged over TCP, and a stdio door over its pipes.

**Daily mark.** `daily.stamp` in the door's node root holds the date the daily commands last ran. It is checked and written with no await in between, so two sessions starting at once can't both run them. The autoexec writes `C:\DAILYOK.FLG` once they finish. `_settle_daily_mark` keeps the stamp if that flag exists. Otherwise it removes the stamp and logs a warning: the next session runs them again, possibly after an interrupted run.

## Terminal output

### ANSI State Tracking

The BBS tracks cursor position and color state precisely:

- `cur_*` properties reflect the actual terminal state. The BBS's own output updates them only through the `input_output.py` functions that write the sequences: `send()`, `ansi_move()`, `ansi_move_2()`, `ansi_cls()`, `ansi_set_region()`, `_ansi_color_write()`, `ansi_hide_cursor()`/`ansi_show_cursor()`. During a door, the ANSI emulator (`ansi_emulator.py`) sets them as the door's output moves the real cursor, and records the door's scroll region in `user.scroll_region_*` and its cursor visibility in `cur_show_cursor` (also on a full reset, `ESC c`). Rendering a screen file into `user.screen` uses the emulator with `live=False`, which records none of the terminal's modes, since none of them reaches the terminal.
- A line feed in `send()` follows the scroll region (`ansi_set_region`) as the terminal does: at the region's bottom the region scrolls and the cursor stays
- `new_*` properties stage pending changes (set by `ansi_move_deferred()`, `ansi_color()`)
- `send()` compares new vs cur and emits minimal escape codes; `ansi_clear_line_end()` applies pending changes the same way before clearing the rest of the row
- After text that fills a row to the last column, the cursor's position differs between terminals (deferred or immediate wrap): it is tracked as the start of the next row with `_pos_uncertain` set, and the next move is sent as an absolute position (the same after setting a scroll region, which homes the cursor on some terminals and not on others). With autowrap off the cursor stays on that last column. Either way `_row_full` is set until something moves the cursor, so `ansi_clear_line_end()` then clears nothing (an `ESC[K` there would erase the character just written)
- Mouse reporting is switched with `ansi_mouse_reporting()`, which tracks it in `user.mouse_reporting`
- Everything the BBS draws goes through those functions; nothing else assigns `cur_*`. What reaches `user.writer` directly is output the tracking doesn't cover:
  - a door's output (passed through by `door.py`'s output pump and tracked by the emulator);
  - file-transfer protocol data and the transfer's status lines (`file_transfer.py`);
  - notices sent just before a connection is closed (idle timeout, a login from elsewhere, shutdown);
  - the screen-size probe in `setup_terminal`, which runs before there is a screen to track.
- `user.write_lock` (re-entrant) serializes writes to `user.writer`, so background tasks such as the stars never interleave with other output

### Screen Buffer

An ANSI emulator (`ansi_emulator.py`) maintains `user.screen` — a character-by-character copy of what the terminal displays. This is used for:
- Saving/restoring screen around popups
- Tracking door game output
- Ambient stars: a star only appears in a cell the copy shows as an empty, default-colour space

### Ambient Stars

`stars.stars_loop` runs per connection. It reads the settings on every tick: the system's `stars.enabled` is the master switch, and a user's `show_stars` can only turn stars off. Stars still on screen are erased when they switch off. A tick first works out what to draw; one that has something draws it under `user.write_lock`, inside `input_output.cursor_preserved`, which saves and restores the tracked cursor, the colours (both current and pending), a staged move, the wrap state and the cursor's visibility, so the BBS's own output is undisturbed, and an idle tick writes nothing; popups (`show_message_box`) restore the same state with `save_cursor`/`restore_cursor`. New stars are sampled with geometric gaps (`_chosen_cells`) rather than with a random number per cell. `ansi_cls` calls a hook that repaints the stars still active, and nothing is drawn while the caller is in a door.

## Drawing on other users' screens

Some activities draw on a user's screen from other users' tasks. In the teleconference, a message, a header change or the typing indicator reaches every member's screen from the task of whoever caused it. That goes through `teleconference._draw_on(target, draw, needed)`:

- It draws in one piece, under the target's write lock and inside `cursor_preserved`, so the target's own half-done output (cursor, colours, a staged move) carries on undisturbed.
- While a popup (`user.popup_depth`) or an overlay (`user.screen_stack`, from `push_screen`) covers the target's screen (`input_output.screen_covered`), it draws nothing. Drawing then would go over the popup, and be lost when the popup restores what it covered. It marks the screen stale (`user.screen_stale`) instead.
- `needed()`, if given, is asked under the lock, once the screen is known to be uncovered. The typing indicator uses it to work out who is typing at drawing time, and to draw only when row 2 of `user.screen` doesn't already show that. Every keystroke in a channel gets there, so it rarely draws.

Each member has a log of the lines in their chat area (`member_lines`): channel messages, and lines sent to them alone, such as private messages, errors and `/help` output. `_display_message` adds a line to the log and draws it in one step under the member's lock, or only logs it while the screen is covered.

When the popup or overlay closes normally (not on the way out of a disconnect), `screen_uncovered` calls `user.redraw_hook` if the screen went stale meanwhile. The teleconference's hook redraws its whole screen under the lock: the layout, then the newest lines of the member's log (as many as the chat area holds), then the half-typed input. `pop_screen` skips repainting its outdated snapshot when such a redraw is coming. A screen counts as covered until the popup or overlay has finished restoring it.

## Modem connections

Each configured port has a `modem.listen()` task, which answers its calls one at a time:

1. `wait_for_call()` opens the port (RTS/CTS flow control, DTR up) and sends the sysop's init string (default `ATZ`), then `modem.SETUP`, a command each (a modem that does not know a setting answers its whole line `ERROR`, and many then apply none of it): `ATE0V1Q0` (no echo, results in words, first, so that the answers to the rest are words), `ATS0=0` (no auto-answer), `AT&C1` (DCD following the carrier), `AT&D2` (hang-up on DTR). A command the modem does not answer, or answers `ERROR`, is logged as a warning.
2. It waits for `RING` (or `RING 1`, `RING A`: distinctive rings), answers with `ATA` and waits (60 s) for `CONNECT`; a failed answer (`NO CARRIER`, silence) gets an `ATH`, and the wait for the next `RING`. Lines end at their LF, or at the CR of an echoed command or a numeric result (a stored profile with E1 and V0, until `SETUP`).
3. On `CONNECT` it returns a `SerialReader` and `SerialWriter`, the telnetlib3 reader's and writer's interface (`read(n)`, `set_encoding`; `write`, `drain`, `close`, `wait_closed`, `get_extra_info`), and starts a task watching the carrier.
4. `listen()` runs the session (`user_loop` with `connection_type="modem"`) to its end, then closes the writer, which hangs up, and waits for that before setting the modem up again for the next call.

During a call:

- **The caller's hang-up**: once DCD drops (having been up), the reader returns `""`, so the session ends; data that comes after the drop (the modem's `NO CARRIER`) is the modem's, not the caller's keys. The watch task polls DCD and ends a read that is waiting; a modem that never shows DCD is warned about (hang-ups then go unnoticed but for the idle timeout).
- **Flow control**: `drain()` waits until no more than about a second of output is queued in the transport and the port: pyserial-asyncio buffers 64 KiB before its own drain waits, and on Windows hands everything to the driver at once, which at modem speeds is minutes that a ZMODEM repair or a cancel would wait through. The speed is the `CARRIER` message's if the modem gives one, else `CONNECT`'s, at most 33,600 (many modems report the computer's speed to them in `CONNECT`). The writer asks file transfers for smaller blocks on slower lines, a drain after each (`SerialWriter.transfer_block`: 256 bytes below 4800 bps, 512 below 9600, else 1024, as lrzsz's `sz`; `file_transfer` puts it in ZMODEM's `Settings.subpacket_size` and `drain_every`), so that what is queued stays near a second plus a block. A drain raises `ConnectionResetError` if the caller hangs up meanwhile, or the port fails (pyserial-asyncio then drops what is written).
- **Hanging up** (`close()`, from any of the BBS's closes: the session's end, shutdown, a second login, logout): wait (up to 10 s) for the output to leave, drop DTR, and if the carrier is still up 3 s later (modems take a moment to go on hook), or cannot be told (no DCD), the `+++` escape between guard times and `ATH`; then close the port at once, dropping output still queued (`_close_port`): pyserial-asyncio's `close()` waits for that output, and its port flush runs on the event loop's thread without a time limit, so a modem that stopped taking data would stop the BBS, or keep the port open for good; and pyserial-asyncio's own graceful close (after a failed read, with output buffered) never ends on Windows, so that is aborted too. The same close ends a `wait_for_call` that is cancelled (a shutdown, with a switched-off modem's setup commands stuck in the port). DTR is left low however it ends.
- **A failed port** (a USB modem unplugged): it is logged as such (not as a hang-up), and reads end the session; `wait_for_call` raises `ModemGone` rather than reading a dead port as a quiet one (which spun without yielding and stopped the whole BBS). `listen()` tries the port again every 10 s, logging an error once until it works again.

Modem callers' terminals count as `ansi-bbs` (CP437). The reader decodes incrementally, so a UTF-8 character split across reads arrives whole.

## Web terminal

Two halves: the page (`web/site/`, deployed into the web site by `web/deploy-site.ps1`) and the bridge, `web/terminal_bridge.py`, a separate process (its own Task Scheduler task), not part of the BBS. The bridge accepts WebSockets from the page and opens an ordinary telnet connection to the BBS for each, so the BBS treats web callers as telnet callers and needs no restart when the bridge does.

- **Protocol** (WebSocket subprotocol `dirtyfork-terminal`): the page's first message is text, `{"cols": C, "rows": R}` (within 40..400 by 10..200); then binary messages carry the terminal's bytes both ways, unchanged. The bridge connects only to the one BBS it was started for, so it cannot relay anywhere else.
- **Telnet** is the bridge's: `Telnet` is the client half without I/O, a parser that keeps its state across reads (so a command split by the network is whole) and answers the BBS's negotiation once per change of state (RFC 1143's rule against loops). It agrees to BINARY both ways (8-bit clean transfers; without it telnetlib3 also waits its full 4 s `connect_maxwait` before the BBS starts), SGA and ECHO, and performs TTYPE (`XTERMJS`) and NAWS (the page's size); everything else is refused. It doubles 0xFF in input and sends a bare CR as CR NUL until BINARY is agreed.
- **Slots**: `--max-clients` in all and `--max-per-address` from one address (nginx's `X-Real-IP`, believed only from a loopback peer); a socket that has not given its size in 10 s is closed, since until it connects it holds a slot with no BBS session whose idle timeout would free it; `--origin` refuses other sites' pages (a client sending no Origin is let through, as it could claim any).
- **Closing**: the BBS side ending, by hang-up or error, closes the WebSocket (1000) so the page can offer to reconnect; an unreachable BBS sends a message and closes with 1011; a socket without a usable size, 1008; past the limits, 1013. An exception that stops the bridge is logged before it exits (under the scheduled task there is no stderr).
- **The page** (`bbs-term/bbs.js`): xterm.js draws the screen, in the IBM VGA 8x16 font (`customGlyphs` off, so its own line and block characters are drawn). The grid is fixed for a connection, because the BBS reads the size once (`get_screen_size`, which xterm.js answers); a window resize only rescales the font, in whole device pixels when "sharp". Bytes from the bridge go through zmodem.js's `Sentry`, which passes what is not ZMODEM to the terminal and turns a ZMODEM header into a download (accepted at once, saved by the browser) or an upload (a panel asks for the files: a file dialog opens only from a click). Typed text goes out as UTF-8; mouse reports with bytes over 127 come from xterm.js's `onBinary`, as raw bytes. Two zmodem.js quirks are handled there: a waiting BBS repeats its ZRINIT, which the Sentry reports as a retraction plus a new detection in the same `consume()`, so that pair keeps the panel; and the hex header it echoes to the terminal on first detection is left out.

## File transfers

`zmodem.py` is a complete ZMODEM, both directions, over any byte link (`read()`, `write()`, `drain()`), knowing nothing of telnet or the BBS. Receiving, it advertises full streaming (CANFDX, CANOVIO, CRC-32), takes 16- and 32-bit CRCs and every header form, answers ZSINIT, refuses ZCOMMAND, asks for data again (ZRPOS) after a damaged subpacket or a silence (and then, while what the sender had already sent drains, takes damage and noise in it as expected, not as errors: getting back in step has a time limit instead), and acknowledges a received file with ZRINIT but a skipped one only with its ZSKIP (zmodem.js gives up on a ZRINIT it did not expect). Sending, it streams ZCRCG subpackets, honours a receiver's buffer size (ZCRCW windows) and ESCCTL, and, between subpackets, reads the receiver's headers that a monitor task has queued, restarting from a ZRPOS position; after a restart it sends data before looking again, or a receiver hunting for the restart would ask again forever. Requests that have piled up behind a request get one restart, from the furthest of them (all were made before the receiver could see an answer; one by one, each would take the sender back behind a receiver that had moved on, which asks again, and so on through the file); other headers are left in place for whatever waits for them (an acknowledgement, the file's ZRINIT), as the sender keeps the receiver's headers in a deque it can look ahead in. A request is taken as made up to the furthest point ever sent, not cut down to the current pass, and a ZACK for an earlier place than the window's end acknowledges nothing. Both directions give up after `retries` errors in a row, counted afresh whenever the other side gets further (the sender: a ZRPOS or ZACK beyond any before it), so a long file over a noisy line is not abandoned for its many repairs; the sender's silences after ZEOF count on their own. The sender logs each restart at debug level and one line per file at info level saying how many there were. Five CANs in a row abort it from either side; a send blocked because the other side stopped reading is interrupted by an abort or a stall timeout. It escapes CR always, so a telnet link not in binary mode cannot mangle it.

`file_transfer.py` puts it (and YMODEM-G, from `lib/ymodem`, in a thread) on the caller's connection: a `_binary_session` holds the user's write lock, sets `user.in_transfer` (the stars stay off), switches the connection's encoding to Latin-1 (`common._set_connection_encoding`, which must reach the reader underneath the idle monitor), reads past the idle monitor's popup (`IdleMonitor.read_raw`), and afterwards drops what the caller's side still sends and restores the encoding; `_with_screen` saves the screen before and redraws it after (`push_screen`/`pop_screen`, with the modes reset first). It reads a megabyte at a time (`READ_SIZE`): telnetlib3's text reader hands back its whole buffer when asked for more than it holds, but decodes byte by byte, with a copy of the buffer each time, when asked for less. Uploads go through an `UploadPolicy`: a sanitised name (`safe_upload_name`), never an existing file or the catalogue's, size and free-space limits checked as the data arrives (`ROOM_CHECK`; a declared size can be false), at most `MAX_UPLOAD_FILES`, a temporary file published by a hard link that fails rather than replace (`publish`). YMODEM-G: `lib/ymodem` saves each file as `file<number>` in a fresh temporary folder, never under the sender's name, which then goes through the same policy when the file is published. `lib/ymodem` is patched (see `lib/README.md`): a cancel is a failure there, not a success, so a half-received file is never published. `file.py` offers only the protocols the terminal can run (`user.transfer_protocols`, from `detect_terminal`); what it sends and catalogues is the file library's (below).

## File library

**The catalogue** (`library.py`) is an SQLite database of its own (`file_library.catalog`, default `files/catalog/library.db`, in a folder of its own with the sync's lock, so the uploads folder holds only uploads and the library's folders; WAL), not the BBS's: it holds every file the library lists, up to millions (the `me` setup has 1.8 million, most of them samples). A `files` row names a file by a **root** and a path under it, never by an absolute path; `file_tags` holds its tags (with their display spelling and order); `sync_state` holds what `library_sync.py` remembers between runs. With millions of rows nothing is stored twice: a file's name is the last part of its path, a linked source's key for a file is its path (`source_key` is stored only for zips, and indexed only there), and a linked file's size and time are what the sync compares, where a zip needs a `fingerprint`. `files.edited` says whose a file's description and tags are: the sync's or the uploader's (`SYNCED`), a sysop's (`EDITED`, from `set_details(by_sysop=True)`), which nothing else writes over, through changes to the file too, or a sysop's given back to the sync (`RESET`, `reset_details`), which describes the file afresh at its next run even if it hasn't changed. That rule is kept by the writes, not by their callers: `set_details` for anyone but a sysop updates only a row that isn't `EDITED`, in one statement that takes the write lock before anything is checked (and reports a row gone), and `put`'s upsert keeps an `EDITED` row's description and tags; so the sync, working from entries read at a batch's start, can't undo an edit made since. `move` re-roots an entry as the same entry (its id, details and date kept; whatever was at the new path forgotten): a zip renamed, an upload approved. The schema has a version (`settings.schema`); `update_schema` (from `ensure_schema`, and from a dry run, which writes nothing else) brings an older catalogue up to date with `_MIGRATIONS` (version 2 added `edited`), under one write transaction, re-reading the version once it holds the lock. A new catalogue's tables and version are made in one transaction too; tables without a version are taken for the first schema's. The roots (`Library.roots`, from `library.from_config`) are `uploads` (`files_dir`), `pending` (uploads awaiting approval), `zips` (what the sync makes) and one per source of a linked type (`library.LINKED_TYPES`: gallery, videos, samples, mods), named after the source, whose files are listed where they are. `library.resolve` is the only way from an entry to a path: the root must be one the config names, no path part may be empty, `.` or `..`, and the real path must be a file strictly inside the root's real folder; a `pending` entry resolves only for vetting. So a caller can be sent nothing but a catalogued file inside its root, and uploads are written only to `files_dir` or `pending_dir` (never to a linked source's folder).

**Comparing.** Names, descriptions, uploaders and tags are stored also normalised (`norm`: NFKC, case-folded, letters, digits and dots only), and searches compare those: `"dirty fork"`, `dirty_fork` and `DirtyFork` are all `dirtyfork`. `norm_pattern` keeps `*` as well and nothing else GLOB treats specially, so a pattern goes to `GLOB` with no escaping.

**Searching.** `parse_query` reads the language (DOCS.md, File Library) into `Term`/`Op` nodes, every fault a `QueryError` whose message is for the caller; terms, nesting and depth are bounded (`MAX_TERMS`, `MAX_DEPTH`), since the text is untrusted and every node becomes SQL. `query_sql` makes one condition with parameters: a tag is `f.id IN (SELECT file_id FROM file_tags WHERE tag_norm = ?)` (evaluated once, then a lookup per row), a name or description `instr(...) > 0`, an uploader `=`, and with a `*` all of them `GLOB`. A word without a field is an OR over tag, name and description (`ANY_FIELD`). Every listing query excludes `root = 'pending'`. Results are an `array` of ids ordered by name (8 bytes a file, so even "everything" is cheap); `file._Items` fetches the entries of the rows on screen (`library.fetch`) as the list scrolls. Every catalogue call from the BBS runs in a thread on a connection of its own (`file._db`), so a search over millions of rows never stalls other callers.

**Browsing** (`library.browse`): a level is a set of tags; its subfolders are the other tags of the files having them all (counted), its files those whose tags are exactly the set (`files.tag_count`). The top level counts every tag with one index scan, less those of pending uploads, instead of joining millions of tag rows to their files.

**Uploads and vetting** (`file.py`): a trusted uploader's files (`file_library.upload_key`, or `sysop`) are received into `files_dir`, anyone else's into `pending_dir`; the upload policy refuses a name taken in either folder (approval moves one to the other) or one the library reserves (`Library.reserved_names`: its folders there; the catalogue's files and the sync's lock too, if the catalogue is put directly in the library folder). Each saved file is catalogued right after the transfer, before the uploader is asked for a description and tags, with an upsert, so it wins over a sync that catalogued the file meanwhile as found in the folder. `_tell_sysops` pages every sysop online about a pending upload (whatever their paging settings: it is work waiting for them, not a page); `common._tell_of_pending_uploads` pages a sysop at login. Sysops are paged once the uploader has given the details (or hung up). `library.approve` moves the file into `files_dir` (`library.move_new`: never replacing a file, all or nothing (a source that can't be removed, being downloaded, undoes the move), and across volumes by a copy beside the target, named like an upload in progress so nothing lists it meanwhile) and then re-roots the entry (dropping a stale row for that name: the name was free on disk); `library.reject` deletes the file and the entry. Both return what went wrong instead of raising, since `user_director` takes any `OSError` for a hang-up. `library.reconcile_uploads` (at BBS startup and in every sync) catalogues files found in the two folders and forgets those gone; it reads the catalogue before the folder, since the BBS publishes an upload before cataloguing it, so an upload arriving meanwhile is never taken for a file gone, and it forgets a row only if it is still in the root it read it from (one approved meanwhile has left `pending`). **Editing details** (`file._edit_details`): one form for a sysop, a description field and a `ListField` of tags (one per item: a tag may hold commas), reached by E in any list (`_show_list` edits, then returns `edited`, so its caller reads again what it lists: Browse, its level, which the new tags may change), by Edit while vetting, and by Sysop > File Details (`edit_files`: the search, its lists' Enter editing, `enter_edits`). It reads the entry afresh, saves in one write that fails if the entry is gone, keeps an unchanged description exactly (line breaks and all), shares the rows left (`_EDIT_FORM_ROWS`) between the description and the tag list (a screen too small for both is told so), and offers Reset for a synced file whose details are the sysop's. The uploader's details, typed after the transfer, don't replace a sysop's set meanwhile (the uploader is told). At startup `read_legacy_meta` reads a `meta.yaml` left from before the catalogue (a reserved name, never listed), `apply_legacy_meta` gives its tags and descriptions to those files, and only then `retire_legacy_meta` moves it into the catalogue's folder (under a time-stamped name if one is there), so a start that fails before then reads it again.

**The sync** (`library_sync.py`, run by the scheduled task from `register-library-sync.ps1`). A handler per source type yields `Item`s: the file's key within the source, its root and path, tags, a fingerprint, and either its description or a `describe` (costly: an HTML title, a module's header) and, for a zip, a `build`. `sync_source` compares a batch of 1000 at a time with what the catalogue has for those keys (a linked source's by root and path, a zip source's by stored key): an unchanged fingerprint, or size and time, keeps the entry (only tags and description are refreshed, unless a sysop's: see the catalogue; `describe` runs only for an entry given back); a new or changed one is built, then described and upserted (moved first, if its zip's name changed); one that fails is logged and keeps its old entry, to be tried again. **Sharing the catalogue with the BBS**, which writes uploads and waits at most 30 s for the lock: the sync's connection begins its write transactions `IMMEDIATE` (`open_catalogue`), since a deferred one reads first, and a BBS commit in between would make its first write fail at once (a stale snapshot, which no busy timeout retries); and it commits before every build and every half second (`settle`), so the lock is never held across a zip being made. A handler doesn't write either (it runs interleaved with fetching); what it wants remembered goes in `ctx.after`, written once the source is synced. The keys seen go into a temporary table, and only after the handler has finished are the source's other entries forgotten: a handler that raises (`SourceError`: a folder missing, GitHub unreachable) forgets nothing. Then `_sweep_zips` deletes the zips in the source's folder that no entry lists, the one place a zip is deleted (but for a whole source forgotten): it compares names as Windows does, ignoring case, since a page renamed from x.htm to X.htm has a new zip, X.zip, that is the file of the forgotten x.zip. Fingerprints: a linked file's size and time; a page's, its own and its `_files` folder's; a site's, every file's (path, size, time); a repository's, its commit. Each carries a recipe prefix (`PAGE_RECIPE`...), changed when a kind of zip is made differently, so every such zip is made again. Zips are made by 7-Zip under a temporary name beside the final one and moved into place (`put_in_place`; a zip being downloaded can't be replaced on Windows, so it waits for the next run). A website zip is updated with 7-Zip's synchronising switches on a copy (unchanged files are copied, not compressed again); a repository is cloned shallow into `repos_dir`, a change fetched, and `git diff --name-status` between the old and new commits says which files to replace (`7z u`) or remove (`7z d`) in a copy of its zip; GitHub's `pushed_at` (in `sync_state`) lets an unchanged repository skip even the fetch. Picture descriptions come from thumbsup2's `ai_descriptions` table, keyed by `thumbsup_key`, which reproduces its Node `hashFile` (sha1 of name, size and `mtimeMs` as JavaScript prints it). A lock file (`Library.sync_lock`) keeps runs one at a time. Folders are walked skipping hidden and system entries; a folder that can't be read is logged and left out, and marks the source incomplete (`Stats.incomplete`), which then forgets nothing that run. Each source's type is recorded in `sync_state` when it syncs, so `forget_unconfigured` can find the sources the config no longer names, and forget their entries and delete their zips and clones (`_forget_source`, a chunk at a time, committing between); a source whose type changes between linked and zipped has its old-shaped entries forgotten the same way, since nothing else would find them. git and 7-Zip are started without a console window (the task runs pythonw). The whole run is inside one handler that logs: under pythonw the log is all there is.

## Idle timeout

`idle.IdleMonitor` wraps the reader's `read()` method — the single entry point for all user input (menus, input fields, doors, teleconference). This means timeouts work everywhere without any per-module code. The warning popup's own input loop calls `read()` recursively; the monitor detects this via an `_in_warning` flag and does a plain timed wait without showing another popup. If the user has no screen yet (before terminal detection), the warning falls back to raw text. File transfers read with `read_raw`, which skips the timeout and popup (the protocols time out themselves) but counts as activity, and touch the clock when they end (a download receives almost nothing while it runs). Setting the encoding through it (`fn_encoding`) reaches the reader underneath.

## Input Field System

The `InputFields` system provides form-based input:

- **InputField**: text input with optional outline, fill character, word wrap, and quote margins; Ctrl+U deletes from the start of the line to the cursor (a line, not the whole text, so a slip in a message costs one line)
- **InputFields**: form container managing multiple fields and named buttons; a form of buttons only (Approve / Reject ...) starts on its first button, and Tab and the arrows wrap among the buttons
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

They load the shipped `DirtyFork.yaml` (as on a fresh clone) with a scratch data directory that is removed afterwards, and need no network, DOSBox or door files. Covered: door node directories, the generated autoexec and dropfiles, the daily mark, the door I/O pumps and process handling, menu keys on `/jump`, dotted paths and jumps to a menu by name, the text menu's prompt line (and the sysop menu's tools a letter each), the escape-sequence helpers, input fields (Ctrl+U, forms of buttons only), the ambient stars, mouse reports and bright backgrounds, what the terminal type implies and the protocol choice it leads to, the encoding switch through the idle monitor, and:

- **ZMODEM** (`test_zmodem.py`): framing in every header form and CRC, escaping of every byte value, and whole transfers between our sender and receiver over an in-memory pipe that can damage, drop or block what passes, with files of awkward sizes, skips, limits, cancels, timeouts, 16-bit CRCs and windowed receivers, more repairs in one file than `retries` (each further on), a receiver that gets no further, requests that pile up (one restart), a request from beyond the current pass, lost confirmations after ZEOF following a repair, and a ZRINIT or ZACK that arrives behind another header, and 256-byte subpackets.
- **Against other implementations** (`test_zmodem_interop.py`, skipped without the tool): zmodem.js under Node (`tests/zmodem_peer.js`, running the web terminal's own copy) and lrzsz's `sz`/`rz` in WSL, both directions, with escaping and with damage on the line.
- **YMODEM-G** (`test_ymodem.py`): `file_transfer` against small fake peers: a sender's cancel midway (nothing published), a device name, a receiver's cancel (not a success), a plain YMODEM receiver that refuses a packet once and asks late for the end of the batch, a connection that closes.
- **Uploads and the file library's screens** (`test_file_transfer.py`): upload names, sizes and room (checked as data arrives), publishing that never replaces; what a caller can be sent, a typed name never joined to a folder, trusted and vetted uploads (where they go, what is catalogued, the sysops' popups once the details are in, an upload rejected or a caller gone mid-prompts), names refused in either folder, the vetting screen and the editing form driven by their keys (fitting screens down to the smallest it allows, a description left untouched kept exactly, an uploader's details not replacing a sysop's), E in a list for sysops only, Enter editing in Sysop > File Details, a list's cache keeping the rows on screen, a tenth digit, sizes that fit, one count per search.
- **The catalogue** (`test_library.py`): the search language (precedence, fields, normalising, wildcards, every error, nesting limits, random input never crashing it) and its results on a small catalogue, browsing, `resolve` refusing everything outside a root, reconciling the library's folders (an upload catalogued while the folder is read is kept), approving (across volumes, over a stale row) and rejecting, never raising, an old `meta.yaml` taken once, a sysop's details (nothing else writing over them, giving them back, a file gone meanwhile) and moving an entry, an older catalogue's schema brought up to date (tables without a version too; a new one made all at once or not at all), the config's sources.
- **The sync** (`test_library_sync.py`): page and site titles through HTTrack's pages, video and module titles, thumbsup2's keys against values from Node, what each source type lists from a scratch tree, syncing (new, changed, removed, retagged; a source that can't be read forgets nothing; a dry run changes nothing; a sysop's details kept through every kind of run, and through edits made while a batch is synced; details given back described afresh, or when they can be; a renamed zip the same entry; a page renamed in case keeping its zip; folder tags), the BBS able to write while a source starts and while a zip is made (and writing throughout a sync), an unreadable folder forgetting nothing, hidden and system files left out, unreadable captions kept, a damaged module zip, sources gone from the config forgotten, zip names never clashing, the command line (a dry run makes nothing, and reads an older catalogue; a failure before any source is logged); and, with 7-Zip and git, website zips kept up to date, a zip in use tried again, a repository's zip following its commits file by file, an empty repository, and a zip of an older recipe made again.
- **The console** (`test_logger.py`): logging (the BBS's, asyncio's, Python's warnings, and a record that cannot be logged) goes on while the console is paused, and lines beyond the backlog are counted, not kept.
- **Who is on** (`test_sessions.py`): an ended session, or one logging out, leaves the registry, but not the session a second login of its handle put there.
- **Modems** (`test_modem.py`, Windows only): `modem.py` on pyserial-asyncio's real transport, against a simulated Hayes modem (`tests/fake_modem.py`: AT commands, RING, CONNECT, a line of a given speed, DCD, DTR, the `+++` escape): setting up, answering (and a failed answer), a modem that answers nothing, a port that fails while waiting, the caller's hang-up (loud and quiet), a modem without DCD, drain at 2400 bps and when the caller hangs up, hanging up after the output (by DTR, and by `ATH` when DTR is ignored), `close()` hanging up, a line that holds its output at the hang-up and a switched-off modem at a shutdown (neither may wait on the port's flush), a modem without DCD that ignores DTR, a modem slow to drop the carrier (no ATH), a port that closes itself with output buffered, drain once the port has failed, a failed port logged as such, a setting the modem does not know (the others still hold), the transfer block by line speed, a distinctive ring, the speed from a CARRIER message, numeric results with echo, one call at a time, a port that cannot be opened, a ZMODEM download over the line; and UTF-8 split across reads.
- **The web terminal's bridge** (`test_terminal_bridge.py`): its telnet client alone, and the bridge against a fake BBS (negotiation, every byte value both ways, the subprotocol and first-message checks, hang-ups and connection errors, an unreachable BBS, the connection limits, silent sockets, origins).
- **Transfers as a web caller makes them** (`test_web_transfers.py`): zmodem.js, over a WebSocket, through the bridge, to a real telnetlib3 server running `file_transfer` as the BBS does; downloads in UTF-8 and CP437, uploads with refused names and limits, cancelling; and the upload naming rules.
- **The page** (`test_web_site.py`): `bbs-local.html` is `bbs.html` with local files, and the integrity hashes match the vendored copies; `bbs.js`, run in Node by `tests/page_in_node.js` as the page runs it (from the `<head>`, while the document loads), with stand-ins for the browser and the libraries (skipped without `node`), connects to `/bbs-ws` on the server that served it, and does not try from a page opened from the disk or one whose libraries did not load, saying why instead and hiding the controls.

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
| `file.py` | File library's screens: search, browse, lists, download, upload, vetting uploads |
| `library.py` | The file library's catalogue: roots and `resolve`, the search language, browsing, approving and rejecting |
| `library_sync.py` | Fills and refreshes the catalogue from `file_library.sources` (zips with 7-Zip, repositories with git) |
| `register-library-sync.ps1` | Registers the sync's Task Scheduler task, its interval from a timed run |
| `register.py` | New user registration |
| `settings.py` | User settings page (shared with sysop) |
| `sysop_module.py` | Sysop panel: user keys, key groups, user settings, vetting uploads, editing files' details |
| `bbs_msg.py` | Popup messages, permission checks, queueing |
| `ansi_emulator.py` | ANSI parser for door output, screen buffer |
| `zmodem.py` | ZMODEM, sending and receiving, over any byte link |
| `file_transfer.py` | Transfers on a caller's connection (binary mode, screen, cancelling) and the upload policy |
| `lib/` | The vendored YMODEM-G library (`ymodem`); where it came from, and what was changed, in `lib/README.md` |
| `idle.py` | Idle timeout: the reader wrapper with its warning popup |
| `logger.py` | Rotating file logging, and the console's, from a thread of its own (a paused console must not stop the event loop); other libraries' and Python's warnings to both |
| `modem.py` | Modem calls: setting up and answering (AT commands), the session's serial reader and writer, the carrier, hanging up, a port's calls one at a time |
| `modules.py` | Dynamic module loader |
| `paths.py` | Path resolution (project vs data directory) |
| `stars.py` | Ambient star animation |
| `web/terminal_bridge.py` | WebSocket-to-telnet bridge for the web terminal (a separate process) |
| `web/register-bridge.ps1` | Registers and starts the bridge's Task Scheduler task |
| `web/site/` | The web terminal's page: `bbs.html`, `bbs-local.html`, and `bbs-term/` (script, style, font, vendored xterm.js and zmodem.js) |
| `web/deploy-site.ps1` | Copies `web/site` into the web site |
| `web/preview.py` | Serves the page and a bridge on one local port, to try changes without nginx |
| `tests/` | Unit tests (`python -m unittest discover -s tests`) |
