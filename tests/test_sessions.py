"""common.forget_session: an ended session leaves the registry of who is
on, but not the session that replaced it under the same handle."""
import unittest

import _setup
import common


class Registry(unittest.TestCase):
    def setUp(self):
        self.saved = dict(common.global_data.users), set(common.global_data.users_logging_in)
        self.addCleanup(self.restore)

    def restore(self):
        common.global_data.users.clear()
        common.global_data.users.update(self.saved[0])
        common.global_data.users_logging_in.clear()
        common.global_data.users_logging_in.update(self.saved[1])

    def session(self, handle):
        user = _setup.make_user()
        user.handle = handle
        return user

    def test_an_ended_session_is_forgotten(self):
        bob = self.session("Bob")
        common.global_data.users["bob"] = bob
        common.forget_session(bob)
        self.assertNotIn("bob", common.global_data.users)

    def test_a_session_replaced_by_a_second_login_leaves_the_new_one(self):
        """Bob logs in again: login closes the first session and registers
        the second under "bob"; the first, ending later, must not remove it
        (it did: the second then was not on the who's-online list, not told
        of a shutdown, and not kicked by a third login)."""
        first, second = self.session("Bob"), self.session("Bob")
        common.global_data.users["bob"] = second
        common.forget_session(first)
        self.assertIs(common.global_data.users.get("bob"), second)

    def test_a_session_that_never_logged_in_is_forgotten_too(self):
        caller = _setup.make_user()
        common.global_data.users_logging_in.add(caller)
        common.forget_session(caller)
        self.assertNotIn(caller, common.global_data.users_logging_in)


if __name__ == "__main__":
    unittest.main()
