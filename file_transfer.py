"""
Async wrapper around YMODEM-G and ZMODEM file transfer protocol libraries.

The protocol libraries are synchronous (blocking I/O). This module bridges
them into the async BBS world by running the protocol in a thread via
asyncio.to_thread(), with blocking wrappers over the async reader/writer
that use asyncio.run_coroutine_threadsafe() to safely cross the thread
boundary.

Usage:
    from file_transfer import send_file_zmodem, recv_file_zmodem
    result = await send_file_zmodem(user, "/path/to/file.zip")
"""

import asyncio
import os
import sys

from definitions import RetVals, success, fail
from logger import log

# ---------------------------------------------------------------------------
# Add lib/ to sys.path so both protocol libraries are importable
# ---------------------------------------------------------------------------
_lib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
if _lib_dir not in sys.path:
    sys.path.insert(0, _lib_dir)

# ---------------------------------------------------------------------------
# Probe which protocol libraries are available
# ---------------------------------------------------------------------------
_have_zmodem = False
_have_ymodem = False

try:
    from modem.protocol.zmodem import ZMODEM
    _have_zmodem = True
except ImportError:
    log.warning("ZMODEM library (modem.protocol.zmodem) not available")

try:
    from ymodem.Socket import ModemSocket
    from ymodem.Protocol import ProtocolType
    _have_ymodem = True
except ImportError:
    log.warning("YMODEM-G library (ymodem.Socket) not available")


# ---------------------------------------------------------------------------
# CAN detection
# ---------------------------------------------------------------------------
CAN_BYTE = b'\x18'
CAN_CHAR = '\x18'
CAN_COUNT_THRESHOLD = 5  # 5 consecutive CANs = user abort


def get_available_protocols():
    """Return a dict of protocol name -> bool indicating availability."""
    return {
        'zmodem': _have_zmodem,
        'ymodem': _have_ymodem,
    }


# ---------------------------------------------------------------------------
# I/O bridge helpers
# ---------------------------------------------------------------------------

def _make_getc(user, loop):
    """Create a blocking getc that reads from user.reader via the event loop.

    Returns a callable ``getc(size, timeout=1)`` suitable for the modem
    library's Modem(getc, putc) constructor.  The callable is designed to
    be called from a *worker thread* (not the event-loop thread).
    """

    def getc(size, timeout=1):
        async def _read():
            try:
                data = await asyncio.wait_for(user.reader.read(size), timeout=timeout)
                if not data:
                    return None
                if isinstance(data, str):
                    return data.encode('latin-1')
                return data
            except asyncio.TimeoutError:
                return None
            except Exception:
                return None

        future = asyncio.run_coroutine_threadsafe(_read(), loop)
        try:
            return future.result(timeout=timeout + 2)
        except Exception:
            return None

    return getc


def _make_putc(user, loop):
    """Create a blocking putc that writes to user.writer via the event loop.

    Returns a callable ``putc(data, timeout=1)`` suitable for the modem
    library's Modem(getc, putc) constructor.  The callable is designed to
    be called from a *worker thread*.
    """

    def putc(data, timeout=1):
        async def _write():
            if isinstance(data, int):
                user.writer.write(chr(data))
            elif isinstance(data, (bytes, bytearray)):
                user.writer.write(data.decode('latin-1', errors='replace'))
            else:
                user.writer.write(data)
            await user.writer.drain()
            return len(data) if not isinstance(data, int) else 1

        future = asyncio.run_coroutine_threadsafe(_write(), loop)
        try:
            return future.result(timeout=timeout + 2)
        except Exception:
            return 0

    return putc


def _make_ymodem_read(user, loop):
    """Create a blocking read callback for the ymodem library.

    Signature: ``read(size, timeout=1) -> bytes | None``
    """

    def read(size, timeout=1):
        async def _read():
            try:
                data = await asyncio.wait_for(user.reader.read(size), timeout=timeout)
                if not data:
                    return None
                if isinstance(data, str):
                    return data.encode('latin-1')
                return data
            except asyncio.TimeoutError:
                return None
            except Exception:
                return None

        future = asyncio.run_coroutine_threadsafe(_read(), loop)
        try:
            return future.result(timeout=timeout + 2)
        except Exception:
            return None

    return read


