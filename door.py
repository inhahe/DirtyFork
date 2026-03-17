"""
BBS Door Game System

Handles launching DOS and native door games, managing node allocation,
generating dropfiles, bridging data between the user's telnet connection
and the door process (via TCP socket for DOSBox/DOOR32, or stdio pipes
for native doors).
"""

import asyncio
import os
import shutil
import socket
import tempfile
import time

from definitions import *
from input_output import send
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


# key = door name, value = list of active Node instances
nodes = {}


def _total_active_nodes():
    """Return the total number of active nodes across all doors."""
    return sum(len(v) for v in nodes.values())


def _allocate_node_number(door_name):
    """Find the lowest available node number for *door_name*."""
    if door_name not in nodes:
        nodes[door_name] = []
    used = {n.node_num for n in nodes[door_name]}
    num = 1
    while num in used:
        num += 1
    return num


def _release_node(door_name, node):
    """Remove *node* from the active list for *door_name*."""
    if door_name in nodes:
        try:
            nodes[door_name].remove(node)
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


def _screen_cols(user):
    return getattr(user, "screen_width", None) or 80


def _time_remaining_secs():
    return 3600  # 60 minutes default


def _time_remaining_mins():
    return 60


def _generate_door_sys(user, node_num, node_dir):
    """Generate DOOR.SYS (PCBoard format)."""
    handle = getattr(user, "handle", None) or "Unknown"
    location = _user_location(user)
    bbs = _bbs_name()
    sysop = _sysop_name()
    rows = _screen_rows(user)
    mins = _time_remaining_mins()
    secs = _time_remaining_secs()

    lines = [
        "COM1:",             # COM port
        "115200",            # baud rate
        "8",                 # data bits
        str(node_num),       # node number
        "Y",                 # screen display locked
        "N",                 # printer toggle
        "Y",                 # page bell
        "Y",                 # caller alarm
        handle,              # user name
        location,            # user location
        "000-000-0000",      # home phone
        "000-000-0000",      # work phone
        "PASSWORD",          # password placeholder
        "0",                 # security level
        "0",                 # total calls
        "01/01/00",          # last call date
        str(secs),           # seconds remaining
        str(mins),           # minutes remaining
        "GR",                # graphics mode (GR = ANSI)
        str(rows),           # screen height
        "N",                 # expert mode
        "",                  # conferences registered in
        "",                  # conference last access
        "",                  # expiration date
        "1",                 # user record number
        "Y",                 # default protocol
        "0",                 # total uploads
        "0",                 # total downloads
        "0",                 # daily download k limit
        "0",                 # daily download k so far
        "01/01/00",          # birthday
        "",                  # path to user database
        node_dir,            # path to door directory
        bbs,                 # BBS name
        sysop,               # sysop name
        "00:00",             # event time
        "Y",                 # error correcting connection
        "N",                 # ANSI in file transfers
        "",                  # default BBS color
        "0",                 # time credits in minutes
        "01/01/00",          # last new file scan
        "00:00:00",          # time of call
        "00:00:00",          # last time on
        "8",                 # max daily files
        "0",                 # files downloaded today
        "0",                 # total uploads k
        "0",                 # total downloads k
        "",                  # comment
        "0",                 # total doors opened
        "0",                 # messages left
    ]
    return "\r\n".join(lines) + "\r\n"


def _generate_dorinfo(user, node_num):
    """Generate DORINFO1.DEF format."""
    bbs = _bbs_name()
    sysop_first, sysop_last = _sysop_first_last()
    user_first, user_last = _user_first_last(user)
    location = _user_location(user)
    mins = _time_remaining_mins()

    lines = [
        bbs,                          # BBS name
        sysop_first,                  # sysop first name
        sysop_last,                   # sysop last name
        "COM1",                       # COM port
        "115200 BAUD,N,8,1",          # baud/parity/data/stop
        "0",                          # network type (0 = gone)
        user_first,                   # user first name
        user_last,                    # user last name
        location,                     # location
        "1",                          # ANSI (0=no, 1=yes, 2=RIP)
        "0",                          # security level
        str(mins),                    # minutes remaining
        "-1",                         # fossil flag (-1 = fossil)
    ]
    return "\r\n".join(lines) + "\r\n"


