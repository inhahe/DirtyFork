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
import time
import paths

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


def _generate_door_sys(user, node_num, node_dir, door_conf, variables):
    """Generate DOOR.SYS (PCBoard format)."""
    df = door_conf.door_sys if door_conf else null
    gdf = lambda key, default: _get_df(df, key, default, variables)

    lines = [
        "COM1:",                                   # COM port (always COM1 in DOSBox)
        gdf("baud_rate", "115200"),                # baud rate
        "8",                                       # data bits (always 8)
        variables["node"],                         # node number
        gdf("screen_display", "Y"),                # screen display locked
        gdf("printer_toggle", "N"),                # printer toggle
        gdf("page_bell", "Y"),                     # page bell
        gdf("caller_alarm", "Y"),                  # caller alarm
        variables["handle"],                       # user name
        variables["location"],                     # user location
        gdf("home_phone", ""),                     # home phone
        gdf("work_phone", ""),                     # work phone
        gdf("password", ""),                       # password placeholder
        gdf("security_level", "0"),                # security level
        gdf("times_called", "0"),                  # total calls
        gdf("last_call_date", "01/01/00"),         # last call date
        variables["secs_remaining"],               # seconds remaining
        variables["mins_remaining"],               # minutes remaining
        "GR",                                      # graphics mode (GR = ANSI, always)
        variables["rows"],                         # screen height
        gdf("expert_mode", "N"),                   # expert mode
        gdf("conferences", ""),                    # conferences registered in
        gdf("conf_joined", ""),                    # conference last access
        gdf("expiration_date", ""),                # expiration date
        gdf("user_record", "1"),                   # user record number
        gdf("protocol", "Z"),                      # default protocol
        gdf("uploads", "0"),                       # total uploads
        gdf("downloads", "0"),                     # total downloads
        gdf("daily_dl_k", "0"),                    # daily download k limit
        gdf("dl_k_today", "0"),                    # daily download k so far
        gdf("birthday", ""),                       # birthday
        gdf("user_db_path", ""),                   # path to user database
        node_dir,                                  # path to door directory
        variables["bbs_name"],                     # BBS name
        variables["sysop_name"],                   # sysop name
        gdf("event_time", "00:00"),                # event time
        gdf("error_correcting", "Y"),              # error correcting connection
        gdf("ansi_in_transfer", "N"),              # ANSI in file transfers
        gdf("default_color", ""),                  # default BBS color
        gdf("time_credits", "0"),                  # time credits in minutes
        gdf("last_new_scan", "01/01/00"),          # last new file scan
        gdf("time_of_call", "00:00:00"),           # time of call
        gdf("last_time_on", "00:00:00"),           # last time on
        gdf("max_daily_files", "999"),             # max daily files
        gdf("files_today", "0"),                   # files downloaded today
        gdf("total_ul_k", "0"),                    # total uploads k
        gdf("total_dl_k", "0"),                    # total downloads k
        gdf("comment", ""),                        # comment
        gdf("total_doors", "0"),                   # total doors opened
        gdf("messages_left", "0"),                 # messages left
    ]
    return "\r\n".join(lines) + "\r\n"


def _generate_dorinfo(user, node_num, door_conf, variables):
    """Generate DORINFO1.DEF format."""
    df = door_conf.dorinfo if door_conf else null
    gdf = lambda key, default: _get_df(df, key, default, variables)

    sysop_first, sysop_last = _sysop_first_last()

    lines = [
        variables["bbs_name"],                     # BBS name
        sysop_first,                               # sysop first name
        sysop_last,                                # sysop last name
        gdf("com_port", "COM1"),                   # COM port
        gdf("baud_parity", "115200 BAUD,N,8,1"),   # baud/parity/data/stop
        gdf("network_type", "0"),                  # network type (0 = none)
        variables["first_name"],                   # user first name
        variables["last_name"],                    # user last name
        variables["location"],                     # location
        gdf("ansi", "1"),                          # ANSI (0=no, 1=yes, 2=RIP)
        gdf("security_level", "0"),                # security level
        variables["mins_remaining"],               # minutes remaining
        "-1",                                      # fossil flag (-1 = fossil, always)
    ]
    return "\r\n".join(lines) + "\r\n"


