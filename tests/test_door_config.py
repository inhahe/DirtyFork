"""door.py: node directories, the DOSBox autoexec, daily commands, dropfiles."""
import os
import types
import unittest
from unittest import mock

import _setup  # noqa: F401  (loads the config)
import door
from config import Config


def root_name(door_dir):
    return os.path.basename(door._node_root(door_dir))


class NodeRoots(unittest.TestCase):
    def setUp(self):
        self.base = door._base_path()

    def under(self, *parts):
        return os.path.join(self.base, *parts)

    def test_plain_names_kept(self):
        self.assertEqual(root_name(self.under("lord")), "lord")
        self.assertEqual(root_name(self.under("lord_demo")), "lord_demo")
        self.assertEqual(root_name(self.under("tw2002")), "tw2002")

    def test_base_dir(self):
        self.assertEqual(root_name(self.base), "~base")

    def test_distinct_dirs_never_share(self):
        dirs = [self.under("a_", "b"), self.under("a", "_b"), self.under("a", "b"),
                self.under("a_b"), self.under("a~b"), self.under("games", "lord"),
                self.under("games_lord"), os.path.join("C:\\", "x", "lord"),
                os.path.join("C:\\", "y", "lord"), self.under("lord"), self.base]
        names = [root_name(d) for d in dirs]
        self.assertEqual(len(set(names)), len(names), names)

    def test_other_drive(self):
        drive = "F:\\" if not self.base.upper().startswith("F") else "G:\\"
        name = root_name(os.path.join(drive, "games", "Trade Wars"))
        self.assertTrue(name.startswith("trade-wars~"), name)


class Autoexec(unittest.TestCase):
    def autoexec(self, door_conf, run_daily):
        text = door._generate_dosbox_config("N", "D", Config(door_conf), {"node": "1"}, 1234,
                                            run_daily=run_daily)
        return text[text.index("[autoexec]"):].splitlines()

    def test_every_command_is_called_in_order(self):
        lines = self.autoexec({"command": "GAME.EXE", "pre_commands": ["SRDOOR", "IF EXIST X DEL X"],
                               "daily_commands": ["MAINT.BAT"]}, run_daily=True)
        calls = [l for l in lines if l.startswith("CALL ")]
        self.assertEqual(calls, ["CALL MAINT.BAT", f"CALL ECHO done> C:\\{door.DAILY_DONE_FLAG}",
                                 "CALL SRDOOR", "CALL IF EXIST X DEL X", "CALL GAME.EXE"])

    def test_daily_commands_only_when_due(self):
        lines = self.autoexec({"command": "GAME.EXE", "daily_commands": ["MAINT.BAT"]}, run_daily=False)
        self.assertNotIn("CALL MAINT.BAT", lines)
        self.assertFalse(any(door.DAILY_DONE_FLAG in l for l in lines))


class DailyMark(unittest.TestCase):
    def test_due_once_a_day_and_unmark(self):
        tmp = _setup.tempfile.mkdtemp(dir=_setup.DATA)
        conf = Config({"daily_commands": ["MAINT"]})
        with mock.patch.object(door, "_node_root", lambda d: tmp):
            self.assertTrue(door._daily_commands_due("x", conf))
            self.assertFalse(door._daily_commands_due("x", conf))
            door._unmark_daily("x")
            self.assertTrue(door._daily_commands_due("x", conf))
            self.assertFalse(door._daily_commands_due("x", Config({})))

    def test_unmark_leaves_another_days_mark(self):
        tmp = _setup.tempfile.mkdtemp(dir=_setup.DATA)
        with open(os.path.join(tmp, "daily.stamp"), "w") as f:
            f.write("1999-01-01\n")
        with mock.patch.object(door, "_node_root", lambda d: tmp):
            door._unmark_daily("x")
        self.assertTrue(os.path.exists(os.path.join(tmp, "daily.stamp")))


class Dropfiles(unittest.TestCase):
    def setUp(self):
        from config import get_config
        self.door_conf = get_config().menu_system.doors_popular.options["Legend of the Red Dragon"]
        self.user = types.SimpleNamespace(handle="Tester", location="Here",
                                          screen_height=25, screen_width=80)

    def test_door_sys_paths_are_dos_paths(self):
        v = door._build_vars(self.user, 1, "N", self.door_conf, 1, in_dosbox=True)
        lines = door._generate_door_sys(None, 1, "N", self.door_conf, v).split("\r\n")
        self.assertEqual(lines[9], "Tester")          # line 10: user name
        self.assertEqual(lines[32:34], ["C:\\", "C:\\"])   # lines 33/34: main and dropfile dirs
        self.assertEqual(lines[35], "Tester")         # line 36: alias

    def test_door32_comm_type(self):
        v = door._build_vars(self.user, 1, "N", self.door_conf, 4321, in_dosbox=True)
        lines = door._generate_door32_sys(None, 1, 4321, self.door_conf, v, True).split("\r\n")
        self.assertEqual(lines[:2], ["1", "1"])       # serial, COM1
        lines = door._generate_door32_sys(None, 1, 4321, self.door_conf, v, False).split("\r\n")
        self.assertEqual(lines[:2], ["2", "4321"])    # telnet socket


class FindDoorConf(unittest.TestCase):
    def test_menu_the_option_was_picked_in_wins(self):
        picked = types.SimpleNamespace(options_info={
            "Same Name": types.SimpleNamespace(conf=Config({"target": "door", "dir": "picked"}))})
        conf = door._find_door_conf(types.SimpleNamespace(_option_menu=picked), "Same Name")
        self.assertEqual(conf.dir, "picked")

    def test_falls_back_to_any_menu(self):
        conf = door._find_door_conf(types.SimpleNamespace(_option_menu=None), "Test Door (BIOS)")
        self.assertEqual(str(conf.dir), "testdoor")


if __name__ == "__main__":
    unittest.main()
