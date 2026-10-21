"""
BBS Door Game System

Handles launching DOS and native door games, managing node allocation,
generating dropfiles, bridging data between the user's telnet connection
and the door process (via TCP socket for DOSBox/DOOR32, or stdio pipes
for native doors).
"""

import asyncio
import hashlib
import os
import re
import shutil
import socket
import time
import paths

from definitions import *
from input_output import send, ansi_cls, ansi_set_region, ansi_reset_modes
from config import get_config
from ansi_emulator import AnsiEmulator
from logger import log

config = get_config()
conf = config.destinations.door


# ---------------------------------------------------------------------------
# Node tracking
# ---------------------------------------------------------------------------

class Node:
    """Represents a single active door session."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# key = node key (see _node_key: the door's directory), value = list of active Node instances
nodes = {}


def _total_active_nodes():
    """Return the total number of active nodes across all doors."""
    return sum(len(v) for v in nodes.values())


def _allocate_node_number(node_key):
    """Find the lowest available node number for the door identified by *node_key*."""
    if node_key not in nodes:
        nodes[node_key] = []
    used = {n.node_num for n in nodes[node_key]}
    num = 1
    while num in used:
        num += 1
    return num


def _release_node(node_key, node):
    """Remove *node* from the active list for *node_key*."""
    if node_key in nodes:
        try:
            nodes[node_key].remove(node)
        except ValueError:
            pass


# ---------------------------------------------------------------------------
# Port helpers
# ---------------------------------------------------------------------------

def _find_free_port(start=5000):
    """Return a TCP port that is currently free, starting the search at *start*."""
    port = start
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1
    raise RuntimeError("Could not find a free TCP port")


# ---------------------------------------------------------------------------
# Dropfile generation
# ---------------------------------------------------------------------------

def _bbs_name():
    return str(config.bbs_name) if config.bbs_name else "DirtyFork"


def _sysop_name():
    return str(config.sysop_name) if config.sysop_name else "Sysop"


def _sysop_first_last():
    name = _sysop_name()
    parts = name.split(None, 1)
    first = parts[0] if parts else "Sysop"
    last = parts[1] if len(parts) > 1 else ""
    return first, last


def _user_first_last(user):
    handle = getattr(user, "handle", None) or "Unknown"
    parts = handle.split(None, 1)
    first = parts[0]
    last = parts[1] if len(parts) > 1 else ""
    return first, last


def _user_location(user):
    return getattr(user, "location", None) or ""


def _user_sex(user):
    sex = getattr(user, "sex", None)
    if sex and str(sex).upper() in ("M", "F"):
        return str(sex).upper()
    return "M"


def _user_age(user):
    age = getattr(user, "age", None)
    if age:
        try:
            return int(age)
        except (ValueError, TypeError):
            pass
    return 0


def _screen_rows(user):
    return getattr(user, "screen_height", None) or 25


def _door_rows(user, door_conf):
    """Rows the door gets: the caller's screen, or fewer if the door wants
    (screen_rows: 24 for doors written for 24-line screens)."""
    rows = _screen_rows(user)
    if door_conf and door_conf.screen_rows:
        try:
            rows = max(1, min(rows, int(door_conf.screen_rows)))
        except (TypeError, ValueError):
            log.warning("Ignoring invalid screen_rows: %s", door_conf.screen_rows)
    return rows


def _screen_cols(user):
    return getattr(user, "screen_width", None) or 80


def _time_remaining_secs():
    return 3600  # 60 minutes default


def _time_remaining_mins():
    return 60


def _generate_door_sys(user, node_num, node_dir, door_conf, variables):
    """Generate DOOR.SYS (the 52-line GAP/PCBoard/Wildcat format)."""
    df = door_conf.door_sys if door_conf else null
    gdf = lambda key, default: _get_df(df, key, default, variables)

    lines = [
        gdf("com_port", "COM1:"),                  #  1 COM port (COM1 in DOSBox; COM0: = local mode)
        gdf("baud_rate", "115200"),                #  2 baud rate
        "8",                                       #  3 parity / data bits (always 8)
        variables["node"],                         #  4 node number
        gdf("dte_rate", "{baud}"),                 #  5 DTE rate (locked port speed)
        gdf("screen_display", "Y"),                #  6 screen display
        gdf("printer_toggle", "N"),                #  7 printer toggle
        gdf("page_bell", "Y"),                     #  8 page bell
        gdf("caller_alarm", "Y"),                  #  9 caller alarm
        variables["handle"],                       # 10 user full name
        variables["location"],                     # 11 calling from
        gdf("home_phone", ""),                     # 12 home phone
        gdf("work_phone", ""),                     # 13 work / data phone
        gdf("password", ""),                       # 14 password placeholder
        gdf("security_level", "0"),                # 15 security level
        gdf("times_called", "1"),                  # 16 total times on
        gdf("last_call_date", "01/01/00"),         # 17 last date called
        variables["secs_remaining"],               # 18 seconds remaining this call
        variables["mins_remaining"],               # 19 minutes remaining this call
        "GR",                                      # 20 graphics mode (GR = ANSI, always)
        gdf("page_length", "{rows}"),              # 21 page length (screen rows unless overridden)
        gdf("expert_mode", "N"),                   # 22 user mode (Y = expert)
        gdf("conferences", ""),                    # 23 conferences registered in
        gdf("conf_joined", ""),                    # 24 conference exited to door from
        gdf("expiration_date", ""),                # 25 user expiration date
        gdf("user_record", "1"),                   # 26 user record number
        gdf("protocol", "Z"),                      # 27 default protocol
        gdf("uploads", "0"),                       # 28 total uploads
        gdf("downloads", "0"),                     # 29 total downloads
        gdf("dl_k_today", "0"),                    # 30 daily download K total (today)
        gdf("daily_dl_k", "999999"),               # 31 daily download max K limit
        gdf("birthday", ""),                       # 32 birthday
        gdf("user_db_path", variables["door_node_dir"]),  # 33 path to the MAIN directory
        variables["door_node_dir"],                # 34 path to the GEN directory (dropfiles)
        variables["sysop_name"],                   # 35 sysop name
        variables["handle"],                       # 36 user alias
        gdf("event_time", "00:00"),                # 37 event time
        gdf("error_correcting", "Y"),              # 38 error correcting connection
        gdf("ansi_in_ng_mode", "N"),               # 39 ANSI supported & caller using NG mode
        gdf("record_locking", "Y"),                # 40 use record locking
        gdf("default_color", "7"),                 # 41 default colour
        gdf("time_credits", "0"),                  # 42 time credits in minutes
        gdf("last_new_scan", "01/01/00"),          # 43 last new files scan date
        gdf("time_of_call", "00:00"),              # 44 time of this call
        gdf("last_time_on", "00:00"),              # 45 time of last call
        gdf("max_daily_files", "999"),             # 46 maximum daily files available
        gdf("files_today", "0"),                   # 47 files downloaded so far today
        gdf("total_ul_k", "0"),                    # 48 total K uploaded
        gdf("total_dl_k", "0"),                    # 49 total K downloaded
        gdf("comment", ""),                        # 50 user comment
        gdf("total_doors", "0"),                   # 51 total doors opened
        gdf("messages_left", "0"),                 # 52 total messages left
    ]
    return "\r\n".join(lines) + "\r\n"


def _generate_dorinfo(user, node_num, door_conf, variables):
    """Generate DORINFO1.DEF (RBBS / QuickBBS format)."""
    df = door_conf.dorinfo if door_conf else null
    gdf = lambda key, default: _get_df(df, key, default, variables)

    sysop_first, sysop_last = _sysop_first_last()

    lines = [
        variables["bbs_name"],                     #  1 BBS name
        sysop_first,                               #  2 sysop first name
        sysop_last,                                #  3 sysop last name
        gdf("com_port", "COM1"),                   #  4 COM port
        gdf("baud_parity", "115200 BAUD,N,8,1"),   #  5 baud/parity/data/stop
        gdf("network_type", "0"),                  #  6 network type (0 = none)
        variables["first_name"],                   #  7 user first name
        variables["last_name"],                    #  8 user last name
        variables["location"],                     #  9 location
        gdf("ansi", "1"),                          # 10 graphics (0=no, 1=ANSI)
        gdf("security_level", "0"),                # 11 security level
        variables["mins_remaining"],               # 12 minutes remaining
        "-1" if variables["fossil"] == "1" else "0",  # 13 -1 = FOSSIL loaded, 0 = use the UART
    ]
    return "\r\n".join(lines) + "\r\n"


def _generate_chain_txt(user, node_num, node_dir, door_conf, variables):
    """Generate CHAIN.TXT (WWIV format)."""
    df = door_conf.chain_txt if door_conf else null
    gdf = lambda key, default: _get_df(df, key, default, variables)

    # CHAIN.TXT directories end with a backslash
    nd = variables["door_node_dir"].replace("/", "\\")
    if not nd.endswith("\\"):
        nd += "\\"

    lines = [
        gdf("user_record", "1"),                   #  1 user number
        variables["handle"],                       #  2 user alias
        variables["handle"],                       #  3 user real name
        "",                                        #  4 callsign (HAM radio)
        variables["age"],                          #  5 age
        variables["sex"],                          #  6 sex
        gdf("gold", "0"),                          #  7 gold
        gdf("last_login", "01/01/00"),             #  8 last logon date
        variables["cols"],                         #  9 screen columns
        variables["rows"],                         # 10 screen lines
        gdf("security_level", "0"),                # 11 security level (0-255)
        gdf("co_sysop", "0"),                      # 12 1 if co-sysop
        gdf("sysop", "0"),                         # 13 1 if sysop
        gdf("ansi", "1"),                          # 14 1 if ANSI
        gdf("remote", "1"),                        # 15 1 if remote caller (0 = local console)
        variables["secs_remaining"],               # 16 seconds left until logoff
        nd,                                        # 17 GFILES directory
        nd,                                        # 18 DATA directory
        gdf("sysop_log", ""),                      # 19 system log of the day
        variables["baud"],                         # 20 user baud rate
        variables["com"],                          # 21 COM port number
        variables["bbs_name"],                     # 22 system name
        variables["sysop_name"],                   # 23 sysop name
        gdf("logon_time", "0"),                    # 24 time user logged on (secs since midnight)
        gdf("secs_on_today", "0"),                 # 25 seconds on system so far today
        gdf("uploaded_k", "0"),                    # 26 uploaded K
        gdf("uploads", "0"),                       # 27 number of uploads
        gdf("downloaded_k", "0"),                  # 28 downloaded K
        gdf("downloads", "0"),                     # 29 number of downloads
        "8N1",                                     # 30 parity
        variables["baud"],                         # 31 COM port baud rate
        variables["node"],                         # 32 node number
    ]
    return "\r\n".join(lines) + "\r\n"


def _generate_door32_sys(user, node_num, socket_handle, door_conf, variables, in_dosbox):
    """Generate DOOR32.SYS (11 lines).

    Native doors get the telnet socket (comm type 2); DOSBox doors
    (*in_dosbox*) are on a serial port, so they get comm type 1 and COM port 1.
    """
    df = door_conf.door32_sys if door_conf else null
    gdf = lambda key, default: _get_df(df, key, default, variables)

    lines = [
        gdf("comm_type", "1" if in_dosbox else "2"),  #  1 comm type (0=local, 1=serial, 2=telnet)
        variables["com"] if in_dosbox else str(socket_handle),  # 2 comm or socket handle
        gdf("baud_rate", "115200"),                #  3 baud rate
        variables["bbs_software"],                 #  4 BBS software name and version
        gdf("user_record", "1"),                   #  5 user record number (1-based)
        variables["handle"],                       #  6 user real name
        variables["handle"],                       #  7 user handle / alias
        gdf("security_level", "0"),                #  8 security level
        variables["mins_remaining"],               #  9 time remaining (minutes)
        gdf("emulation", "1"),                     # 10 emulation (0=ASCII, 1=ANSI)
        variables["node"],                         # 11 current node number
    ]
    return "\r\n".join(lines) + "\r\n"


def _generate_sfdoors_dat(user, node_num, door_conf, variables):
    """Generate SFDOORS.DAT (Spitfire format)."""
    df = door_conf.sfdoors_dat if door_conf else null
    gdf = lambda key, default: _get_df(df, key, default, variables)

    lines = [
        "1",                                       # user record number
        variables["handle"],                       # user name
        "",                                        # password placeholder
        "0",                                       # security level
        variables["mins_remaining"],               # minutes remaining
        gdf("ansi", "1"),                          # ANSI (1=yes)
        variables["node"],                         # node number
        variables["bbs_name"],                     # BBS name
        variables["sysop_name"],                   # sysop name
        gdf("baud_rate", "115200"),                # baud rate
        gdf("com_port", "COM1"),                   # COM port
        gdf("data_bits", "8"),                     # data bits
        gdf("stop_bits", "1"),                     # stop bits
        gdf("parity", "N"),                        # parity
    ]
    return "\r\n".join(lines) + "\r\n"


def _generate_callinfo_bbs(user, node_num, door_conf, variables):
    """Generate CALLINFO.BBS (Wildcat! format)."""
    df = door_conf.callinfo_bbs if door_conf else null
    gdf = lambda key, default: _get_df(df, key, default, variables)

    lines = [
        variables["first_name"],                   # first name
        variables["last_name"],                    # last name
        variables["location"],                     # city/location
        gdf("baud_rate", "115200"),                # baud rate
        gdf("fossil_connected", "1"),              # FOSSIL connected (1=yes)
        gdf("security_level", "0"),                # security level
        variables["mins_remaining"],               # time remaining (minutes)
        gdf("ansi", "1"),                          # ANSI (1=yes)
        variables["handle"],                       # alias/handle
        "",                                        # password placeholder
        gdf("home_phone", ""),                     # home phone
        gdf("data_phone", ""),                     # data phone
        gdf("expiration_date", "01/01/00"),        # expiration date
        gdf("user_record", "1"),                   # user record number
        gdf("com_port", "1"),                      # COM port number
        gdf("times_on_today", "0"),                # times on today
        gdf("total_times_on", "0"),                # total times on
        gdf("total_uploads", "0"),                 # total uploads
        gdf("total_downloads", "0"),               # total downloads
        gdf("kb_dl_today", "0"),                   # KB downloaded today
        gdf("max_kb_per_day", "0"),                # max KB per day
    ]
    return "\r\n".join(lines) + "\r\n"


def _write_all_dropfiles(user, node_num, node_dir, door_conf, variables, in_dosbox, socket_handle=0):
    """Write every supported dropfile format into *node_dir*."""
    files = {
        "DOOR.SYS":            _generate_door_sys(user, node_num, node_dir, door_conf, variables),
        f"DOOR{node_num}.SYS": _generate_door_sys(user, node_num, node_dir, door_conf, variables),
        "DORINFO1.DEF":        _generate_dorinfo(user, node_num, door_conf, variables),
        f"DORINFO{node_num}.DEF": _generate_dorinfo(user, node_num, door_conf, variables),
        "CHAIN.TXT":           _generate_chain_txt(user, node_num, node_dir, door_conf, variables),
        "DOOR32.SYS":          _generate_door32_sys(user, node_num, socket_handle, door_conf, variables, in_dosbox),
        "SFDOORS.DAT":         _generate_sfdoors_dat(user, node_num, door_conf, variables),
        "CALLINFO.BBS":        _generate_callinfo_bbs(user, node_num, door_conf, variables),
    }
    for name, content in files.items():
        path = os.path.join(node_dir, name)
        with open(path, "w", newline="") as f:
            f.write(content)
    return files


# ---------------------------------------------------------------------------
# Command-line variable substitution
# ---------------------------------------------------------------------------

def _build_vars(user, node_num, node_dir, door_conf, socket_port, config_path="", in_dosbox=False):
    """Build the dict used for {variable} substitution in the door command.

    For DOSBox doors the node directory is mounted as C:, so every path the
    door sees ({dropfile_dir}, {dropfile_path}, {door_node_dir}) is the DOS
    path, not the host path.  {node_dir} is always the host path.
    """
    handle = getattr(user, "handle", None) or "Unknown"
    door_dir = _resolve_door_dir(door_conf, _base_path())

    dropfile_type = str(door_conf.dropfile_type) if door_conf.dropfile_type else "DOOR.SYS"
    door_node_dir = DOS_NODE_DRIVE + "\\" if in_dosbox else node_dir
    dropfile_path = (DOS_NODE_DRIVE + "\\" + dropfile_type) if in_dosbox else os.path.join(node_dir, dropfile_type)

    user_first, user_last = _user_first_last(user)

    base_vars = {
        "node": str(node_num),
        "com": "1",
        "baud": "115200",
        "dropfile_path": dropfile_path,
        "dropfile_dir": door_node_dir,
        "door_node_dir": door_node_dir,
        "dropfile_type": dropfile_type,
        "config_path": config_path,
        "time_limit": str(_time_remaining_mins()),
        "mins_remaining": str(_time_remaining_mins()),
        "secs_remaining": str(int(_time_remaining_secs())),
        "handle": handle,
        "first_name": user_first,
        "last_name": user_last,
        "location": _user_location(user),
        "age": str(_user_age(user)),
        "sex": _user_sex(user),
        "socket_handle": str(socket_port),
        "graphics_mode": "ANSI",
        "fossil": "1" if door_conf.fossil else "0",
        "bbs_software": "DirtyFork",
        "bbs_name": _bbs_name(),
        "sysop_name": _sysop_name(),
        "data_path": (DOS_DOOR_DRIVE + "\\") if in_dosbox else door_dir,
        "rows": str(_door_rows(user, door_conf)),
        "cols": str(_screen_cols(user)),
        "irq": "4",
        "io_port": "3F8",
        "uart_type": "16550",
        "node_dir": node_dir,
        "socket_port": str(socket_port),
    }

    # Add all scalar door config values as variables.
    # Dict values (sub-sections like door_sys, dorinfo) are skipped.
    # Session variables (handle, node, rows, etc.) always take priority.
    if door_conf:
        try:
            for k, v in door_conf.items():
                k = str(k)
                if k not in base_vars and v is not null and v is not None and not hasattr(v, 'items'):
                    base_vars[k] = _safe_format(str(v), base_vars)
        except Exception:
            pass

    return base_vars


def _safe_format(template, variables):
    """Substitute {variable} placeholders using only the provided dict.

    This prevents users from injecting arbitrary format strings (e.g. via
    their handle) that could resolve against Python internals.
    """
    try:
        return template.format_map(variables)
    except (KeyError, ValueError, IndexError):
        return template


def _get_df(section, key, default, variables):
    """Read a field from a dropfile config section with {variable} substitution.

    Falls back to *default* if the section is absent or the key is not set.
    The null sentinel (falsy) is treated as absent; explicit empty string "" is
    preserved as-is.
    """
    if section:
        v = section[key]
        if v is not None and v is not null:
            return _safe_format(str(v), variables)
    return _safe_format(str(default), variables)


# ---------------------------------------------------------------------------
# Door directory resolution
# ---------------------------------------------------------------------------

# Seconds to wait for a door to exit by itself before terminating it: after
# the door closed its side, and after the caller hung up / aborted.
DOOR_EXIT_GRACE = 1.0
HANGUP_EXIT_GRACE = 10.0

# Drive letters inside DOSBox: C: = node (dropfile) dir, D: = door dir,
# E: = shared tools dir (FOSSIL driver etc.), when one is configured.
DOS_NODE_DRIVE = "C:"
DOS_DOOR_DRIVE = "D:"
DOS_TOOLS_DRIVE = "E:"


def _base_path():
    """Directory that relative door paths are resolved against."""
    return paths.resolve_project(str(conf.base_path)) if conf.base_path else paths.resolve_project("doors")


def _resolve_door_dir(door_conf, base_path):
    """Resolve the door's directory.  Relative paths are relative to *base_path*."""
    door_dir_raw = str(door_conf.dir) if door_conf.dir else ""
    if not door_dir_raw:
        return base_path
    if os.path.isabs(door_dir_raw):
        return door_dir_raw
    return os.path.join(base_path, door_dir_raw)


