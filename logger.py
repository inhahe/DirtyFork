"""
Logging system for DirtyFork BBS.

Provides a module-level `log` logger and a `setup_logging()` function
that configures Python's logging module with a RotatingFileHandler
(for log file splitting) and a StreamHandler (for console output).

Usage:
    from logger import log, setup_logging
    setup_logging()          # call once at startup, after config is loaded
    log.info("message")      # use everywhere else
"""

import glob
import logging
import os
import re
import time
from datetime import timedelta
from logging.handlers import RotatingFileHandler

from config import get_config

log = logging.getLogger("dirtyfork")


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
    log_path = "DirtyFork.log"
    split_at = 1_000_000
    max_length = 10_000_000
    max_age = "1 year"

    if log_conf:
        if log_conf.path:
            log_path = str(log_conf.path)
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

    # Prevent duplicate handlers if setup_logging is called more than once
    log.handlers.clear()

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=split_at,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    # Console handler (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

    log.info("Logging initialised (file=%s, split_at=%d, backups=%d, max_age=%s)",
             log_path, split_at, backup_count, max_age)
