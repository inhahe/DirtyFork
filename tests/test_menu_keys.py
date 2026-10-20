"""Menu keys hold however a menu is reached: navigation, /jump, dotted paths."""
import types
import unittest
from unittest import mock

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
        dest, item, parent, err, route = menu.resolve_jump("doors_sys", user("sysop"))
        self.assertEqual((dest, err), ("doors_sysop", None))
        self.assertEqual([n.name for n in route], ["main", "doors"])   # the menus above it
        self.assertIn("Missing keys: doors", menu.route_denied(user("sysop"), route))
        *_, route = menu.resolve_jump("doors_sys", user("doors", "sysop"))
        self.assertIsNone(menu.route_denied(user("doors", "sysop"), route))

    def test_check_menu_keys(self):
        import common
        node = menu.get_menu_node("doors_sysop")
        self.assertEqual(common.check_menu_keys(user("doors"), node).status, fail)
        self.assertEqual(common.check_menu_keys(user("doors", "sysop"), node).status, success)


def tree(links):
    """MenuNodes linked as *links* says ({menu: [menus its options lead to]}),
    with .parent set as the real tree sets it: the last menu linking wins."""
    nodes = {name: menu.MenuNode(name) for name in links}
    for name, targets in links.items():
        for target in targets:
            nodes[name].children[target] = nodes[target]
            nodes[target].parent = nodes[name]
    return nodes


def refusing(*names):
    """A stand-in for common.check_menu_keys under which only menus *names* refuse."""
    def check(user, node):
        refused = node.name in names
        return types.SimpleNamespace(status=fail if refused else success,
                                     err_msg=f"Access denied to {node.name}." if refused else None)
    return check


class JumpByName(unittest.TestCase):
    """/j <menu name> goes through no menus of its own: it must still be a
    menu the user could reach through menus that admit them."""

    def setUp(self):
        menu._ensure_menu_tree()  # (built now, so it doesn't replace the trees patched in below)

    def jump(self, links, name, *refused):
        import common
        with mock.patch.object(menu, "_menu_nodes", tree(links)), \
             mock.patch.object(common, "check_menu_keys", refusing(*refused)):
            dest, item, parent, err, route = menu.resolve_jump(name, user())
            self.assertEqual((dest, err), (name, None))
            return menu.route_denied(user(), route)

    def test_listed_in_a_keyed_and_an_open_menu(self):
        links = {"main": ["open", "keyed"], "open": ["games"], "keyed": ["games"], "games": []}
        self.assertIsNone(self.jump(links, "games", "keyed"))          # through "open"
        self.assertIsNotNone(self.jump(links, "games", "keyed", "open"))  # (names either)

    def test_loop_inside_a_keyed_menu(self):
        links = {"main": ["sysop"], "sysop": ["tools", "help"], "tools": ["help"], "help": ["tools"]}
        self.assertIn("sysop", self.jump(links, "tools", "sysop") or "admitted")
        self.assertIsNone(self.jump(links, "tools"))

    def test_main_linked_back_to_from_a_keyed_menu(self):
        links = {"main": ["sysop"], "sysop": ["main"]}
        self.assertIsNone(self.jump(links, "main", "sysop"))

    def test_menu_nothing_links_to(self):
        links = {"main": ["a"], "a": [], "lonely": ["inner"], "inner": []}
        self.assertIsNone(self.jump(links, "lonely", "main"))        # nothing above it
        self.assertIn("lonely", self.jump(links, "inner", "lonely") or "admitted")


if __name__ == "__main__":
    unittest.main()