def _resolve_under_base(path):
    """Resolve a sysop-configured path: absolute as-is, else relative to base_path."""
    path = str(path)
    return path if os.path.isabs(path) else os.path.join(_base_path(), path)


def _node_key(door_dir):
    """Key for node allocation.  Two menu entries that share a door directory
    (e.g. the same door listed in two categories) share one set of nodes, so
    they can never be handed the same node number."""
    return os.path.normcase(os.path.abspath(door_dir))


def _node_root(door_dir):
    """Host directory holding this door's per-node dropfile directories.

    Kept outside the door's own directory so that removing a finished node
    can never touch the door's data files (some doors keep their own NODEn
    files or directories).  One flat directory per door directory, and no two
    door directories share one: a door directly under base_path whose name is
    made of [a-z0-9._-] keeps that name; any other door gets its last
    component plus '~' and a hash of its full path ('~' never occurs in the
    first kind, so the two kinds can't meet), and base_path itself is '~base'.
    """
    door_abs = os.path.abspath(door_dir)
    try:
        rel = os.path.normcase(os.path.relpath(door_abs, os.path.abspath(_base_path())))
    except ValueError:  # on another drive (Windows)
        rel = None
    if rel == os.curdir:
        name = "~base"  # a door whose dir is base_path itself (e.g. the sysop DOS shell)
    elif rel is not None and _PLAIN_NODE_NAME.fullmatch(rel) and rel != os.pardir:
        name = rel
    else:
        digest = hashlib.sha1(_node_key(door_dir).encode("utf-8")).hexdigest()[:12]
        label = re.sub(r"[^a-z0-9._-]", "-", os.path.basename(door_abs).lower()) or "door"
        name = f"{label}~{digest}"
    return os.path.join(_base_path(), "_nodes", name)


