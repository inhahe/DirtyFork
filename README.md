# DirtyFork BBS

A modern async Python BBS supporting telnet and dial-up modem connections, with full ANSI/CP437 support, DOS door games, forums, private messaging, file transfers, and real-time teleconference chat.

## Features

- **Door games** via DOSBox-X with node management and all major dropfile formats
- **Forums** with threaded replies, quoting, and search
- **Private messages** with threading
- **Teleconference** — split-screen multi-channel real-time chat
- **File library** with ZMODEM/YMODEM-G upload and download
- **Full ANSI/CP437 and UTF-8** with automatic encoding detection
- **Per-user settings** — profile, preferences, encoding, start destination
- **Access control** via white/black key system with recursive key groups
- **Sysop panel** — manage user keys, key groups, and user settings
- **Configurable menus** with prefix matching, multi-column layout, and `/jump` navigation
- **Popup system** with queueing, scrolling, and mouse support
- **Web terminal** — callers can use the BBS from a web page (jsTerm, through a WebSocket-to-telnet bridge); see [DOCS.md](DOCS.md#web-terminal)
- **Modem support** via pyserial-asyncio with AT command handling (untested — see below)
- **Idle timeout** with configurable warning prompt and separate modem/telnet timeouts
- **Rotating logs** and SQLite database (auto-created on first run)

## Requirements

- Python 3.10+
- [DOSBox-X](https://dosbox-x.com/) (for door games)

```
pip install -r requirements.txt
```

## Quick Start

1. Copy `DirtyFork.yaml` to your data directory and edit it:
   - Set `bbs_name` and `sysop_name`
   - Set `dosbox_path` under `destinations.door` to your DOSBox-X executable
2. Run the BBS:
   ```
   python DirtyFork.py --data-dir /path/to/your/data
   ```
3. Connect with any telnet client to port 23.

The database and log file are created automatically on first run.

## Usage

```
python DirtyFork.py [config] [--data-dir PATH] [--debug]

  config          Path to config file (default: DirtyFork.yaml in data dir)
  --data-dir PATH Directory for data files: config, database, logs, user configs
                  (default: current working directory)
  --debug         Enable verbose debug logging
```

## Configuration

`DirtyFork.yaml` is the main config file. Key settings:

```yaml
bbs_name: My BBS
sysop_name: Sysop
hostname: 0.0.0.0   # bind address
port: 23

destinations:
  door:
    dosbox_path: C:\dosbox-x\dosbox-x.exe
    base_path: doors
    max_nodes: 20
```

Top-level config values (like `bbs_name` and `sysop_name`) are available as `{bbs_name}` and `{sysop_name}` placeholders anywhere in the config, including door command strings and dropfile sections.

### Adding Door Games

Put each door in its own directory under `doors/` and add a menu option whose target is the `door` module. Doors can be grouped into category submenus of the Doors menu (each category is a menu with its own `destinations` entry); see `DOCS.md` for the full set of door options (FOSSIL loading, pre-commands, per-door DOSBox settings, Y2K date shifting, per-door keys):

```yaml
menu_system:
  doors:
    options:
      Space: {target: doors_space}
  doors_space:
    title: Space
    option_defaults:
      target: door
      dosbox_conf: doors/dosbox.conf
    options:
      Trade Wars 2002:
        max_nodes: 4
        command: 'TW2002.EXE TWNODE={node}'
        dir: 'tw2002'
```

Inside DOSBox, `C:\` holds the dropfiles for the session, `D:\` is the door's directory and `E:\` is `doors/tools` (not included: put a FOSSIL driver and DOORWAY there if your doors need them); point the door's own configuration at `C:\` for its dropfile. Each session gets its own node directory and the BBS writes all supported dropfile formats automatically. With DOORWAY installed, a sysop-only DOS shell door lets you run door installers and config programs from your terminal.

### Supported Dropfile Formats

| File | Format |
|------|--------|
| `DOOR.SYS` | GAP/PCBoard/Wildcat (52 lines) |
| `DORINFO1.DEF` | RBBS-PC / QuickBBS |
| `CHAIN.TXT` | WWIV (32 lines) |
| `CALLINFO.BBS` | Wildcat! |
| `DOOR32.SYS` | Modern 32-bit (11 lines) |
| `SFDOORS.DAT` | Spitfire |

Field defaults for each format are in `doors/dropfiles/*.yaml` and can be overridden per door in `DirtyFork.yaml`.

### Escaping a Door

Press **Ctrl+X three times** within 2 seconds to abort a door session and return to the BBS.

## Directory Layout

```
DirtyFork.yaml        # main config (copy to your data dir)
DirtyFork.db          # SQLite database (auto-created)
DirtyFork.log         # log file (auto-created)
user_configs/         # per-user YAML profiles
files/                # file library
files/meta.yaml       # file metadata (keys, descriptions)
doors/                # door game directories
doors/dosbox.conf     # shared DOSBox-X base config
doors/dropfiles/      # dropfile format defaults
doors/tools/          # mounted as E: in door sessions (FOSSIL driver, DOORWAY; not included)
doors/_nodes/         # per-session node dirs (dropfiles) and last session logs
input_fields.yaml     # input field definitions
register.yaml         # registration form config
```

## Access Control

Destinations and menus support white/black key access control:

```yaml
destinations:
  doors:
    white_keys: [doors]   # user must have this key
    black_keys: [banned]  # user must NOT have this key
```

Keys are assigned to users in the `USER_KEYS` database table. New users receive default keys from `user_defaults.keys` (e.g., `[doors]`).

### Key Groups

Key groups let a single key automatically grant other keys, with recursive expansion:

```yaml
key_groups:
  sysop:
  - doors
  - debug
```

A user with the `sysop` key effectively has `doors` and `debug` too. Groups can include other groups. The sysop can edit groups at runtime via the sysop panel.

### Banned Users

The `banned` key is checked at login. If a user's expanded key set contains `banned`, they are immediately logged out — no need to add `banned` to every destination's `black_keys`.

## Menu Navigation

Menus support **prefix matching** — type the shortest unambiguous prefix of an option name (e.g., `m` for "Messages", `fo` for "Forums"). Type `x` to exit, `xx` to go up two levels, etc.

The **`/jump`** command (or `/j`) navigates directly using dotted paths:

```
/j forums.philosophy     → opens the Philosophy forum
/j files.search          → opens file search
```

Users can set a **start destination** in their settings (same `/jump` syntax) to skip the main menu on login.

## Sysop Panel

The sysop menu (requires the `sysop` key group) provides:

- **Keys** — view and edit any user's keys
- **Groups** — edit key group definitions (saved to YAML, applied live)
- **Settings** — edit any user's profile and preferences

## Modem Support (Experimental)

Modem/serial connections are supported via pyserial-asyncio. The BBS listens for incoming calls using AT commands (RING detection, ATA to answer, ATH to hang up). Multiple serial ports can be configured for multi-line setups.

**Note:** Modem support is currently untested — the developer does not have a modem. If you try it, please report issues.

```yaml
modem:
  baudrate: 115200        # serial port speed — 115200 is ideal because
                          # modem compression can exceed the line rate
  init_string: ATZ        # default AT init command for all ports
  idle_timeout: 300       # modem idle timeout in seconds (0 = disabled)
  ports:
    - port: COM1
    - port: COM2
    - port: COM3
      baudrate: 9600      # per-port override
```

Modem connections auto-detect as ANSI/CP437 terminals. Each port gets its own listener task.

## Idle Timeout

Configurable inactivity timeout with optional "are you still there?" warning prompt. Separate timeout values for telnet and modem connections. The warning shows as a popup that saves/restores the screen.

```yaml
idle_timeout: 300         # telnet timeout in seconds (0 = disabled)
idle_warning: 30          # seconds before timeout to show warning (0 = no warning)
```

## Documentation

See [DOCS.md](DOCS.md) for setting up and configuring the BBS: the config file, keys, menus, every module and the door options. [design.md](design.md) describes how it works inside: the architecture, routing and key checks, door sessions, ANSI state tracking, the tests and the file manifest.

## License

See [LICENSE](LICENSE).
