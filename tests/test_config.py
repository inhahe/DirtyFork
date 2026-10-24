"""config.py: views over layers of config (as user.conf is: the user's YAML over the main config)."""
import os
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

  def test_a_users_file_over_the_main_config(self):
    top = tempfile.mkdtemp(prefix="config-")
    try:
      user_file = os.path.join(top, "someone.yaml")
      with open(user_file, "w", encoding="utf-8") as f:
        f.write("email: a@example.org\nlog:\n  path: mine.log\n")
      main = config.get_config()
      user_conf = ConfigView(config.get_config(path=user_file), main, main)  # (as common.py builds it)
      self.assertEqual(user_conf.email, "a@example.org")
      self.assertEqual(user_conf.database, "DirtyFork.db")  # (not in the user's file: the main config's)
      self.assertEqual(user_conf.log.path, "mine.log")
      self.assertEqual(user_conf.log.max_age, "1 year")  # (the rest of the section)
    finally:
      config.configs.pop(os.path.join(top, "someone.yaml"), None)
      import shutil
      shutil.rmtree(top, ignore_errors=True)


if __name__ == "__main__":
  unittest.main()