_PLAIN_NODE_NAME = re.compile(r"[a-z0-9._-]+")


def _is_door_option(option_conf):
    return bool(option_conf) and option_conf is not null and str(option_conf.target or "") == "door"


def _find_door_conf(user, door_name):
    """The config of the door the user picked, or null.

    Doors can live in any menu (e.g. category submenus of the doors menu):
    it is option *door_name* of the menu whose option the user picked
    (user._option_menu, set by a menu pick, /jump, a dotted path or a start
    destination, once the keys of the menus on the way have been checked).
    Other menus are deliberately not searched: a door of the same name there
    may sit behind keys nobody checked.
    """
    picked = getattr(user, "_option_menu", None)
    info = picked.options_info.get(door_name) if picked is not None else None
    if info is not None and _is_door_option(info.conf):
        return info.conf
    return null


# ---------------------------------------------------------------------------
# DOSBox config generation
# ---------------------------------------------------------------------------

# Written to the node directory (C:\) by the autoexec once the daily commands
# have run to the end; without it the day's mark is taken back.
DAILY_DONE_FLAG = "DAILYOK.FLG"


def _daily_stamp_path(door_dir):
    return os.path.join(_node_root(door_dir), "daily.stamp")


def _daily_stamp_is_today(stamp):
    try:
        with open(stamp) as f:
            return f.read().strip() == time.strftime("%Y-%m-%d")
    except OSError:
        return False


