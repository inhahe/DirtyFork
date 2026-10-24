"""
Logging system for DirtyFork BBS.

Provides a module-level `log` logger and a `setup_logging()` function
that configures Python's logging module with a RotatingFileHandler
(for log file splitting) and the console.

The console is written by a thread of its own (ConsoleLog): the BBS's event
loop only hands it records. A console can stop taking output for any length
of time (in a Windows console with QuickEdit, a click in the window pauses
every program writing to it until the selection ends), and a write the loop
made itself would stop the whole BBS meanwhile: every caller frozen,
connections accepted and never answered.

Usage:
    from logger import log, setup_logging
    setup_logging()          # call once at startup, after config is loaded
    log.info("message")      # use everywhere else
"""

import atexit
import glob
import logging
import os
import queue
import re
import sys
import threading
import time
import traceback
from datetime import timedelta
from logging.handlers import RotatingFileHandler

from config import get_config
import paths

log = logging.getLogger("dirtyfork")


class ConsoleLog(logging.Handler):
    """Shows records on the console (stderr) from a thread of its own.

    At most *backlog* records wait while the console is not taking output;
    further ones are not shown (the log file has them), and once there is room
    again a line says how many were left out. stop() writes what is waiting,
    for at most *timeout* seconds (the console may still be paused at exit).

    A record that cannot be logged (by this handler, or by the log file's:
    report_error) is told on the console the same way, rather than written
    to stderr by the thread logging it; the same error again within a
    minute (a log file that cannot be rotated fails every record) is not."""

    def __init__(self, backlog=10_000, stream=None):
        super().__init__()
        self._stream = stream
        self._backlog = backlog
        # (a SimpleQueue: its put is reentrant, so a record logged while one
        # is being put, by a finalizer, say, cannot deadlock the thread
        # putting them, which is the event loop's)
        self._queue = queue.SimpleQueue()
        self._left_out = 0
        self._last_error = None  # ((type, message), when)
        self._thread = threading.Thread(target=self._show, name="console log", daemon=True)
        self._thread.start()

    def emit(self, record):
        try:
            line = self.format(record)
        except Exception:
            self.handleError(record)
            return
        self._put(line)

    def handleError(self, record):
        self.report_error(record)

    def report_error(self, record):
        """Tell, on the console, why *record* could not be logged (called
        while its exception is being handled)."""
        if not logging.raiseExceptions:
            return
        exc_type, exc, _ = sys.exc_info()
        key, now = (exc_type, str(exc)), time.monotonic()
        with self.lock:
            if self._last_error and self._last_error[0] == key and now - self._last_error[1] < 60:
                return
            self._last_error = (key, now)
            self._put(f"--- Logging error ---\n{traceback.format_exc().rstrip()}\n"
                      f"Message: {record.msg!r}\nArguments: {record.args!r}")

    def _put(self, line):
        if self._queue.qsize() >= self._backlog:
            self._left_out += 1
            return
        if self._left_out:
            self._queue.put(f"({self._left_out} log lines were not shown here while the "
                            f"console was not taking output; the log file has them)")
            self._left_out = 0
        self._queue.put(line)

    def _show(self):
        while True:
            line = self._queue.get()
            if line is None:
                return
            stream = self._stream or sys.stderr
            try:
                stream.write(line + "\n")
                stream.flush()
            except Exception:
                pass  # (no console, or a closed one: nothing to show it on)

    def stop(self, timeout=2.0):
        self._queue.put(None)
        self._thread.join(timeout)