def _generate_chain_txt(user, node_num, node_dir):
    """Generate CHAIN.TXT (WWIV format)."""
    handle = getattr(user, "handle", None) or "Unknown"
    age = _user_age(user)
    sex = _user_sex(user)
    rows = _screen_rows(user)
    cols = _screen_cols(user)
    sysop = _sysop_name()
    bbs = _bbs_name()
    secs = float(_time_remaining_secs())

    # CHAIN.TXT expects the node directory with trailing backslash
    nd = node_dir.replace("/", "\\")
    if not nd.endswith("\\"):
        nd += "\\"

    lines = [
        "1",                # user number
        handle,             # user handle
        handle,             # real name
        "",                 # callsign
        str(age),           # age
        sex,                # sex
        "0",                # gold
        "01/01/00",         # last login
        str(cols),          # columns
        str(rows),          # rows
        "0",                # security level
        "0",                # co-sysop flag
        "1",                # ANSI (1=yes)
        "0",                # remote (0=local)
        f"{secs:.1f}",      # seconds remaining
        nd,                 # node directory with trailing slash
        "",                 # not used
        "",                 # not used
        sysop,              # sysop name
        bbs,                # bbs name
        "",                 # not used
        "COM1",             # com port
        "0000000",          # not used
        "115200",           # baud rate
        "",                 # not used
        str(node_num),      # node number
    ]
    return "\r\n".join(lines) + "\r\n"


def _generate_door32_sys(user, node_num, socket_handle=0):
    """Generate DOOR32.SYS (modern format)."""
    handle = getattr(user, "handle", None) or "Unknown"
    bbs = _bbs_name()
    mins = _time_remaining_mins()

    lines = [
        "2",                # comm type (2 = telnet)
        str(socket_handle), # socket/comm handle
        "115200",           # baud rate
        bbs,                # BBS software name
        "1",                # user record number
        handle,             # user display name
        handle,             # real name
        handle,             # handle
        "0",                # security level
        str(mins),          # time remaining minutes
        "1",                # emulation (1 = ANSI)
        str(node_num),      # current node number
    ]
    return "\r\n".join(lines) + "\r\n"


def _generate_sfdoors_dat(user, node_num):
    """Generate SFDOORS.DAT (Spitfire format)."""
    handle = getattr(user, "handle", None) or "Unknown"
    bbs = _bbs_name()
    sysop = _sysop_name()

    lines = [
        "1",                # user record number
        handle,             # user name
        "",                 # password placeholder
        "0",                # security level
        str(_time_remaining_mins()),  # minutes remaining
        "1",                # ANSI (1=yes)
        str(node_num),      # node number
        bbs,                # BBS name
        sysop,              # sysop name
        "115200",           # baud rate
        "COM1",             # COM port
        "8",                # data bits
        "1",                # stop bits
        "N",                # parity
    ]
    return "\r\n".join(lines) + "\r\n"


def _generate_callinfo_bbs(user, node_num):
    """Generate CALLINFO.BBS (Wildcat format)."""
    handle = getattr(user, "handle", None) or "Unknown"
    location = _user_location(user)
    sysop = _sysop_name()
    bbs = _bbs_name()
    mins = _time_remaining_mins()
    secs = _time_remaining_secs()

    lines = [
        handle,             # user name
        "1",                # speed/baud
        location,           # user location
        "0",                # security level
        str(mins),          # time remaining
        "ANSI",             # emulation
        str(node_num),      # node number
        "",                 # screen door path
        "",                 # BBS directory
        sysop,              # sysop name
        handle,             # user alias
        "00:00",            # time of logon
        str(secs),          # seconds remaining
        "115200",           # baud rate
        "1",                # com port number
        bbs,                # BBS name
    ]
    return "\r\n".join(lines) + "\r\n"


