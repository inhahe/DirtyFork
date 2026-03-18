"""
Path resolution for DirtyFork BBS.

  project_dir  — directory containing the BBS source files (set at import time)
  data_dir     — directory for user data (DirtyFork.yaml, .db, logs, user_configs, files)
                 defaults to "." (current working directory); overridden by --data-dir CLI arg

Helper functions:
  resolve_data(path)    — absolute path under data_dir (unless path is already absolute)
  resolve_project(path) — absolute path under project_dir (unless path is already absolute)
"""

import os

# Absolute path to the directory containing this file (i.e. the BBS source tree)
project_dir = os.path.dirname(os.path.abspath(__file__))

# Set by DirtyFork.py before anything else imports it
data_dir = "."


def resolve_data(path):
    """Return an absolute path by joining data_dir + path, unless path is already absolute."""
    if not path:
        return path
    path = str(path)
    if os.path.isabs(path):
        return path
    return os.path.join(data_dir, path)


def resolve_project(path):
    """Return an absolute path by joining project_dir + path, unless path is already absolute."""
    if not path:
        return path
    path = str(path)
    if os.path.isabs(path):
        return path
    return os.path.join(project_dir, path)