def _generate_chain_txt(user, node_num, node_dir, door_conf, variables):
    """Generate CHAIN.TXT (WWIV format)."""
    df = door_conf.chain_txt if door_conf else null
    gdf = lambda key, default: _get_df(df, key, default, variables)

    # CHAIN.TXT expects the node directory with a trailing backslash
    nd = node_dir.replace("/", "\\")
    if not nd.endswith("\\"):
        nd += "\\"

    lines = [
        gdf("user_record", "1"),                   # user record number
        variables["handle"],                       # user handle
        variables["handle"],                       # real name (same as handle)
        "",                                        # callsign (not used)
        variables["age"],                          # age
        variables["sex"],                          # sex
        gdf("gold", "0"),                          # gold/credits
        gdf("last_login", "01/01/00"),             # last login date
        variables["cols"],                         # screen width
        variables["rows"],                         # screen rows
        gdf("security_level", "0"),                # security level
        gdf("co_sysop", "0"),                      # co-sysop flag
        gdf("ansi", "1"),                          # ANSI (1=yes)
        gdf("remote", "0"),                        # remote flag
        variables["secs_remaining"],               # seconds remaining
        nd,                                        # node directory with trailing backslash
        "",                                        # (reserved)
        "",                                        # (reserved)
        variables["sysop_name"],                   # sysop name
        variables["bbs_name"],                     # BBS name
        "",                                        # (reserved)
        "COM1",                                    # COM port (always COM1)
        "0000000",                                 # (reserved)
        variables["baud"],                         # baud rate
        "",                                        # (reserved)
        variables["node"],                         # node number
    ]
    return "\r\n".join(lines) + "\r\n"


