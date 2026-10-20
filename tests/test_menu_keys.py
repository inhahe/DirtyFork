"""Menu keys hold however a menu is reached: navigation, /jump, dotted paths."""
import types
import unittest

import _setup  # noqa: F401
import menu
from definitions import fail, success


def user(*keys):
    return types.SimpleNamespace(keys=set(keys))


class JumpRoutes(unittest.TestCase):
    def test_route_lists_the_menus_passed(self):
        dest, item, parent, err, route = menu.resolve_jump("doors.sysop tools.test door (bios)")
        self.assertIsNone(err)
        self.assertEqual(dest, "door")
        self.assertEqual([n.name for n in route], ["main", "doors", "doors_sysop"])

    def test_jump_into_a_keyed_category_is_denied(self):
        *_, route = menu.resolve_jump("doors.sysop tools.test door (bios)")
        self.assertIn("Sysop Tools", menu.route_denied(user("doors"), route))
        self.assertIsNone(menu.route_denied(user("doors", "sysop"), route))

    def test_dotted_path_from_a_menu(self):
        *_, err, route = menu.resolve_dotted("doors", "sysop tools.test door (bios)")
        self.assertIsNone(err)
        self.assertIn("Missing keys: sysop", menu.route_denied(user("doors"), route))

    def test_unkeyed_route(self):
        *_, route = menu.resolve_jump("doors.most popular.legend of the red dragon")
        self.assertIsNone(menu.route_denied(user("doors"), route))
        self.assertIn("Missing keys: doors", menu.route_denied(user(), route))   # the doors menu itself

    def test_menu_reached_by_name(self):
        dest, item, parent, err, route = menu.resolve_jump("doors_sys")
        self.assertEqual((dest, err), ("doors_sysop", None))
        self.assertEqual([n.name for n in route], ["main", "doors"])   # the menus above it
        self.assertIn("Missing keys: doors", menu.route_denied(user("sysop"), route))

    def test_ancestors_of_a_menu_in_a_loop(self):
        a, b = types.SimpleNamespace(name="a"), types.SimpleNamespace(name="b")
        a.parent, b.parent = b, a                     # each links to the other
        self.assertEqual([n.name for n in menu._ancestors(a)], ["b"])

    def test_check_menu_keys(self):
        import common
        node = menu.get_menu_node("doors_sysop")
        self.assertEqual(common.check_menu_keys(user("doors"), node).status, fail)
        self.assertEqual(common.check_menu_keys(user("doors", "sysop"), node).status, success)


if __name__ == "__main__":
    unittest.main()