class _FileLog(RotatingFileHandler):
    """The log file. A record it cannot write is told on the console
    (*console*, a ConsoleLog), not written to stderr by the thread logging
    it: under a paused console that write would stop the event loop."""

    def __init__(self, *args, console=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = console

    def handleError(self, record):
        if self.console is not None:
            self.console.report_error(record)


def _stop_console():
    """At exit: show what the console has waiting (for a while)."""
    for handler in log.handlers:
        if isinstance(handler, ConsoleLog):
            handler.stop()


def _log_unraisable(unraisable):
    """sys.unraisablehook: an exception Python can only report, to the log."""
    where = unraisable.err_msg or "Exception ignored in"
    log.error("%s: %r", where, unraisable.object,
              exc_info=(unraisable.exc_type, unraisable.exc_value, unraisable.exc_traceback))


def _parse_duration(text):
    """Parse a human-readable duration string into a timedelta.

    Supports forms like "1 year", "30 days", "6 months", "2 hours",
    "1 year 30 days", etc.
    """
    if not text:
        return None

    text = text.strip().lower()
    total = timedelta()
    pattern = re.compile(r'(\d+)\s*(year|month|week|day|hour|minute|second)s?')
    matches = pattern.findall(text)
    if not matches:
        return None

    for value_str, unit in matches:
        value = int(value_str)
        if unit == "year":
            total += timedelta(days=value * 365)
        elif unit == "month":
            total += timedelta(days=value * 30)
        elif unit == "week":
            total += timedelta(weeks=value)
        elif unit == "day":
            total += timedelta(days=value)
        elif unit == "hour":
            total += timedelta(hours=value)
        elif unit == "minute":
            total += timedelta(minutes=value)
        elif unit == "second":
            total += timedelta(seconds=value)

    return total if total > timedelta() else None


def _cleanup_old_logs(log_path, max_age_str):
    """Delete rotated log files older than *max_age_str*.

    Looks for files matching the base log path with numeric suffixes
    (e.g. DirtyFork.log.1, DirtyFork.log.2) as produced by
    RotatingFileHandler, as well as the base log file itself.
    """
    max_age = _parse_duration(max_age_str)
    if max_age is None:
        return

    cutoff = time.time() - max_age.total_seconds()
    base = os.path.abspath(log_path)
    pattern = base + ".*"
    candidates = glob.glob(pattern)
    # Also consider the base file itself
    candidates.append(base)

    for path in candidates:
        try:
            if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                os.remove(path)
        except OSError:
            pass


def setup_logging():
    """Configure the ``dirtyfork`` logger from the YAML config.

    Must be called once at startup after the config has been loaded.
    """
    config = get_config()
    log_conf = config.log

    # Defaults
    log_path = paths.resolve_data("DirtyFork.log")
    split_at = 1_000_000
    max_length = 10_000_000
    max_age = "1 year"

    if log_conf:
        if log_conf.path:
            log_path = paths.resolve_data(str(log_conf.path))
        if log_conf.split_at:
            split_at = int(log_conf.split_at)
        if log_conf.max_length:
            max_length = int(log_conf.max_length)
        if log_conf.max_age:
            max_age = str(log_conf.max_age)

    # Calculate backup count from max_length and split_at
    backup_count = max(max_length // split_at - 1, 0)

    # Clean up old log files before setting up handlers
    _cleanup_old_logs(log_path, max_age)

    # Configure the logger
    log.setLevel(logging.DEBUG)
    log.propagate = False  # Don't propagate to root logger (prevents duplicate output)

    # Prevent duplicate handlers if setup_logging is called more than once
    root = logging.getLogger()
    for handler in list(log.handlers):
        root.removeHandler(handler)
        if isinstance(handler, ConsoleLog):
            handler.stop()
        handler.close()
    log.handlers.clear()

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console (stderr), written by its own thread — only show DEBUG if --debug was passed
    console_handler = ConsoleLog()
    console_handler.setLevel(logging.DEBUG if "--debug" in sys.argv else logging.INFO)
    console_handler.setFormatter(formatter)
    atexit.unregister(_stop_console)  # (once, for whichever console is current)
    atexit.register(_stop_console)

    # File handler with rotation
    file_handler = _FileLog(
        log_path,
        maxBytes=split_at,
        backupCount=backup_count,
        encoding="utf-8",
        console=console_handler,
    )
    file_handler.setLevel(logging.DEBUG if "--debug" in sys.argv else logging.INFO)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    log.addHandler(console_handler)

    # Other libraries' warnings (asyncio's, telnetlib3's) go to both too: left
    # to logging's last resort, the event loop would write them to the console
    # itself. So do Python's warnings ("coroutine ... was never awaited") and
    # the exceptions it can only report ("Exception ignored in ..."), which
    # are otherwise written to stderr by whichever thread raised them.
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    logging.captureWarnings(True)
    sys.unraisablehook = _log_unraisable

    log.debug("Logging initialised (file=%s, split_at=%d, backups=%d, max_age=%s)",
             log_path, split_at, backup_count, max_age)