def _generate_door32_sys(user, node_num, socket_handle, door_conf, variables):
    """Generate DOOR32.SYS (modern 32-bit format)."""
    df = door_conf.door32_sys if door_conf else null
    gdf = lambda key, default: _get_df(df, key, default, variables)

    lines = [
        gdf("comm_type", "2"),                     # comm type (2 = telnet)
        str(socket_handle),                        # socket/comm handle (always dynamic)
        gdf("baud_rate", "115200"),                # baud rate
        variables["bbs_name"],                     # BBS software name
        "1",                                       # user record number
        variables["handle"],                       # user display name
        variables["handle"],                       # real name
        variables["handle"],                       # handle
        gdf("security_level", "0"),                # security level
        variables["mins_remaining"],               # time remaining minutes
        gdf("emulation", "1"),                     # emulation (1 = ANSI)
        variables["node"],                         # current node number
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


def _write_all_dropfiles(user, node_num, node_dir, door_conf, variables, socket_handle=0):
    """Write every supported dropfile format into *node_dir*."""
    files = {
        "DOOR.SYS":            _generate_door_sys(user, node_num, node_dir, door_conf, variables),
        f"DOOR{node_num}.SYS": _generate_door_sys(user, node_num, node_dir, door_conf, variables),
        "DORINFO1.DEF":        _generate_dorinfo(user, node_num, door_conf, variables),
        f"DORINFO{node_num}.DEF": _generate_dorinfo(user, node_num, door_conf, variables),
        "CHAIN.TXT":           _generate_chain_txt(user, node_num, node_dir, door_conf, variables),
        "DOOR32.SYS":          _generate_door32_sys(user, node_num, socket_handle, door_conf, variables),
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

def _build_vars(user, node_num, node_dir, door_conf, socket_port, config_path=""):
    """Build the dict used for {variable} substitution in the door command."""
    handle = getattr(user, "handle", None) or "Unknown"
    base_path = paths.resolve_project(str(conf.base_path)) if conf.base_path else paths.resolve_project("doors")
    door_dir = _resolve_door_dir(door_conf, base_path)

    dropfile_type = str(door_conf.dropfile_type) if door_conf.dropfile_type else "DOOR.SYS"
    dropfile_path = os.path.join(node_dir, dropfile_type)

    user_first, user_last = _user_first_last(user)

    base_vars = {
        "node": str(node_num),
        "com": "1",
        "baud": "115200",
        "dropfile_path": dropfile_path,
        "dropfile_dir": node_dir,
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

    # Only [serial] and [autoexec] go here; everything else lives in the
    # sysop-editable doors/dosbox.conf which is loaded first by DOSBox-X.
    config_content = f"""[serial]
serial1=nullmodem server:127.0.0.1 port:{socket_port} transparent:1 baudrate:115200

[autoexec]
mount c "{node_dir}"
mount d "{door_dir}"
c:
{copy_cmds}d:
CALL {resolved_command}
exit
"""
    return config_content


# ---------------------------------------------------------------------------
# Data bridging
# ---------------------------------------------------------------------------

async def _bridge_socket(user, reader_or_host, writer_or_port, process, emulator=None, session_log=None):
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
                log.warning("Process exited before socket connection (code %s)", process.returncode)
                return
            try:
                reader, writer = await asyncio.open_connection(host, port)
                break
            except (ConnectionRefusedError, OSError):
                await asyncio.sleep(retry_delay)
        else:
            log.error("Could not connect to door socket at %s:%s after %s retries",
                      host, port, max_retries)
            return
        log.debug("Connected to door socket at %s:%s", host, port)
    else:
        # DOSBox door: connection already established, reader/writer passed directly
        reader, writer = reader_or_host, writer_or_port

    # Three Ctrl+X (0x18) presses within 2 seconds aborts the door session.
    ESCAPE_CHAR = b'\x18'
    ESCAPE_COUNT = 3
    ESCAPE_WINDOW = 2.0
    _escape_hits = 0
    _escape_last = 0.0

    async def _show_queued_popups():
        """Show all queued popups, then clear the popup event."""
        from input_fields import show_message_box as _show_mb
        user._in_popup = True
        try:
            while user.popup_queue:
                kwargs = user.popup_queue.pop(0)
                r = await _show_mb(user, queued_count=len(user.popup_queue), **kwargs)
                if r == "abort":
                    user.popup_queue.clear()
                    break
        finally:
            user._in_popup = False
            user.popup_event.clear()

    async def user_to_door():
        """Read from user's telnet reader, write to door socket.
        Pauses when a popup is active (popup_event is set).
        Three Ctrl+] within 2 seconds abort the session."""
        nonlocal _escape_hits, _escape_last
        try:
            while True:
                if user.popup_event and user.popup_event.is_set():
                    await _show_queued_popups()
                    continue
                try:
                    data = await asyncio.wait_for(user.reader.read(4096), timeout=0.1)
                except asyncio.TimeoutError:
                    continue
                if not data:
                    break
                if isinstance(data, str):
                    data = data.encode("cp437", errors="replace")

                # Check for escape sequence
                now = asyncio.get_event_loop().time()
                for byte in data:
                    if bytes([byte]) == ESCAPE_CHAR:
                        if now - _escape_last > ESCAPE_WINDOW:
                            _escape_hits = 0
                        _escape_hits += 1
                        _escape_last = now
                        if _escape_hits >= ESCAPE_COUNT:
                            log.info("User aborted door session via escape sequence")
                            return
                    else:
                        _escape_hits = 0

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
                if session_log:
                    session_log.write(data)
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


async def _bridge_stdio(user, process, emulator=None, session_log=None):
    """Bridge data between the user's telnet connection and a subprocess's stdin/stdout."""

    ESCAPE_CHAR = b'\x18'
    ESCAPE_COUNT = 3
    ESCAPE_WINDOW = 2.0
    _escape_hits = 0
    _escape_last = 0.0

    async def user_to_door():
        """Read from user's telnet reader, write to process stdin.
        Pauses when a popup is active (popup_event is set).
        Three Ctrl+] within 2 seconds abort the session."""
        nonlocal _escape_hits, _escape_last
        try:
            while process.returncode is None:
                if user.popup_event and user.popup_event.is_set():
                    await _show_queued_popups()
                    continue
                try:
                    data = await asyncio.wait_for(user.reader.read(4096), timeout=0.1)
                except asyncio.TimeoutError:
                    continue
                if not data:
                    break
                if isinstance(data, str):
                    data = data.encode("cp437", errors="replace")

                now = asyncio.get_event_loop().time()
                for byte in data:
                    if bytes([byte]) == ESCAPE_CHAR:
                        if now - _escape_last > ESCAPE_WINDOW:
                            _escape_hits = 0
                        _escape_hits += 1
                        _escape_last = now
                        if _escape_hits >= ESCAPE_COUNT:
                            log.info("User aborted door session via escape sequence")
                            return
                    else:
                        _escape_hits = 0

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
                if session_log:
                    session_log.write(data)
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
    base_path = paths.resolve_project(str(conf.base_path)) if conf.base_path else paths.resolve_project("doors")
    door_dir = _resolve_door_dir(door_conf, base_path)

    # Create node directory under the door's own directory
    node_dir = os.path.join(door_dir, f"node{node_num}")
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
        # ---- notify user of escape sequence ----------------------------------
        from input_fields import show_message_box
        await show_message_box(
            user,
            text=f"Launching {door_name}.\n\nPress Ctrl+X three times to exit if the door hangs.",
            title="Door",
        )

        # ---- build variable dict (must come before dropfiles) ----------------
        config_path = os.path.join(node_dir, "dosbox_door.conf")
        variables = _build_vars(user, node_num, node_dir, door_conf, socket_port, config_path)

        # ---- generate dropfiles ----------------------------------------------
        _write_all_dropfiles(user, node_num, node_dir, door_conf, variables, socket_handle=socket_port)

        # ---- launch door -----------------------------------------------------
        command_template = str(door_conf.command) if door_conf.command else ""

        if comm_type in ("COM", "FOSSIL"):
            # Start the TCP listener *before* writing the DOSBox config and launching
            # DOSBox, so the port is already bound when DOSBox finishes booting and
            # tries to connect.
            dosbox_conn_future = asyncio.get_event_loop().create_future()

            def _on_dosbox_connect(r, w):
                if not dosbox_conn_future.done():
                    dosbox_conn_future.set_result((r, w))
                else:
                    w.close()

            dosbox_tcp_server = await asyncio.start_server(
                _on_dosbox_connect, "127.0.0.1", socket_port
            )
            log.debug("Listening for DOSBox on 127.0.0.1:%s", socket_port)

            dosbox_config = _generate_dosbox_config(
                node_dir, door_dir, door_conf, variables, socket_port
            )
            with open(config_path, "w") as f:
                f.write(dosbox_config)
            node.config_path = config_path

            dosbox_exe = str(conf.dosbox_path) if conf.dosbox_path else "dosbox"
            dosbox_base_conf = str(door_conf.dosbox_conf) if door_conf.dosbox_conf else ""
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
                door_reader, door_writer = await asyncio.wait_for(
                    dosbox_conn_future, timeout=60.0
                )
            except asyncio.TimeoutError:
                log.error("DOSBox did not connect on port %s within 60 s", socket_port)
                await send(user, cr + lf + "Door timed out (DOSBox did not connect)." + cr + lf,
                           drain=True)
                return RetVals(status=fail, err_msg="DOSBox connection timeout",
                               next_destination=Destinations.main, next_menu_item=null)
            finally:
                dosbox_tcp_server.close()  # stop accepting new connections

            log.debug("DOSBox connected on port %s", socket_port)
            session_log_path = os.path.join(door_dir, "session.log")
            with open(session_log_path, "w", encoding="utf-8", errors="replace") as session_log:
                await _bridge_socket(user, door_reader, door_writer, process, emulator, session_log=session_log)

        elif comm_type == "SOCKET":
            # Native socket door (DOOR32 style): launch process, bridge via TCP socket
            resolved_cmd = _safe_format(command_template, variables)
            cmd_parts = resolved_cmd.split()
            cwd = door_dir if os.path.isdir(door_dir) else None

            log.debug("Launching native socket door: %s (cwd=%s)", resolved_cmd, cwd)
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                cwd=cwd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            node.process = process

            session_log_path = os.path.join(door_dir, "session.log")
            with open(session_log_path, "w", encoding="utf-8", errors="replace") as session_log:
                await _bridge_socket(user, "127.0.0.1", socket_port, process, emulator, session_log=session_log)

        elif comm_type == "STDIO":
            # Native stdio door: launch process, bridge via stdin/stdout pipes
            resolved_cmd = _safe_format(command_template, variables)
            cmd_parts = resolved_cmd.split()
            cwd = door_dir if os.path.isdir(door_dir) else None

            log.debug("Launching native stdio door: %s (cwd=%s)", resolved_cmd, cwd)
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                cwd=cwd,
            )
            node.process = process

            session_log_path = os.path.join(door_dir, "session.log")
            with open(session_log_path, "w", encoding="utf-8", errors="replace") as session_log:
                await _bridge_stdio(user, process, emulator, session_log=session_log)

        else:
            log.error("Unknown communication type: %s", comm_type)
            await send(user, cr + lf + f"Unknown door communication type: {comm_type}" + cr + lf,
                       drain=True)
            return RetVals(status=fail, err_msg=f"Unknown comm type: {comm_type}",
                           next_destination=Destinations.main, next_menu_item=null)

        # Terminate DOSBox promptly — it won't self-exit when the serial connection closes
        if node.process and node.process.returncode is None:
            try:
                node.process.terminate()
                await asyncio.wait_for(node.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                log.warning("Process did not exit after terminate, killing")
                try:
                    node.process.kill()
                    await asyncio.wait_for(node.process.wait(), timeout=3.0)
                except Exception:
                    pass
            except Exception:
                pass

        rc = node.process.returncode if node.process else None
        if dosbox_log_file:
            dosbox_log_file.close()
            dosbox_log_file = None
        log.info("%s node %s exited with code %s", door_name, node_num, rc)

        # Read and log DOSBox output; always log it, show to user on non-zero exit
        dosbox_log_path = os.path.join(node_dir, "dosbox.log")
        dosbox_log_contents = None
        if os.path.exists(dosbox_log_path):
            try:
                with open(dosbox_log_path, "r", errors="replace") as _f:
                    dosbox_log_contents = _f.read().strip()
                if dosbox_log_contents:
                    log.debug("DOSBox log for %s node %s:\n%s", door_name, node_num, dosbox_log_contents)
            except Exception as _e:
                log.warning("Could not read dosbox.log: %s", _e)
        if rc and dosbox_log_contents:
            await send(user, cr + lf + "--- DOSBox log ---" + cr + lf, drain=True)
            for _line in dosbox_log_contents.splitlines()[-40:]:
                await send(user, _line + cr + lf)
            await send(user, "--- end ---" + cr + lf, drain=True)

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

        if dosbox_log_file:
            try:
                dosbox_log_file.close()
            except Exception:
                pass

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

        log.debug("Cleaned up %s node %s", door_name, node_num)

    await send(user, cr + lf + "Returning to BBS..." + cr + lf, drain=True)
    from common import _find_fallback_destination
    prev = _find_fallback_destination(user, avoid=Destinations.door)
    return RetVals(status=success, next_destination=prev, next_menu_item=null)
