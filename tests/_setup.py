"""Shared test setup: import this before any BBS module.

Loads the shipped DirtyFork.yaml (as on a fresh clone), with a scratch data
directory for the database and user files, and provides small fakes.
Run the tests from the project directory:  python -m unittest discover -s tests
"""
import atexit
import os
import shutil
import sys
import tempfile

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)
os.chdir(PROJECT)  # the config's !include paths are relative to the project directory

import paths  # noqa: E402

DATA = tempfile.mkdtemp(prefix="dirtyfork-tests-")
paths.data_dir = DATA


@atexit.register
def _cleanup():
    common = sys.modules.get("common")
    if common is not None:
        common.con.close()  # the database common.py opened (else the directory can't go)
    shutil.rmtree(DATA, ignore_errors=True)

from config import get_config  # noqa: E402

get_config(path=os.path.join(PROJECT, "DirtyFork.yaml"), main=True)


class FakeWriter:
    """Stands in for a telnet writer: collects what is written."""

    def __init__(self, fail_drain=False):
        self.out = []
        self.fail_drain = fail_drain

    def write(self, s):
        self.out.append(s)

    async def drain(self):
        if self.fail_drain:
            raise ConnectionResetError("caller gone")

    def get_extra_info(self, *args, **kwargs):
        return None

    def text(self):
        return "".join(self.out)


def make_user(rows=25, cols=80):
    """A logged-out User on an 80x25 screen, writing to a FakeWriter."""
    import common
    from definitions import Char
    user = common.User(None, FakeWriter())
    user.screen_height, user.screen_width = rows, cols
    user.screen = [[Char() for _ in range(cols)] for _ in range(rows)]
    return user
