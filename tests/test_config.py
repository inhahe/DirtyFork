"""config.py: views over layers of config (as user.conf is: the user's YAML over the main config)."""
import os
import shutil
import tempfile
import unittest

import _setup  # noqa: F401  (paths, config)

import config
from config import Config, ConfigView
from definitions import null


def view(values):
  """A view of one Config, as get_config gives (its layers are views of those)."""
  return ConfigView(Config(values))


class Layers(unittest.TestCase):
  def test_a_key_one_layer_lacks_comes_from_the_next(self):
    user, main = view({"encoding": "utf-8"}), view({"encoding": "cp437", "show_stars": False, "x": 5})
    for v in (ConfigView(user, main), ConfigView(user, ConfigView(view({}), main))):
      self.assertEqual((v.encoding, v.x, v.show_stars), ("utf-8", 5, False))
      self.assertIs(v.nosuch, null)

  def test_sections_are_merged_across_views(self):
    v = ConfigView(view({"s": {"a": 10}}), view({"s": {"a": 1, "b": 2, "t": {"c": 3}}}))
    self.assertEqual((v.s.a, v.s.b, v.s.t.c), (10, 2, 3))
    self.assertEqual(sorted(v.s.keys()), ["a", "b", "t"])

  def test_in_asks_the_layers(self):
    v = ConfigView(view({"a": 1}), view({"b": 2}))
    self.assertEqual(("a" in v, "b" in v, "c" in v), (True, True, False))
    self.assertNotIn("x", view({"s": {"y": 1}}).s)

  def test_a_null_set_on_purpose_hides_the_next_layers(self):
    # (as with Config layers: a key there, even if null, is that layer's answer)
    self.assertIs(ConfigView(view({"a": None}), view({"a": 1})).a, null)

  def test_a_key_not_there_is_read_without_being_added(self):
    # (reading one adds nothing: a key added as null would hide the next layers)
    c = Config({"bio": "see {log}"})
    self.assertEqual(c["nosuch"], null)
    self.assertEqual(c.bio, "see {log}")  # (resolving it reads log, which isn't there)
    self.assertEqual(sorted(dict.keys(c)), ["bio"])
    self.assertEqual(ConfigView(ConfigView(c), view({"log": {"path": "x"}})).log.path, "x")

  def test_get_gives_its_default_for_a_key_not_there(self):
    v = ConfigView(view({"a": 1}), view({"b": None}))
    self.assertEqual((v.get("a", 9), v.get("c", 9), v.get("c")), (1, 9, None))
    self.assertIs(v.get("b", 9), null)  # (there, as null)


class Files(unittest.TestCase):
  def setUp(self):
    self.top = tempfile.mkdtemp(prefix="config-")
    self.user_file = os.path.join(self.top, "someone.yaml")

  def tearDown(self):
    config.configs.pop(self.user_file, None)
    shutil.rmtree(self.top, ignore_errors=True)

  def write(self, text):
    with open(self.user_file, "w", encoding="utf-8") as f:
      f.write(text)

  def test_a_users_file_over_the_main_config(self):
    self.write("email: a@example.org\nlog:\n  path: mine.log\n")
    user_conf = ConfigView(config.get_config(path=self.user_file), config.get_config())  # (as common.py makes it)
    self.assertEqual(user_conf.email, "a@example.org")
    self.assertEqual(user_conf.database, "DirtyFork.db")  # (not in the user's file: the main config's)
    self.assertEqual(user_conf.log.path, "mine.log")
    self.assertEqual(user_conf.log.max_age, "1 year")  # (the rest of the section)

  def test_a_users_file_is_read_again_once_changed(self):
    # (the Settings page writes it, then fills its form from it: a stale copy
    # would show the old values, and saving them would undo the change)
    self.write("email: a@example.org\n")
    self.assertEqual(config.get_config(path=self.user_file).email, "a@example.org")
    self.write("email: b@example.org\nage: 30\n")
    self.assertEqual(config.get_config(path=self.user_file).email, "b@example.org")
    self.assertIs(config.get_config(path=self.user_file)._layers[0], config.configs[self.user_file])  # (kept)
    self.assertEqual(config.get_config(path=self.user_file).email, "b@example.org")


if __name__ == "__main__":
  unittest.main()