def _daily_commands_due(door_dir, door_conf):
    """True if the door has daily_commands and they haven't run yet today.

    Marks today as done, so only the first session of the day runs them;
    _unmark_daily takes that back if they don't run to the end.  Doors that
    share a directory share the mark.  Called on the event loop with no await
    in between check and mark, so two sessions starting at once can't both run
    them.
    """
    if not door_conf.daily_commands:
        return False
    stamp = _daily_stamp_path(door_dir)
    if _daily_stamp_is_today(stamp):
        return False
    os.makedirs(os.path.dirname(stamp), exist_ok=True)
    with open(stamp, "w") as f:
        f.write(time.strftime("%Y-%m-%d") + "\n")
    return True


def _settle_daily_mark(door_dir, node_dir, door_name):
    """After the session that was to run the daily commands, while its node
    directory still exists: keep today's mark if they ran to the end (the
    autoexec then wrote DAILY_DONE_FLAG there), else take it back so the
    next session runs them, and warn the sysop, since they may have been cut
    off part-way and will run again over whatever they left."""
    if os.path.exists(os.path.join(node_dir, DAILY_DONE_FLAG)):
        return
    _unmark_daily(door_dir)
    log.warning("%s: the daily commands did not run to the end (cut off, or the door "
                "never started); the next session runs them again", door_name)


def _unmark_daily(door_dir):
    """Take back today's mark: the session that was to run the daily commands
    didn't run them to the end (the door never started, or the caller left
    during them), so the next session runs them."""
    stamp = _daily_stamp_path(door_dir)
    if _daily_stamp_is_today(stamp):
        try:
            os.remove(stamp)
        except OSError:
            pass