def _write_all_dropfiles(user, node_num, node_dir, socket_handle=0):
    """Write every supported dropfile format into *node_dir*."""
    files = {
        "DOOR.SYS": _generate_door_sys(user, node_num, node_dir),
        f"DOOR{node_num}.SYS": _generate_door_sys(user, node_num, node_dir),
        "DORINFO1.DEF": _generate_dorinfo(user, node_num),
        f"DORINFO{node_num}.DEF": _generate_dorinfo(user, node_num),
        "CHAIN.TXT": _generate_chain_txt(user, node_num, node_dir),
        "DOOR32.SYS": _generate_door32_sys(user, node_num, socket_handle),
        "SFDOORS.DAT": _generate_sfdoors_dat(user, node_num),
        "CALLINFO.BBS": _generate_callinfo_bbs(user, node_num),
    }
    for name, content in files.items():
        path = os.path.join(node_dir, name)
        with open(path, "w", newline="") as f:
            f.write(content)
    return files


# ---------------------------------------------------------------------------
# Command-line variable substitution
# ---------------------------------------------------------------------------

def _build_vars(user, node_num, node_dir, door_conf, socket_port, config_path=""):
    """Build the dict used for {variable} substitution in the door command."""
    handle = getattr(user, "handle", None) or "Unknown"
    base_path = str(conf.base_path) if conf.base_path else "c:\\doors"
    door_dir = _resolve_door_dir(door_conf, base_path)

    dropfile_type = str(door_conf.dropfile_type) if door_conf.dropfile_type else "DOOR.SYS"
    dropfile_path = os.path.join(node_dir, dropfile_type)

    return {
        "node": str(node_num),
        "com": "1",
        "baud": "115200",
        "dropfile_path": dropfile_path,
        "dropfile_dir": node_dir,
        "dropfile_type": dropfile_type,
        "config_path": config_path,
        "time_limit": str(_time_remaining_mins()),
        "handle": handle,
        "socket_handle": str(socket_port),
        "graphics_mode": "ANSI",
        "bbs_software": "DirtyFork",
        "bbs_name": _bbs_name(),
        "sysop_name": _sysop_name(),
        "data_path": door_dir,
        "rows": str(_screen_rows(user)),
        "cols": str(_screen_cols(user)),
        "irq": "4",
        "io_port": "3F8",
        "uart_type": "16550",
        "node_dir": node_dir,
        "socket_port": str(socket_port),
    }


def _safe_format(template, variables):
    """Substitute {variable} placeholders using only the provided dict.

    This prevents users from injecting arbitrary format strings (e.g. via
    their handle) that could resolve against Python internals.
    """
    try:
        return template.format_map(variables)
    except (KeyError, ValueError, IndexError):
        return template


# ---------------------------------------------------------------------------
# Door directory resolution
# ---------------------------------------------------------------------------

def _resolve_door_dir(door_conf, base_path):
    """Resolve the door's directory.  Relative paths are relative to *base_path*."""
    door_dir_raw = str(door_conf.dir) if door_conf.dir else ""
    if not door_dir_raw:
        return base_path
    if os.path.isabs(door_dir_raw):
        return door_dir_raw
    return os.path.join(base_path, door_dir_raw)


# ---------------------------------------------------------------------------
# DOSBox config generation
# ---------------------------------------------------------------------------

def _generate_dosbox_config(node_dir, door_dir, door_conf, variables, socket_port):
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

    config_content = f"""[serial]
serial1=nullmodem server:127.0.0.1 port:{socket_port}

[autoexec]
mount c "{node_dir}"
mount d "{door_dir}"
c:
{copy_cmds}d:
{resolved_command}
exit
"""
    return config_content


# ---------------------------------------------------------------------------
# Data bridging
# ---------------------------------------------------------------------------