def _make_ymodem_write(user, loop):
    """Create a blocking write callback for the ymodem library.

    Signature: ``write(data, timeout=1) -> int``
    """

    def write(data, timeout=1):
        async def _write():
            if isinstance(data, (bytes, bytearray)):
                user.writer.write(data.decode('latin-1', errors='replace'))
            else:
                user.writer.write(str(data))
            await user.writer.drain()
            return len(data)

        future = asyncio.run_coroutine_threadsafe(_write(), loop)
        try:
            return future.result(timeout=timeout + 2)
        except Exception:
            return 0

    return write


# ---------------------------------------------------------------------------
# ZMODEM auto-start sequence for SyncTERM
# ---------------------------------------------------------------------------
ZMODEM_AUTOSTART = b'**\x18B00000000000000\r\n'


# ---------------------------------------------------------------------------
# ZMODEM transfers
# ---------------------------------------------------------------------------

async def send_file_zmodem(user, file_path):
    """Send a file to the user via ZMODEM.

    Returns a RetVals with .status = success or fail and .message.
    """
    if not _have_zmodem:
        return RetVals(status=fail, message="ZMODEM library not available")

    if not os.path.isfile(file_path):
        return RetVals(status=fail, message=f"File not found: {file_path}")

    filename = os.path.basename(file_path)
    log.info("Starting ZMODEM send of '%s' to %s",
             filename, getattr(user, 'name', 'unknown'))

    # Notify the user
    user.writer.write("Starting ZMODEM transfer...\r\n")
    await user.writer.drain()

    # Send the ZMODEM auto-start sequence so SyncTERM opens its receive dialog
    user.writer.write(ZMODEM_AUTOSTART.decode('latin-1'))
    await user.writer.drain()

    loop = asyncio.get_event_loop()
    getc = _make_getc(user, loop)
    putc = _make_putc(user, loop)

    def _do_send():
        try:
            modem = ZMODEM(getc, putc)
            with open(file_path, 'rb') as f:
                return modem.send(f)
        except Exception as exc:
            log.error("ZMODEM send error: %s", exc, exc_info=True)
            return None

    try:
        result = await asyncio.to_thread(_do_send)
    except Exception as exc:
        log.error("ZMODEM send thread error: %s", exc, exc_info=True)
        user.writer.write("\r\nTransfer failed.\r\n")
        await user.writer.drain()
        return RetVals(status=fail, message=str(exc))

    if result is not None and result is not False:
        log.info("ZMODEM send of '%s' complete", filename)
        user.writer.write("\r\nTransfer complete.\r\n")
        await user.writer.drain()
        return RetVals(status=success, message="Transfer complete")
    else:
        log.warning("ZMODEM send of '%s' failed", filename)
        user.writer.write("\r\nTransfer failed.\r\n")
        await user.writer.drain()
        return RetVals(status=fail, message="Transfer failed")


async def recv_file_zmodem(user, save_dir):
    """Receive file(s) from the user via ZMODEM.

    Files are saved under *save_dir*.
    Returns a RetVals with .status = success or fail and .message.
    """
    if not _have_zmodem:
        return RetVals(status=fail, message="ZMODEM library not available")

    os.makedirs(save_dir, exist_ok=True)

    log.info("Starting ZMODEM receive into '%s' from %s",
             save_dir, getattr(user, 'name', 'unknown'))

    user.writer.write("Starting ZMODEM receive... send your file now.\r\n")
    await user.writer.drain()

    loop = asyncio.get_event_loop()
    getc = _make_getc(user, loop)
    putc = _make_putc(user, loop)

    def _do_recv():
        try:
            modem = ZMODEM(getc, putc)
            return modem.recv(save_dir)
        except Exception as exc:
            log.error("ZMODEM recv error: %s", exc, exc_info=True)
            return None

    try:
        result = await asyncio.to_thread(_do_recv)
    except Exception as exc:
        log.error("ZMODEM recv thread error: %s", exc, exc_info=True)
        user.writer.write("\r\nTransfer failed.\r\n")
        await user.writer.drain()
        return RetVals(status=fail, message=str(exc))

    if result is not None and result is not False:
        log.info("ZMODEM receive complete (%s)", result)
        user.writer.write("\r\nTransfer complete.\r\n")
        await user.writer.drain()
        return RetVals(status=success, message="Transfer complete")
    else:
        log.warning("ZMODEM receive failed")
        user.writer.write("\r\nTransfer failed.\r\n")
        await user.writer.drain()
        return RetVals(status=fail, message="Transfer failed")