def _generate_dosbox_config(node_dir, door_dir, door_conf, variables, socket_port, run_daily=False):
    """Generate the DOSBox .conf file content."""
    command = str(door_conf.command) if door_conf.command else ""
    resolved_command = _safe_format(command, variables)

    # Build copy commands to put dropfiles where the door expects them
    # By default, dropfiles are already in node_dir which is mounted as C:
    copy_cmds = ""
    dropfile_dir = door_conf.dropfile_dir
    if dropfile_dir and str(dropfile_dir):
        # If the door expects dropfiles somewhere specific, copy them
        dest = str(dropfile_dir)
        dest_resolved = _safe_format(dest, variables)
        copy_cmds = f'xcopy c:\\*.SYS "{dest_resolved}" /Y\n'
        copy_cmds += f'xcopy c:\\*.DEF "{dest_resolved}" /Y\n'
        copy_cmds += f'xcopy c:\\*.TXT "{dest_resolved}" /Y\n'
        copy_cmds += f'xcopy c:\\*.BBS "{dest_resolved}" /Y\n'
        copy_cmds += f'xcopy c:\\*.DAT "{dest_resolved}" /Y\n'

    # Per-door DOSBox-X overrides, e.g.  dosbox_settings: {cpu: {cycles: 20000}}
    # These are written before [serial]/[autoexec] and override doors/dosbox.conf.
    settings_text = ""
    settings = door_conf.dosbox_settings
    if settings and hasattr(settings, "items"):
        for section, values in settings.items():
            if section in ("serial", "autoexec") or not hasattr(values, "items"):
                log.warning("Ignoring dosbox_settings section '%s'", section)
                continue
            settings_text += f"[{section}]\n"
            for key, value in values.items():
                settings_text += f"{key}={value}\n"
            settings_text += "\n"

    # Shared tools directory (FOSSIL driver etc.), mounted as E:.
    tools_mount = ""
    tools_path = door_conf.tools_path or conf.tools_path
    if tools_path:
        tools_dir = _resolve_under_base(tools_path)
        if os.path.isdir(tools_dir):
            tools_mount = f'mount {DOS_TOOLS_DRIVE[0].lower()} "{tools_dir}"\n'
        else:
            log.warning("tools_path not found: %s", tools_dir)

    # Commands run before the door, from the door directory: the FOSSIL
    # driver for doors that need one (fossil: true), then any pre_commands.
    pre = []
    # Y2K-buggy doors: run the emulated clock N years in the past.  A multiple
    # of 28 keeps the weekdays (and leap years) the same as today's calendar,
    # and the date still advances daily, so the door's daily maintenance works.
    if door_conf.date_shift_years:
        try:
            shift = int(door_conf.date_shift_years)
            today = time.localtime()
            year = today.tm_year - shift
            day = today.tm_mday
            if today.tm_mon == 2 and day == 29 and not (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
                day = 28
            pre.append(f"DATE {today.tm_mon:02d}/{day:02d}/{year:04d}")
        except (TypeError, ValueError):
            log.warning("Ignoring invalid date_shift_years: %s", door_conf.date_shift_years)
    if door_conf.fossil:
        fossil_cmd = str(door_conf.fossil_command or conf.fossil_command or "")
        if not fossil_cmd:
            log.warning("Door wants a FOSSIL driver but no fossil_command is configured")
        elif not tools_mount:
            log.warning("Door wants a FOSSIL driver but tools_path is not mounted")
        else:
            pre.append(f"{DOS_TOOLS_DRIVE}\\{_safe_format(fossil_cmd, variables)}")
    # daily_commands (e.g. the door's maintenance program) on the first session
    # of each day, then pre_commands on every session.
    for key, wanted in (("daily_commands", run_daily), ("pre_commands", True)):
        commands = door_conf[key]
        if not commands or not wanted:
            continue
        if isinstance(commands, str):
            commands = [commands]
        pre += [_safe_format(str(c), variables) for c in commands]
        if key == "daily_commands":
            pre.append(f"ECHO done> {DOS_NODE_DRIVE}\\{DAILY_DONE_FLAG}")
    # Each line is CALLed: a batch file run without CALL replaces the autoexec
    # and never returns.  DOSBox-X's CALL also runs programs and internal
    # commands (IF, DATE, DEL ...).
    pre_text = "".join(f"CALL {c}\n" for c in pre)

    # Only [serial] and [autoexec] go here; everything else lives in the
    # sysop-editable doors/dosbox.conf which is loaded first by DOSBox-X.
    config_content = f"""{settings_text}[serial]
serial1=nullmodem server:127.0.0.1 port:{socket_port} transparent:1 baudrate:115200

[autoexec]
mount c "{node_dir}"
mount d "{door_dir}"
{tools_mount}c:
{copy_cmds}d:
{pre_text}CALL {resolved_command}
exit
"""
    return config_content


# ---------------------------------------------------------------------------
# Data bridging
# ---------------------------------------------------------------------------

async def _show_queued_popups(user):
    """Show all of *user*'s queued popups over the door, then clear the popup event."""
    from input_fields import show_message_box
    try:
        while user.popup_queue:
            kwargs = user.popup_queue.pop(0)
            r = await show_message_box(user, queued_count=len(user.popup_queue), **kwargs)
            if r == "abort":
                user.popup_queue.clear()
                break
    finally:
        user.popup_event.clear()


class _DoorInput:
    """What the caller types, on its way to the door.

    * Ctrl+X three times within 2 seconds aborts the session.
    * key_translation: doorway -- ANSI/VT cursor and function key sequences
      (ESC[A, ESC[11~, ESC OP, ...) become DOORWAY's NUL + scan code, so
      arrow-key driven DOS programs run through DOORWAY work from an
      ordinary terminal.
    * input_pace_ms -- send keys one at a time, this far apart, for doors that
      throw away typed-ahead input.
    """
    ESCAPE_CHAR = 0x18
    ESCAPE_COUNT = 3
    ESCAPE_WINDOW = 2.0

    # sequence after ESC -> PC scan code
    DOORWAY_KEYS = {
        b"[A": 0x48, b"OA": 0x48, b"[B": 0x50, b"OB": 0x50,
        b"[C": 0x4D, b"OC": 0x4D, b"[D": 0x4B, b"OD": 0x4B,
        b"[H": 0x47, b"OH": 0x47, b"[1~": 0x47, b"[7~": 0x47,
        b"[F": 0x4F, b"OF": 0x4F, b"[4~": 0x4F, b"[8~": 0x4F, b"[K": 0x4F,
        b"[2~": 0x52, b"[@": 0x52, b"[3~": 0x53,
        b"[5~": 0x49, b"[V": 0x49, b"[6~": 0x51, b"[U": 0x51,
        b"OP": 0x3B, b"OQ": 0x3C, b"OR": 0x3D, b"OS": 0x3E, b"Ot": 0x3F,
        b"[11~": 0x3B, b"[12~": 0x3C, b"[13~": 0x3D, b"[14~": 0x3E, b"[15~": 0x3F,
        b"[17~": 0x40, b"[18~": 0x41, b"[19~": 0x42, b"[20~": 0x43, b"[21~": 0x44,
        b"[23~": 0x85, b"[24~": 0x86,
    }

    def __init__(self, door_conf):
        self.translate = str(door_conf.key_translation or "").lower() == "doorway"
        if door_conf.key_translation and not self.translate:
            log.warning("Unknown key_translation '%s' (supported: doorway)", door_conf.key_translation)
        try:
            self.pace = max(0.0, float(door_conf.input_pace_ms or 0) / 1000.0)
        except (TypeError, ValueError):
            log.warning("Ignoring invalid input_pace_ms: %s", door_conf.input_pace_ms)
            self.pace = 0.0
        self.pending = b""      # an ESC sequence that may still turn into a key
        self._escape_hits = 0
        self._escape_last = 0.0

    def aborted(self, data, now):
        """Track Ctrl+X presses; True once the caller has asked to abort."""
        for byte in data:
            if byte == self.ESCAPE_CHAR:
                if now - self._escape_last > self.ESCAPE_WINDOW:
                    self._escape_hits = 0
                self._escape_hits += 1
                self._escape_last = now
                if self._escape_hits >= self.ESCAPE_COUNT:
                    return True
            else:
                self._escape_hits = 0
        return False

    def keys(self, data):
        """Translate *data*; returns the list of byte strings to send, each one key."""
        if not self.translate:
            return [bytes([b]) for b in data] if self.pace else [data]
        out = []
        for byte in data:
            if self.pending:
                seq = self.pending[1:] + bytes([byte])
                if seq in self.DOORWAY_KEYS:
                    out.append(b"\x00" + bytes([self.DOORWAY_KEYS[seq]]))
                    self.pending = b""
                    continue
                if any(k.startswith(seq) for k in self.DOORWAY_KEYS):
                    self.pending += bytes([byte])
                    continue
                out.extend(bytes([b]) for b in self.pending)  # not a key after all
                self.pending = b""
            if byte == 0x1B:
                self.pending = b"\x1b"
            else:
                out.append(bytes([byte]))
        return out if self.pace else ([b"".join(out)] if out else [])

    def flush(self):
        """Keys held back waiting for the rest of an ESC sequence (none came: a plain ESC)."""
        held, self.pending = self.pending, b""
        if not held:
            return []
        return [bytes([b]) for b in held] if self.pace else [held]

    async def send(self, keys, write, drain):
        for i, key in enumerate(keys):
            write(key)
            await drain()
            if self.pace and i < len(keys) - 1:
                await asyncio.sleep(self.pace)
        if self.pace and keys:
            await asyncio.sleep(self.pace)


class _DoorOutput:
    """Door output on its way to the caller.

    DOS doors were written for ANSI.SYS, where ESC[2J (and a form feed) clears
    the screen *and homes the cursor*.  BBS terminals do the same, but
    VT100-style clients (PuTTY, xterm, ...) leave the cursor where it was and
    treat a form feed as a line feed, which scrambles every screen the door
    draws afterwards.  So both become ESC[2J ESC[H, which means the same thing
    on every terminal.
    """
    CLEAR = "\x1b[2J"

    def __init__(self):
        self.held = ""   # a possible start of ESC[2J at the end of the last chunk

    def feed(self, text):
        text = self.held + text
        self.held = ""
        for n in range(len(self.CLEAR) - 1, 0, -1):
            if text.endswith(self.CLEAR[:n]):
                self.held = text[-n:]
                text = text[:-n]
                break
        return text.replace(self.CLEAR, self.CLEAR + "\x1b[H").replace("\x0c", self.CLEAR + "\x1b[H")

    def flush(self):
        held, self.held = self.held, ""
        return held


# Why a door session ended (returned by the pumps and bridges)
ENDED_BY_DOOR = "door"      # the door exited or closed its side
ENDED_BY_CALLER = "caller"  # the caller hung up or aborted with Ctrl+X (or the BBS side failed)


async def _pump_user_to_door(user, door_input, write, drain, still_running=lambda: True):
    """Caller -> door.  Pauses while a popup is shown.

    Returns ENDED_BY_CALLER when the caller aborts (Ctrl+X three times) or
    hangs up, ENDED_BY_DOOR when the door goes away (its process exits, or
    writing to it fails).
    """
    try:
        while still_running():
            if user.popup_event and user.popup_event.is_set():
                await _show_queued_popups(user)
                continue
            try:
                data = await asyncio.wait_for(user.reader.read(4096), timeout=0.1)
            except asyncio.TimeoutError:
                keys = door_input.flush()
            else:
                if not data:
                    return ENDED_BY_CALLER
                if isinstance(data, str):
                    data = data.encode("cp437", errors="replace")
                if door_input.aborted(data, asyncio.get_event_loop().time()):
                    log.info("User aborted door session via escape sequence")
                    return ENDED_BY_CALLER
                keys = door_input.keys(data)
            try:
                await door_input.send(keys, write, drain)
            except OSError:
                return ENDED_BY_DOOR
        return ENDED_BY_DOOR
    except (OSError, Disconnected):
        return ENDED_BY_CALLER
    except Exception:
        log.error("user_to_door error", exc_info=True)
        return ENDED_BY_CALLER


class _SessionLog:
    """The raw output of a door session (session<N>.log), kept for debugging.

    A debugging aid must never disturb the session, so nothing here raises:
    if the file can't be opened, written or closed (a full disk, say; closing
    flushes, so it can fail too), the log stops and the session goes on.
    """

    def __init__(self, path):
        self._path = path
        self._file = None
        try:
            self._file = open(path, "w", encoding="utf-8", errors="replace")
        except OSError as e:
            log.warning("Door session log %s not kept: %s", path, e)

    def write(self, text):
        if self._file is not None:
            try:
                self._file.write(text)
            except Exception as e:
                self._stop(e)

    def close(self):
        if self._file is not None:
            try:
                self._file.close()
                self._file = None
            except Exception as e:
                self._stop(e)

    def _stop(self, error):
        log.warning("Door session log %s stopped: %s", self._path, error)
        f, self._file = self._file, None
        try:
            f.close()  # (closed already if it was close() that failed)
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()


async def _pump_door_to_user(user, read, emulator=None, session_log=None):
    """Door -> caller, keeping the ANSI emulator's copy of the screen in step.
    *session_log*, if given, is a _SessionLog.

    Returns ENDED_BY_DOOR when the door closes its side, ENDED_BY_CALLER
    when writing to the caller fails (the caller hung up).
    """
    door_output = _DoorOutput()

    async def deliver(text):
        nonlocal emulator
        if not text:
            return
        if emulator:
            try:
                emulator.feed(text)
            except Exception:
                emulator = None  # the session goes on without it
                log.error("Door output: ANSI emulator failed; popups over this door "
                          "may not restore its screen", exc_info=True)
        if session_log:
            session_log.write(text)
        user.writer.write(text)
        await user.writer.drain()

    while True:
        try:
            if door_output.held:
                try:
                    data = await asyncio.wait_for(read(4096), timeout=0.05)
                except asyncio.TimeoutError:
                    data = None  # nothing more came: send what was held back
            else:
                data = await read(4096)
        except OSError:
            data = b""  # the door's side broke: treat it as closed
        try:
            if data is None:
                await deliver(door_output.flush())
                continue
            if not data:
                await deliver(door_output.flush())
                return ENDED_BY_DOOR
            if isinstance(data, bytes):
                data = data.decode("cp437", errors="replace")
            await deliver(door_output.feed(data))
        except (OSError, Disconnected):
            return ENDED_BY_CALLER
        except Exception:
            log.error("door_to_user error", exc_info=True)
            return ENDED_BY_CALLER


# When the door ends, its last output may still be on its way (in the pipe or
# socket): give the output pump this long to deliver it.
OUTPUT_DRAIN_SECS = 2.0


async def _run_until_first_done(*coros, output=None):
    """Run the bridge tasks; when any finishes, cancel the rest.

    If the first to finish reports ENDED_BY_DOOR, the task at index *output*
    (the door-to-caller pump) first gets OUTPUT_DRAIN_SECS to deliver the
    door's last output.  Returns the result of the task that finished first.
    """
    tasks = [asyncio.create_task(c) for c in coros]
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        first = next(t for t in tasks if t in done)
        if (output is not None and not tasks[output].done() and not first.exception()
                and first.result() == ENDED_BY_DOOR):
            await asyncio.wait([tasks[output]], timeout=OUTPUT_DRAIN_SECS)
        return first.result()
    finally:
        # (also when this task is cancelled: the bridge must not outlive it)
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def _bridge_socket(user, reader_or_host, writer_or_port, process, door_conf,
                         emulator=None, session_log=None):
    """Bridge data between the user's telnet connection and a TCP socket.

    For DOSBox (COM/FOSSIL) doors, pass an already-connected (reader, writer).
    For native SOCKET doors, pass (host, port) strings and this connects to them.
    """
    if isinstance(reader_or_host, str):
        # Native SOCKET door: connect to the door process
        host, port = reader_or_host, writer_or_port
        reader = writer = None
        retry_delay = 0.2
        max_retries = 50  # 10 seconds total
        for attempt in range(max_retries):
            if process.returncode is not None:
                raise RuntimeError(f"the door exited (code {process.returncode}) "
                                   f"before opening its socket")
            try:
                reader, writer = await asyncio.open_connection(host, port)
                break
            except OSError:
                await asyncio.sleep(retry_delay)
        else:
            raise RuntimeError(f"the door did not open its socket on port {port} "
                               f"within {max_retries * retry_delay:.0f} s")
        log.debug("Connected to door socket at %s:%s", host, port)
    else:
        # DOSBox door: connection already established, reader/writer passed directly
        reader, writer = reader_or_host, writer_or_port

    async def watch_process():
        """Wait for the door subprocess to exit."""
        while process.returncode is None:
            await asyncio.sleep(0.25)
        return ENDED_BY_DOOR

    try:
        return await _run_until_first_done(
            _pump_user_to_door(user, _DoorInput(door_conf), writer.write, writer.drain),
            _pump_door_to_user(user, reader.read, emulator, session_log),
            watch_process(),
            output=1,
        )
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def _bridge_stdio(user, process, door_conf, emulator=None, session_log=None):
    """Bridge data between the user's telnet connection and a subprocess's stdin/stdout."""
    try:
        return await _run_until_first_done(
            _pump_user_to_door(user, _DoorInput(door_conf), process.stdin.write, process.stdin.drain,
                               still_running=lambda: process.returncode is None),
            _pump_door_to_user(user, process.stdout.read, emulator, session_log),
            output=1,
        )
    finally:
        # A door that is still running sees its input end (its "carrier
        # drop"), so it can save and exit within the hangup grace.
        try:
            process.stdin.close()
        except Exception:
            pass


DOSBOX_CONNECT_SECS = 60.0  # how long DOSBox-X may take to start and connect


class _DoorStartError(Exception):
    """The door could not be started; the message is for the caller."""


async def _wait_for_dosbox(conn_future, process, timeout):
    """Wait for DOSBox-X (*process*) to connect to our listener.

    *conn_future* gets the connection's (reader, writer), which this returns.
    Raises _DoorStartError if DOSBox-X exits first (a bad setting, say) or
    hasn't connected within *timeout* seconds.
    """
    exited = asyncio.ensure_future(process.wait())
    try:
        await asyncio.wait([conn_future, exited], timeout=timeout,
                           return_when=asyncio.FIRST_COMPLETED)
    finally:
        if not exited.done():
            exited.cancel()
    if conn_future.done():
        return conn_future.result()
    conn_future.cancel()  # so a connection that still comes in gets closed
    if process.returncode is not None:
        raise _DoorStartError(f"DOSBox-X exited (code {process.returncode}) before the door started.")
    raise _DoorStartError("Door timed out (DOSBox did not connect).")


def _log_dosbox_output(node_dir, door_name, node_num):
    """Log what DOSBox-X wrote to the session's dosbox.log; returns it (or None)."""
    path = os.path.join(node_dir, "dosbox.log")
    try:
        with open(path, "r", errors="replace") as f:
            contents = f.read().strip()
    except OSError:
        return None
    if contents:
        log.debug("DOSBox log for %s node %s:\n%s", door_name, node_num, contents)
    return contents


async def _stop_process(process, grace):
    """Give *process* up to *grace* seconds to exit by itself, then terminate
    it (kill it if that fails).  Returns True if it had to be stopped."""
    if process is None or process.returncode is not None:
        return False
    try:
        await asyncio.wait_for(process.wait(), timeout=grace)
        return False
    except asyncio.TimeoutError:
        pass
    try:
        process.terminate()
        await asyncio.wait_for(process.wait(), timeout=5.0)
    except asyncio.TimeoutError:
        log.warning("Door process did not exit after terminate, killing it")
        try:
            process.kill()
            await asyncio.wait_for(process.wait(), timeout=3.0)
        except Exception:
            pass
    except Exception:
        pass
    return True


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def run(user, destination, menu_item=None):
    """Launch a door game for *user*.

    Parameters
    ----------
    user : User
        The connected BBS user.
    destination : config object
        The ``destinations.door`` config (base_path, max_nodes, etc.).
    menu_item : str or config object, optional
        The name or config of the specific door chosen from the menu.
        When called from the menu system this is the menu option name
        (e.g. ``"Trade Wars 2002"``).
    """

    # ---- resolve door-specific configuration --------------------------------
    # menu_item may be a string (door name) or a config object.
    # If it's a string, look it up in the menu it was chosen from (any menu
    # whose option targets the door module).
    door_name = None
    door_conf = null

    if menu_item is not None and menu_item is not null:
        # menu_item is a tuple: (door_name,)
        if isinstance(menu_item, tuple):
            door_name = str(menu_item[-1])
        elif isinstance(menu_item, str):
            door_name = menu_item
        else:
            door_conf = menu_item
            door_name = getattr(menu_item, "name", None) or "unknown_door"
        if door_conf is null and door_name:
            door_conf = _find_door_conf(user, door_name)
            if door_conf is null or not door_conf:
                door_conf = null

    if door_conf is null or not door_conf:
        log.warning("No door configuration found for menu_item=%s", menu_item)
        return RetVals(status=fail, err_msg="Door not found or not configured.",
                       next_destination=null, next_menu_item=null)

    if door_name is None:
        door_name = "unknown_door"

    # Per-door access: white_keys/black_keys on the door's own entry (e.g. an
    # adult door, or a sysop-only config tool) on top of the door module's keys.
    from common import check_keys, access_denied_message
    access = check_keys(user, door_conf)
    if access.status == fail:
        return RetVals(status=fail, err_msg=access_denied_message(door_name, access),
                       next_destination=null, next_menu_item=null)

    # ---- resolve paths -------------------------------------------------------
    door_dir = _resolve_door_dir(door_conf, _base_path())
    if not os.path.isdir(door_dir):
        msg = f"{door_name} is not installed (missing directory {door_dir})."
        log.error(msg)
        return RetVals(status=fail, err_msg=msg, next_destination=null, next_menu_item=null)
    node_key = _node_key(door_dir)

    # ---- check node limits ---------------------------------------------------
    # A null next_destination returns the user to the menu they chose the door from.
    global_max = int(conf.max_nodes) if conf.max_nodes else 20
    door_max = int(door_conf.max_nodes) if door_conf.max_nodes else global_max

    if node_key not in nodes:
        nodes[node_key] = []

    if len(nodes[node_key]) >= door_max:
        msg = f"All {door_max} node(s) for {door_name} are in use. Please try again later."
        log.warning("Node limit reached for %s (%s)", door_name, door_max)
        return RetVals(status=fail, err_msg=msg, next_destination=null, next_menu_item=null)

    if _total_active_nodes() >= global_max:
        msg = f"All {global_max} system door node(s) are in use. Please try again later."
        log.warning("Global node limit reached (%s)", global_max)
        return RetVals(status=fail, err_msg=msg, next_destination=null, next_menu_item=null)

    # ---- allocate node -------------------------------------------------------
    node_num = _allocate_node_number(node_key)

    # Enforce door_max on node number (some doors require node <= max_nodes)
    if node_num > door_max:
        msg = f"No available node slot for {door_name}."
        log.warning("Allocated node %s exceeds door max %s", node_num, door_max)
        return RetVals(status=fail, err_msg=msg, next_destination=null, next_menu_item=null)

    # Per-node dropfile directory (mounted as C: for DOSBox doors)
    node_root = _node_root(door_dir)
    node_dir = os.path.join(node_root, f"node{node_num}")
    if os.path.exists(node_dir):
        shutil.rmtree(node_dir, ignore_errors=True)  # leftover from a crashed session
    os.makedirs(node_dir, exist_ok=True)

    # Determine if native (32-bit) or DOS (16-bit via DOSBox)
    is_native = bool(door_conf.native) if door_conf.native else False

    # Determine communication type — default based on native setting
    if door_conf.communication_type:
      comm_type = str(door_conf.communication_type).upper().strip()
    else:
      comm_type = "SOCKET" if is_native else "COM"

    # Warn on contradictory settings
    if is_native and comm_type in ("COM", "FOSSIL"):
      log.warning("Door '%s' is native=true but communication_type=%s (COM/FOSSIL requires DOSBox). "
                   "Treating as non-native.", door_name, comm_type)
      is_native = False
    elif not is_native and comm_type in ("SOCKET", "STDIO"):
      log.warning("Door '%s' is native=false but communication_type=%s. "
                   "Treating as native.", door_name, comm_type)
      is_native = True

    in_dosbox = comm_type in ("COM", "FOSSIL")
    # A native socket door listens on a port we choose and pass to it.  For
    # DOSBox doors we listen and DOSBox connects; that port is assigned by the
    # OS when the listener is bound (choosing a "free" one first would race
    # with other sessions and other BBS instances).
    socket_port = None if in_dosbox else _find_free_port(5000 + node_num)

    # ---- create node object --------------------------------------------------
    node = Node(
        node_num=node_num,
        user=user,
        process=None,
        node_dir=node_dir,
        socket_port=socket_port,
        door_name=door_name,
    )
    nodes[node_key].append(node)

    log.info("Starting %s on node %s for user %s (comm=%s)",
             door_name, node_num, getattr(user, 'handle', '?'), comm_type)

    # Create ANSI emulator to track screen state during door session
    emulator = AnsiEmulator(user)
    user.in_door = True
    user.popup_event = asyncio.Event()
    dosbox_log_file = None
    dosbox_tcp_server = None
    ended_by = ENDED_BY_DOOR
    daily_marked = False  # this session is the day's first: it runs the daily commands
    dosbox_log_read = False

    try:
        # ---- notify user of escape sequence ----------------------------------
        from input_fields import show_message_box
        await show_message_box(
            user,
            text=f"Launching {door_name}.\n\nPress Ctrl+X three times to exit if the door hangs.",
            title="Door",
        )
        # Start the door on a clean screen (and in the emulator's copy of it)
        await ansi_cls(user)
        # A door written for a 24-line screen (screen_rows: 24) gets a scroll
        # region of that height, so it scrolls where it expects to.
        door_rows = _door_rows(user, door_conf)
        if door_rows < _screen_rows(user):
            await ansi_set_region(user, 1, door_rows, drain=True)
            emulator.scroll_bottom = door_rows

        if in_dosbox:
            # Listen *before* writing the DOSBox config and launching DOSBox, so
            # the port is already bound when DOSBox finishes booting and connects.
            dosbox_conn_future = asyncio.get_event_loop().create_future()

            def _on_dosbox_connect(r, w):
                if not dosbox_conn_future.done():
                    dosbox_conn_future.set_result((r, w))
                else:
                    w.close()

            dosbox_tcp_server = await asyncio.start_server(_on_dosbox_connect, "127.0.0.1", 0)
            socket_port = dosbox_tcp_server.sockets[0].getsockname()[1]
            node.socket_port = socket_port
            log.debug("Listening for DOSBox on 127.0.0.1:%s", socket_port)

        # ---- build variable dict (must come before dropfiles) ----------------
        config_path = os.path.join(node_dir, "dosbox_door.conf")
        # Raw door output of the most recent session on this node (kept after exit, for debugging)
        session_log_path = os.path.join(node_root, f"session{node_num}.log")
        variables = _build_vars(user, node_num, node_dir, door_conf, socket_port, config_path,
                                in_dosbox=in_dosbox)

        # ---- generate dropfiles ----------------------------------------------
        _write_all_dropfiles(user, node_num, node_dir, door_conf, variables, in_dosbox,
                             socket_handle=socket_port)

        # ---- launch door -----------------------------------------------------
        command_template = str(door_conf.command) if door_conf.command else ""

        if in_dosbox:
            daily_marked = _daily_commands_due(door_dir, door_conf)
            dosbox_config = _generate_dosbox_config(
                node_dir, door_dir, door_conf, variables, socket_port, run_daily=daily_marked,
            )
            with open(config_path, "w") as f:
                f.write(dosbox_config)

            dosbox_exe = str(conf.dosbox_path) if conf.dosbox_path else "dosbox"
            dosbox_base_conf = paths.resolve_project(str(door_conf.dosbox_conf)) if door_conf.dosbox_conf else ""
            dosbox_log_path = os.path.join(node_dir, "dosbox.log")
            dosbox_log_file = open(dosbox_log_path, "w")
            log.debug("Launching DOSBox (%s) with config %s, log %s", dosbox_exe, config_path, dosbox_log_path)
            dosbox_cmd = [dosbox_exe, "-noconsole", "-noprimaryconf", "-nosecondaryconf"]
            if dosbox_base_conf and os.path.exists(dosbox_base_conf):
                dosbox_cmd += ["-conf", dosbox_base_conf]
            else:
                if dosbox_base_conf:
                    log.warning("dosbox_conf not found: %s", dosbox_base_conf)
            dosbox_cmd += ["-conf", config_path]
            process = await asyncio.create_subprocess_exec(
                *dosbox_cmd,
                stdout=dosbox_log_file,
                stderr=dosbox_log_file,
            )
            node.process = process

            # Wait for DOSBox to connect, then close the listener
            try:
                door_reader, door_writer = await _wait_for_dosbox(
                    dosbox_conn_future, process, DOSBOX_CONNECT_SECS)
            except _DoorStartError as e:
                log.error("%s: %s (port %s)", door_name, e, socket_port)
                return RetVals(status=fail, err_msg=str(e), next_destination=null, next_menu_item=null)
            finally:
                dosbox_tcp_server.close()  # stop accepting new connections

            log.debug("DOSBox connected on port %s", socket_port)
            with _SessionLog(session_log_path) as session_log:
                ended_by = await _bridge_socket(user, door_reader, door_writer, process, door_conf, emulator, session_log=session_log)

        elif comm_type == "SOCKET":
            # Native socket door (DOOR32 style): launch process, bridge via TCP socket
            resolved_cmd = _safe_format(command_template, variables)
            cmd_parts = resolved_cmd.split()

            log.debug("Launching native socket door: %s (cwd=%s)", resolved_cmd, door_dir)
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                cwd=door_dir,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            node.process = process

            with _SessionLog(session_log_path) as session_log:
                ended_by = await _bridge_socket(user, "127.0.0.1", socket_port, process, door_conf, emulator, session_log=session_log)

        elif comm_type == "STDIO":
            # Native stdio door: launch process, bridge via stdin/stdout pipes
            resolved_cmd = _safe_format(command_template, variables)
            cmd_parts = resolved_cmd.split()

            log.debug("Launching native stdio door: %s (cwd=%s)", resolved_cmd, door_dir)
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                cwd=door_dir,
            )
            node.process = process

            with _SessionLog(session_log_path) as session_log:
                ended_by = await _bridge_stdio(user, process, door_conf, emulator, session_log=session_log)

        else:
            log.error("Unknown communication type: %s", comm_type)
            return RetVals(status=fail, err_msg=f"Unknown door communication type: {comm_type}",
                           next_destination=null, next_menu_item=null)

        # Give the door time to finish, then terminate it.  When the door exits
        # by itself, DOSBox runs the autoexec 'exit' right after closing the
        # serial connection.  When the caller hung up or aborted, the door sees
        # its carrier drop (the connection to DOSBox is closed by now) and needs
        # a few seconds to save the player and clear its "online" records --
        # killing it at once leaves those behind.
        grace = DOOR_EXIT_GRACE if ended_by == ENDED_BY_DOOR else HANGUP_EXIT_GRACE
        terminated = await _stop_process(node.process, grace)

        rc = node.process.returncode if node.process else None
        if dosbox_log_file:
            dosbox_log_file.close()
            dosbox_log_file = None
        log.info("%s node %s exited with code %s", door_name, node_num, rc)

        # Log DOSBox's output, and show it to a debug user if DOSBox failed
        dosbox_log_contents = _log_dosbox_output(node_dir, door_name, node_num)
        dosbox_log_read = True
        # DOSBox itself failed: show its log, but only to users with the debug
        # key -- it is internal detail, not something an ordinary caller needs.
        if rc and not terminated and dosbox_log_contents and "debug" in getattr(user, "keys", ()):
            await send(user, cr + lf + "--- DOSBox log ---" + cr + lf, drain=True)
            for _line in dosbox_log_contents.splitlines()[-40:]:
                # the log can contain characters the caller's encoding (CP437) lacks
                _line = _line.encode("cp437", errors="replace").decode("cp437")
                await send(user, _line + cr + lf)
            await send(user, "--- end ---" + cr + lf, drain=True)

    except Disconnected:
        log.info("User disconnected while in %s node %s", door_name, node_num)
        raise  # (the door process is stopped below)

    except Exception as e:
        log.error("Error running %s node %s: %s", door_name, node_num, e)
        return RetVals(status=fail, err_msg=f"Door error: {e}",
                       next_destination=null, next_menu_item=null)

    finally:
        # ---- cleanup ---------------------------------------------------------
        try:
            # A door still running here is one whose session failed (DOSBox
            # never connected, an error, the caller gone before it started):
            # stop it before its node directory goes and the node is reused.
            await _stop_process(node.process, 0)
        finally:
            # (even if that wait was interrupted)
            if node.process and node.process.returncode is None:
                try:
                    node.process.kill()
                except Exception:
                    pass
            user.in_door = False
            user.popup_event = None
            _release_node(node_key, node)
            if dosbox_tcp_server is not None:
                dosbox_tcp_server.close()  # no-op if already closed after DOSBox connected
            if dosbox_log_file:
                try:
                    dosbox_log_file.close()
                except Exception:
                    pass
            if in_dosbox and not dosbox_log_read:
                _log_dosbox_output(node_dir, door_name, node_num)
            if daily_marked:
                _settle_daily_mark(door_dir, node_dir, door_name)  # (before node_dir goes)
            # Remove the node directory (the next session on the node empties
            # it again if something in it was still held open)
            shutil.rmtree(node_dir, ignore_errors=True)
            if os.path.exists(node_dir):
                log.error("Could not remove all of node dir %s", node_dir)
            log.debug("Cleaned up %s node %s", door_name, node_num)
        try:
            # back to the full screen, and undo any mode the door left set
            # (its own scroll region, origin mode, a hidden cursor, ...)
            await ansi_reset_modes(user, drain=True)
        except Exception:
            pass  # caller already gone

    await send(user, cr + lf + "Returning to BBS..." + cr + lf, drain=True)
    # null: back to the menu the door was chosen from (see common.do_destination)
    return RetVals(status=success, next_destination=null, next_menu_item=null)