async def _bridge_socket(user, host, port, process, emulator=None):
    """Bridge data between the user's telnet connection and a TCP socket.

    Used for DOSBox (nullmodem serial) and native socket (DOOR32) doors.
    """
    reader = None
    writer = None
    retry_delay = 0.2
    max_retries = 50  # 10 seconds total

    for attempt in range(max_retries):
        if process.returncode is not None:
            log.warning("Process exited before socket connection (code %s)", process.returncode)
            return
        try:
            reader, writer = await asyncio.open_connection(host, port)
            break
        except (ConnectionRefusedError, OSError):
            await asyncio.sleep(retry_delay)
    else:
        log.error("Could not connect to door socket at %s:%s after %s retries", host, port, max_retries)
        return

    log.info("Connected to door socket at %s:%s", host, port)

    async def user_to_door():
        """Read from user's telnet reader, write to door socket.
        Pauses when a popup is active (popup_event is set)."""
        try:
            while True:
                # If a popup is active, wait for it to finish before reading user input
                if user.popup_event and user.popup_event.is_set():
                    while user.popup_event.is_set():
                        await asyncio.sleep(0.05)
                    continue
                try:
                    data = await asyncio.wait_for(user.reader.read(4096), timeout=0.1)
                except asyncio.TimeoutError:
                    continue
                if not data:
                    break
                if isinstance(data, str):
                    data = data.encode("cp437", errors="replace")
                writer.write(data)
                await writer.drain()
        except (ConnectionError, Disconnected, asyncio.CancelledError):
            pass
        except Exception as e:
            log.error("user_to_door error: %s", e)

    async def door_to_user():
        """Read from door socket, write to user's telnet writer."""
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                if isinstance(data, bytes):
                    data = data.decode("cp437", errors="replace")
                if emulator:
                    emulator.feed(data)
                user.writer.write(data)
                await user.writer.drain()
        except (ConnectionError, Disconnected, asyncio.CancelledError):
            pass
        except Exception as e:
            log.error("door_to_user error: %s", e)

    async def watch_process():
        """Wait for the door subprocess to exit."""
        while process.returncode is None:
            await asyncio.sleep(0.25)

    try:
        tasks = [
            asyncio.create_task(user_to_door()),
            asyncio.create_task(door_to_user()),
            asyncio.create_task(watch_process()),
        ]
        # When any task finishes, cancel the others
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
        for t in pending:
            try:
                await t
            except asyncio.CancelledError:
                pass
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def _bridge_stdio(user, process, emulator=None):
    """Bridge data between the user's telnet connection and a subprocess's stdin/stdout."""

    async def user_to_door():
        """Read from user's telnet reader, write to process stdin.
        Pauses when a popup is active (popup_event is set)."""
        try:
            while process.returncode is None:
                if user.popup_event and user.popup_event.is_set():
                    while user.popup_event.is_set():
                        await asyncio.sleep(0.05)
                    continue
                try:
                    data = await asyncio.wait_for(user.reader.read(4096), timeout=0.1)
                except asyncio.TimeoutError:
                    continue
                if not data:
                    break
                if isinstance(data, str):
                    data = data.encode("cp437", errors="replace")
                process.stdin.write(data)
                await process.stdin.drain()
        except (ConnectionError, Disconnected, asyncio.CancelledError):
            pass
        except Exception as e:
            log.error("user_to_door (stdio) error: %s", e)

    async def door_to_user():
        """Read from process stdout, write to user's telnet writer."""
        try:
            while True:
                data = await process.stdout.read(4096)
                if not data:
                    break
                if isinstance(data, bytes):
                    data = data.decode("cp437", errors="replace")
                if emulator:
                    emulator.feed(data)
                user.writer.write(data)
                await user.writer.drain()
        except (ConnectionError, Disconnected, asyncio.CancelledError):
            pass
        except Exception as e:
            log.error("door_to_user (stdio) error: %s", e)

    try:
        tasks = [
            asyncio.create_task(user_to_door()),
            asyncio.create_task(door_to_user()),
        ]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
        for t in pending:
            try:
                await t
            except asyncio.CancelledError:
                pass
    finally:
        pass


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
    from common import Destinations

    # ---- resolve door-specific configuration --------------------------------
    # menu_item may be a string (door name) or a config object.
    # If it's a string, look it up under menu_system.doors.options.
    door_name = None
    door_conf = null

    if menu_item is not None and menu_item is not null:
        if isinstance(menu_item, str):
            door_name = menu_item
            menu_doors = config.menu_system.doors if config.menu_system else null
            if menu_doors and menu_doors.options:
                door_conf = menu_doors.options[menu_item]
                # Apply option_defaults if present
                if door_conf is null or not door_conf:
                    door_conf = null
        else:
            # Assume it's already a config-like object
            door_conf = menu_item
            door_name = getattr(menu_item, "name", None) or "unknown_door"

    if door_conf is null or not door_conf:
        log.warning("No door configuration found for menu_item=%s", menu_item)
        await send(user, cr + lf + "Door not found or not configured." + cr + lf, drain=True)
        return RetVals(status=fail, err_msg="Door not configured",
                       next_destination=Destinations.main, next_menu_item=null)

    if door_name is None:
        door_name = "unknown_door"

    # ---- check node limits ---------------------------------------------------
    global_max = int(conf.max_nodes) if conf.max_nodes else 20
    door_max = int(door_conf.max_nodes) if door_conf.max_nodes else global_max

    if door_name not in nodes:
        nodes[door_name] = []

    if len(nodes[door_name]) >= door_max:
        msg = f"All {door_max} node(s) for {door_name} are in use. Please try again later."
        log.warning("Node limit reached for %s (%s)", door_name, door_max)
        await send(user, cr + lf + msg + cr + lf, drain=True)
        return RetVals(status=fail, err_msg=msg,
                       next_destination=Destinations.main, next_menu_item=null)

    if _total_active_nodes() >= global_max:
        msg = f"All {global_max} system door node(s) are in use. Please try again later."
        log.warning("Global node limit reached (%s)", global_max)
        await send(user, cr + lf + msg + cr + lf, drain=True)
        return RetVals(status=fail, err_msg=msg,
                       next_destination=Destinations.main, next_menu_item=null)

    # ---- allocate node -------------------------------------------------------
    node_num = _allocate_node_number(door_name)

    # Enforce door_max on node number (some doors require node <= max_nodes)
    if node_num > door_max:
        msg = f"No available node slot for {door_name}."
        log.warning("Allocated node %s exceeds door max %s", node_num, door_max)
        await send(user, cr + lf + msg + cr + lf, drain=True)
        return RetVals(status=fail, err_msg=msg,
                       next_destination=Destinations.main, next_menu_item=null)

    # ---- resolve paths -------------------------------------------------------
    base_path = str(conf.base_path) if conf.base_path else "c:\\doors"
    door_dir = _resolve_door_dir(door_conf, base_path)

    # Create temp node directory
    node_dir = os.path.join(tempfile.gettempdir(), "dirtyfork_doors", f"node{node_num}")
    os.makedirs(node_dir, exist_ok=True)

    # Determine communication type
    comm_type_raw = str(door_conf.communication_type).upper() if door_conf.communication_type else "COM"
    comm_type = comm_type_raw.strip()

    # Find a free socket port
    socket_port = _find_free_port(5000 + node_num)

    # ---- create node object --------------------------------------------------
    node = Node(
        node_num=node_num,
        user=user,
        process=None,
        config_path=None,
        node_dir=node_dir,
        socket_port=socket_port,
        door_name=door_name,
    )
    nodes[door_name].append(node)

    log.info("Starting %s on node %s for user %s (comm=%s, port=%s)",
             door_name, node_num, getattr(user, 'handle', '?'), comm_type, socket_port)

    # Create ANSI emulator to track screen state during door session
    emulator = AnsiEmulator(user)
    user.in_door = True
    user.popup_event = asyncio.Event()
    dosbox_log_file = None

    try:
        # ---- generate dropfiles ----------------------------------------------
        _write_all_dropfiles(user, node_num, node_dir, socket_handle=socket_port)

        # ---- build variable dict ---------------------------------------------
        config_path = os.path.join(node_dir, "dosbox_door.conf")
        variables = _build_vars(user, node_num, node_dir, door_conf, socket_port, config_path)

        # ---- launch door -----------------------------------------------------
        command_template = str(door_conf.command) if door_conf.command else ""

        if comm_type in ("COM", "FOSSIL"):
            # DOSBox mode: generate config, launch DOSBox, bridge via TCP socket
            dosbox_config = _generate_dosbox_config(
                node_dir, door_dir, door_conf, variables, socket_port
            )
            with open(config_path, "w") as f:
                f.write(dosbox_config)
            node.config_path = config_path

            dosbox_exe = str(conf.dosbox_path) if conf.dosbox_path else "dosbox"
            dosbox_log_path = os.path.join(node_dir, "dosbox.log")
            dosbox_log_file = open(dosbox_log_path, "w")
            log.info("Launching DOSBox (%s) with config %s, log %s", dosbox_exe, config_path, dosbox_log_path)
            process = await asyncio.create_subprocess_exec(
                dosbox_exe, "-conf", config_path, "-noconsole",
                stdout=dosbox_log_file,
                stderr=dosbox_log_file,
            )
            node.process = process

            await send(user, cr + lf + f"Launching {door_name}..." + cr + lf, drain=True)
            await _bridge_socket(user, "127.0.0.1", socket_port, process, emulator)

        elif comm_type == "SOCKET":
            # Native socket door (DOOR32 style): launch process, bridge via TCP socket
            resolved_cmd = _safe_format(command_template, variables)
            cmd_parts = resolved_cmd.split()
            cwd = door_dir if os.path.isdir(door_dir) else None

            log.info("Launching native socket door: %s (cwd=%s)", resolved_cmd, cwd)
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                cwd=cwd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            node.process = process

            await send(user, cr + lf + f"Launching {door_name}..." + cr + lf, drain=True)
            await _bridge_socket(user, "127.0.0.1", socket_port, process, emulator)

        elif comm_type == "STDIO":
            # Native stdio door: launch process, bridge via stdin/stdout pipes
            resolved_cmd = _safe_format(command_template, variables)
            cmd_parts = resolved_cmd.split()
            cwd = door_dir if os.path.isdir(door_dir) else None

            log.info("Launching native stdio door: %s (cwd=%s)", resolved_cmd, cwd)
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                cwd=cwd,
            )
            node.process = process

            await send(user, cr + lf + f"Launching {door_name}..." + cr + lf, drain=True)
            await _bridge_stdio(user, process, emulator)

        else:
            log.error("Unknown communication type: %s", comm_type)
            await send(user, cr + lf + f"Unknown door communication type: {comm_type}" + cr + lf,
                       drain=True)
            return RetVals(status=fail, err_msg=f"Unknown comm type: {comm_type}",
                           next_destination=Destinations.main, next_menu_item=null)

        # Wait for process to fully exit
        if node.process and node.process.returncode is None:
            try:
                await asyncio.wait_for(node.process.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                log.warning("Process did not exit in time, terminating")
                try:
                    node.process.terminate()
                    await asyncio.wait_for(node.process.wait(), timeout=5.0)
                except Exception:
                    try:
                        node.process.kill()
                    except Exception:
                        pass

        rc = node.process.returncode if node.process else None
        if dosbox_log_file:
            dosbox_log_file.close()
        log.info("%s node %s exited with code %s", door_name, node_num, rc)

    except Disconnected:
        log.info("User disconnected while in %s node %s", door_name, node_num)
        # Kill the door process if it's still running
        if node.process and node.process.returncode is None:
            try:
                node.process.terminate()
            except Exception:
                pass
        raise

    except Exception as e:
        log.error("Error running %s node %s: %s", door_name, node_num, e)
        # Kill the door process if it's still running
        if node.process and node.process.returncode is None:
            try:
                node.process.terminate()
            except Exception:
                pass
        await send(user, cr + lf + f"Door error: {e}" + cr + lf, drain=True)
        return RetVals(status=fail, err_msg=str(e),
                       next_destination=Destinations.main, next_menu_item=null)

    finally:
        # ---- cleanup ---------------------------------------------------------
        user.in_door = False
        user.popup_event = None
        _release_node(door_name, node)

        # Remove temp node directory
        try:
            if os.path.exists(node_dir):
                shutil.rmtree(node_dir, ignore_errors=True)
        except Exception as e:
            log.error("Failed to clean up node dir %s: %s", node_dir, e)

        # Remove DOSBox config if it exists outside node_dir
        if node.config_path and os.path.exists(node.config_path):
            try:
                os.remove(node.config_path)
            except Exception:
                pass

        log.info("Cleaned up %s node %s", door_name, node_num)

    await send(user, cr + lf + "Returning to BBS..." + cr + lf, drain=True)
    return RetVals(status=success, next_destination=Destinations.main, next_menu_item=null)
