# DirtyFork BBS

A modern async Python telnet BBS with full ANSI/CP437 support, DOS door games, forums, private messaging, file transfers, and real-time teleconference chat.

## Features

- **Door games** via DOSBox-X with node management and all major dropfile formats
- **Forums** with threaded replies, quoting, and search
- **Private messages** with threading
- **Teleconference** — split-screen multi-channel real-time chat
- **File library** with ZMODEM/YMODEM-G upload and download
- **Full ANSI/CP437** rendering with cursor and color state tracking
- **Per-user settings** — handle, password, profile, preferences
- **Access control** via white/black key system
- **Configurable menus** with prefix matching and multi-column layout
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

Add entries under `menu_system.doors.options` in `DirtyFork.yaml`:

```yaml
menu_system:
  doors:
    options:
      Trade Wars 2002:
        max_nodes: 4
        communication_type: COM
        command: 'TW2002.EXE TWNODE={node}'
        dir: 'tw2002'
```

Each door runs in its own node directory. The BBS writes all supported dropfile formats automatically.

### Supported Dropfile Formats

| File | Format |
|------|--------|
| `DOOR.SYS` | PCBoard |
| `DORINFO1.DEF` | RBBS-PC |
| `CHAIN.TXT` | WWIV extended (26-field) |
| `CALLINFO.BBS` | Wildcat! |
| `DOOR32.SYS` | Modern 32-bit telnet |
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

Keys are assigned to users in the `USER_KEYS` database table. All users get the `doors` key by default (configurable in `user_defaults.keys`).

## License

See [LICENSE](LICENSE).