# ---------------------------------------------------------------------------
# YMODEM-G transfers
# ---------------------------------------------------------------------------

async def send_file_ymodem(user, file_path):
    """Send a file to the user via YMODEM-G.

    Returns a RetVals with .status = success or fail and .message.
    """
    if not _have_ymodem:
        return RetVals(status=fail, message="YMODEM library not available")

    if not os.path.isfile(file_path):
        return RetVals(status=fail, message=f"File not found: {file_path}")

    filename = os.path.basename(file_path)
    log.info("Starting YMODEM-G send of '%s' to %s",
             filename, getattr(user, 'name', 'unknown'))

    user.writer.write("Starting YMODEM-G transfer...\r\n")
    await user.writer.drain()

    loop = asyncio.get_event_loop()
    read_cb = _make_ymodem_read(user, loop)
    write_cb = _make_ymodem_write(user, loop)

    def _progress(task_index, name, total, sent):
        log.debug("YMODEM-G send progress: %s %d/%d", name, sent, total)

    def _do_send():
        try:
            modem = ModemSocket(
                read_cb,
                write_cb,
                protocol_type=ProtocolType.YMODEM,
                protocol_type_options=['g'],
            )
            return modem.send([file_path], callback=_progress)
        except Exception as exc:
            log.error("YMODEM-G send error: %s", exc, exc_info=True)
            return False

    try:
        result = await asyncio.to_thread(_do_send)
    except Exception as exc:
        log.error("YMODEM-G send thread error: %s", exc, exc_info=True)
        user.writer.write("\r\nTransfer failed.\r\n")
        await user.writer.drain()
        return RetVals(status=fail, message=str(exc))

    if result:
        log.info("YMODEM-G send of '%s' complete", filename)
        user.writer.write("\r\nTransfer complete.\r\n")
        await user.writer.drain()
        return RetVals(status=success, message="Transfer complete")
    else:
        log.warning("YMODEM-G send of '%s' failed", filename)
        user.writer.write("\r\nTransfer failed.\r\n")
        await user.writer.drain()
        return RetVals(status=fail, message="Transfer failed")


async def recv_file_ymodem(user, save_dir):
    """Receive file(s) from the user via YMODEM-G.

    Files are saved under *save_dir*.
    Returns a RetVals with .status = success or fail and .message.
    """
    if not _have_ymodem:
        return RetVals(status=fail, message="YMODEM library not available")

    os.makedirs(save_dir, exist_ok=True)

    log.info("Starting YMODEM-G receive into '%s' from %s",
             save_dir, getattr(user, 'name', 'unknown'))

    user.writer.write("Starting YMODEM-G receive... send your file now.\r\n")
    await user.writer.drain()

    loop = asyncio.get_event_loop()
    read_cb = _make_ymodem_read(user, loop)
    write_cb = _make_ymodem_write(user, loop)

    def _progress(task_index, name, total, sent):
        log.debug("YMODEM-G recv progress: %s %d/%d", name, sent, total)

    def _do_recv():
        try:
            modem = ModemSocket(
                read_cb,
                write_cb,
                protocol_type=ProtocolType.YMODEM,
                protocol_type_options=['g'],
            )
            return modem.recv(save_dir, callback=_progress)
        except Exception as exc:
            log.error("YMODEM-G recv error: %s", exc, exc_info=True)
            return False

    try:
        result = await asyncio.to_thread(_do_recv)
    except Exception as exc:
        log.error("YMODEM-G recv thread error: %s", exc, exc_info=True)
        user.writer.write("\r\nTransfer failed.\r\n")
        await user.writer.drain()
        return RetVals(status=fail, message=str(exc))

    if result:
        log.info("YMODEM-G receive complete")
        user.writer.write("\r\nTransfer complete.\r\n")
        await user.writer.drain()
        return RetVals(status=success, message="Transfer complete")
    else:
        log.warning("YMODEM-G receive failed")
        user.writer.write("\r\nTransfer failed.\r\n")
        await user.writer.drain()
        return RetVals(status=fail, message="Transfer failed")
