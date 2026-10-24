"""file_transfer.py's upload policy (names, sizes, room, publishing), and
file.py's downloads and catalogue. (Transfers themselves: test_zmodem*.py,
test_ymodem.py, test_web_transfers.py.)"""
import asyncio
import os
import shutil
import tempfile
import unittest
from unittest import mock

import _setup
import file_transfer


class UploadNames(unittest.TestCase):
    def test_what_survives(self):
        cases = {
            "report.pdf": "report.pdf",
            "..\\..\\DirtyFork.yaml": "DirtyFork.yaml",
            "/etc/passwd": "passwd",
            "C:\\Windows\\win.ini": "win.ini",
            "file.txt:hidden": "hidden",
            ".htaccess": "htaccess",
            ".upload-x.part": "upload-x.part",
            "name. . .": "name",
            "CON": "_CON",
            "nul.txt": "_nul.txt",
            "a<b>c?.txt": "a_b_c_.txt",
            "tab\there.txt": "tab_here.txt",
            "caf\u00e9 \u263a.zip": "caf\u00e9 \u263a.zip",
            "...": None,
            "": None,
            "x" * 200 + ".zip": "x" * 116 + ".zip",
            # cut to length, what is left must still not start with a dot
            "." + " " * 120 + ".upload-x": "upload-x",
        }
        for sent, expected in cases.items():
            self.assertEqual(file_transfer.safe_upload_name(sent), expected, repr(sent))

    def test_sizes(self):
        p = file_transfer.parse_size
        self.assertEqual(p("100 MB", 1), 100 * 1024 ** 2)
        self.assertEqual(p("1.5GB", 1), int(1.5 * 1024 ** 3))
        self.assertEqual(p("512", 1), 512)
        self.assertEqual(p(4096, 1), 4096)
        self.assertEqual(p(None, 7), 7)
        self.assertEqual(p("lots", 7), 7)
        self.assertEqual(p(0, 7), 0)  # (keep no reserve: not "absent")
        self.assertEqual(p("0 MB", 7), 0)

    def test_publishing_never_replaces_a_file(self):
        d = tempfile.mkdtemp(prefix="publish-")
        try:
            policy = file_transfer.UploadPolicy(directory=d, keep_free=0)
            temp = os.path.join(d, ".upload-1.part")
            with open(temp, "wb") as f:
                f.write(b"new")
            with open(os.path.join(d, "x.bin"), "wb") as f:
                f.write(b"old")
            self.assertFalse(policy.publish(temp, "x.bin"))  # (it arrived meanwhile)
            with open(os.path.join(d, "x.bin"), "rb") as f:
                self.assertEqual(f.read(), b"old")
            self.assertFalse(os.path.exists(temp))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_nor_takes_a_name_that_arrived_in_the_other_folder(self):
        # (a trusted and an untrusted upload of one name, at once: one goes to
        # the library, the other to the pending folder)
        top = tempfile.mkdtemp(prefix="publish-")
        try:
            mine, other = os.path.join(top, "pending"), os.path.join(top, "files")
            os.makedirs(mine)
            os.makedirs(other)
            policy = file_transfer.UploadPolicy(directory=mine, others=(other,), keep_free=0)
            self.assertEqual(policy.check("x.bin", 3), "x.bin")
            with open(os.path.join(other, "x.bin"), "wb") as f:
                f.write(b"theirs")
            temp = os.path.join(mine, ".upload-1.part")
            with open(temp, "wb") as f:
                f.write(b"new")
            self.assertFalse(policy.publish(temp, "x.bin"))
            self.assertEqual(os.listdir(mine), [])
            self.assertEqual(policy.refused, [("x.bin", "a file with that name arrived meanwhile")])
        finally:
            shutil.rmtree(top, ignore_errors=True)


class UploadRoom(unittest.TestCase):
    def test_an_upload_that_fills_the_disk_is_stopped(self):
        """A sender can declare no size (or a false one): the free space is
        checked while the data arrives too."""
        d = tempfile.mkdtemp(prefix="room-")
        try:
            policy = file_transfer.UploadPolicy(directory=d, keep_free=10 ** 18)  # (never enough)
            name = policy.check("big.bin", None)
            self.assertEqual(name, "big.bin")  # (no size declared: nothing to refuse yet)
            sink = file_transfer._UploadSink(policy, name)
            with self.assertRaises(file_transfer.zmodem.TransferError):
                for _ in range(3):
                    sink.write(b"z" * file_transfer.ROOM_CHECK)
            sink.discard()
            self.assertEqual(policy.refused, [("big.bin", "there is not enough room for it")])
            self.assertEqual(os.listdir(d), [])
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TransferSession(unittest.TestCase):
    def test_a_transfer_counts_as_activity(self):
        """A download receives almost nothing for its length: without this, a
        long one ends in an idle disconnect at the next menu."""
        class Reader:
            touched = 0

            async def read_raw(self, n):
                return b""  # (nothing more comes)

            read = read_raw

            def touch(self):
                Reader.touched += 1
        user = _setup.make_user()
        user.reader = Reader()

        async def go():
            async with file_transfer._binary_session(user):
                pass
        asyncio.run(go())
        self.assertEqual(Reader.touched, 1)

    def test_a_file_gone_before_sending_is_a_failure_not_a_crash(self):
        from test_zmodem import End, Pipe
        user = _setup.make_user()

        async def direct(user, text, work):
            a, b = Pipe(), Pipe()
            # (a receiver that answers; the file is looked at after that)
            b.write(file_transfer.zmodem.Encoder.hex_header(file_transfer.zmodem.ZRINIT, bytes([0, 0, 0, 0x23])))
            return await work(End(b, a))
        with mock.patch.object(file_transfer, "_with_screen", direct):
            result = asyncio.run(file_transfer.send_files_zmodem(user, [os.path.join(
                tempfile.gettempdir(), "no-such-file-for-dirtyfork.bin")]))
        self.assertNotEqual(result.status, file_transfer.success)
        self.assertTrue(result.message.startswith("The transfer failed:"), result.message)

    def test_zmodem_sends_in_the_blocks_the_link_asks_for(self):
        """A modem's writer asks for small blocks, a drain after each: at
        modem speeds what is queued beyond the line's buffer (16 KiB is a
        minute at 2400 bps) holds up a repair or a cancel."""
        user = _setup.make_user()
        default = file_transfer.zmodem.Settings()
        settings = file_transfer._settings(user)
        self.assertEqual((settings.drain_every, settings.subpacket_size),
                         (default.drain_every, default.subpacket_size))
        user.writer.transfer_block = 256  # (a 2400 bps modem's)
        settings = file_transfer._settings(user)
        self.assertEqual((settings.drain_every, settings.subpacket_size), (256, 256))


class LibraryFiles(unittest.TestCase):
    """file.py: what a caller can download, uploads, and vetting them."""

    def setUp(self):
        import file
        import library
        from test_library import make_library
        self.file, self.library = file, library
        self.dir = tempfile.mkdtemp(prefix="library-")
        self.lib = make_library(self.dir)
        os.makedirs(self.lib.pending_dir, exist_ok=True)
        self.write(self.lib.files_dir, "game.zip", b"a game")
        self.write(self.lib.pending_dir, "unvetted.zip", b"not approved")
        self.write(self.lib.files_dir, ".upload-x.part", b"someone's upload in progress")
        self.write(self.dir, "secret.db", b"password hashes")
        con = library.connect(self.lib)
        self.game = library.put(con, root="uploads", path="game.zip", size=6, uploader="a")
        self.unvetted = library.put(con, root="pending", path="unvetted.zip", size=12, uploader="b")
        con.commit()
        con.close()
        self.patches = [mock.patch.object(file, "_library", lambda: self.lib)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, folder, name, data):
        with open(os.path.join(folder, name), "wb") as f:
            f.write(data)

    def entry(self, file_id):
        return asyncio.run(self.file._db(self.library.get, file_id))

    def user(self, handle="caller", keys=()):
        user = _setup.make_user()
        user.handle, user.keys = handle, set(keys)
        return user

    def test_what_can_be_sent(self):
        f = self.file
        caller, sysop = self.user(), self.user("boss", {"sysop"})
        self.assertEqual(f._download_path(caller, self.entry(self.game)),
                         os.path.realpath(os.path.join(self.lib.files_dir, "game.zip")))
        self.assertIsNone(f._download_path(caller, self.entry(self.unvetted)))  # (awaiting approval)
        self.assertIsNotNone(f._download_path(sysop, self.entry(self.unvetted)))

    def test_a_typed_name_is_looked_up_never_joined_to_a_folder(self):
        f = self.file
        user = self.user()
        shown, sent = mock.AsyncMock(), mock.AsyncMock()
        for typed in ("../secret.db", "..\\secret.db", os.path.join(self.dir, "secret.db"),
                      ".upload-x.part", "unvetted.zip", "library.db"):
            with mock.patch.object(f, "show_message_box", shown), \
                    mock.patch.object(f, "send_files_zmodem", sent), \
                    mock.patch.object(f, "send_files_ymodem", sent), \
                    mock.patch.object(f, "_transfers_refused", mock.AsyncMock(return_value=False)), \
                    mock.patch.object(f, "ansi_cls", mock.AsyncMock()), \
                    mock.patch.object(f, "_read_line", mock.AsyncMock(return_value=typed)):
                asyncio.run(f._download_file(user))
            sent.assert_not_awaited()
            self.assertIn("No file in the library", shown.await_args.args[1], typed)

    def upload(self, user, names, answers, during=None, tell=None):
        """_upload_file, as if *names* arrived and the caller typed *answers*
        (an exception among them is raised instead; during() runs before each
        answer). Returns (the sysops' popups, the caller's message boxes); with
        *tell*, that is what pages the sysops instead."""
        f = self.file
        popups, messages = [], []

        async def receive(user, policy):
            for name in names:
                if policy.check(name, 1):
                    self.write(policy.directory, name, b"data")
                    policy.saved.append(name)
            return f.RetVals(status=f.success, message="Transfer complete.")
        answers = iter(answers)

        async def read_line(user, max_len=200):
            if during:
                during()
            answer = next(answers)
            if isinstance(answer, BaseException):
                raise answer
            return answer

        async def tell_sysops(text):
            popups.append(text)

        async def show(user, text, *args, **kwargs):
            messages.append(text)
        with mock.patch.object(f, "_choose_protocol", mock.AsyncMock(return_value="zmodem")), \
                mock.patch.object(f, "receive_files_zmodem", receive), \
                mock.patch.object(f, "show_message_box", show), \
                mock.patch.object(f, "_tell_sysops", tell or tell_sysops), \
                mock.patch.object(f, "_read_line", read_line):
            asyncio.run(f._upload_file(user))
        return popups, messages

    def catalogued(self, name):
        con = self.library.connect(self.lib)
        try:
            row = con.execute("SELECT id FROM files WHERE path = ?", (name,)).fetchone()
            return self.library.get(con, row[0]) if row else None
        finally:
            con.close()

    def test_a_trusted_upload_is_listed_at_once(self):
        user = self.user("alice", {"trusted_uploader"})
        valid = self.file._valid_tags()
        popups, _ = self.upload(user, ["mine.bin"], ["my description", f"2, {valid[0].upper()}, nonesuch, 2"])
        e = self.catalogued("mine.bin")
        self.assertEqual((e.root, e.uploader, e.description), ("uploads", "alice", "my description"))
        self.assertEqual(e.tags, (valid[1], valid[0]))
        self.assertTrue(os.path.isfile(os.path.join(self.lib.files_dir, "mine.bin")))
        self.assertEqual(popups, [])

    def test_anyone_elses_waits_for_approval_and_the_sysops_are_told(self):
        user = self.user("mallory")
        popups, _ = self.upload(user, ["tool.exe"], ["useful", ""])
        e = self.catalogued("tool.exe")
        self.assertEqual((e.root, e.uploader, e.description), ("pending", "mallory", "useful"))
        self.assertTrue(os.path.isfile(os.path.join(self.lib.pending_dir, "tool.exe")))
        self.assertFalse(os.path.exists(os.path.join(self.lib.files_dir, "tool.exe")))
        self.assertIsNone(self.file._download_path(self.user(), e))
        self.assertEqual(len(popups), 1)
        self.assertIn("mallory uploaded tool.exe", popups[0])

    def test_an_upload_may_not_take_a_name_in_either_folder(self):
        user = self.user("mallory")
        self.upload(user, ["game.zip", "unvetted.zip", "catalog", "zips"], [])
        con = self.library.connect(self.lib)
        try:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM files").fetchone()[0], 2)
        finally:
            con.close()
        with open(os.path.join(self.lib.files_dir, "game.zip"), "rb") as fh:
            self.assertEqual(fh.read(), b"a game")

    def test_the_sysops_hear_of_an_upload_once_its_details_are_in(self):
        seen = []

        async def tell_sysops(text):
            seen.append(self.catalogued("tool.exe").description)
        self.upload(self.user("mallory"), ["tool.exe"], ["useful", ""], tell=tell_sysops)
        self.assertEqual(seen, ["useful"])

    def test_an_upload_rejected_while_its_details_are_asked_for(self):

        def reject():  # (the sysop, quicker than the uploader)
            con = self.library.connect(self.lib)
            try:
                e = self.catalogued("tool.exe")
                if e:
                    self.assertIsNone(self.library.reject(self.lib, con, e.id))
            finally:
                con.close()
        popups, messages = self.upload(self.user("mallory"), ["tool.exe"], ["useful", "1"], during=reject)
        self.assertIsNone(self.catalogued("tool.exe"))
        self.assertIn("No longer in the library", messages[-1])  # (not "catalogued successfully")
        self.assertEqual(popups, [])  # (nothing waits for the sysops)

    def test_a_caller_leaving_mid_details_still_has_the_sysops_told(self):
        f = self.file
        told = mock.AsyncMock()
        with self.assertRaises(f.Disconnected):
            self.upload(self.user("mallory"), ["tool.exe"], [f.Disconnected()], tell=told)
        told.assert_awaited_once()
        self.assertTrue(self.catalogued("tool.exe").pending)

    def test_a_superscript_two_at_the_tag_prompt(self):
        # ("²".isdigit(), but int() refuses it: an AZERTY keyboard's top-left key)
        f = self.file
        self.upload(self.user("mallory"), ["tool.exe"], ["useful", "², 1"])
        self.assertEqual(self.catalogued("tool.exe").tags, (f._valid_tags()[0],))

    def vet(self, file_id, keys):
        """_vet_one on upload *file_id*, with these keys pressed."""
        import input_fields
        f = self.file
        keys = iter(keys)

        async def key(user, *args, **kwargs):
            return next(keys)
        shown = mock.AsyncMock()
        with mock.patch.object(input_fields, "get_input_key", key), \
                mock.patch.object(f, "show_message_box", shown):
            asyncio.run(f._vet_one(self.user("boss", {"sysop"}), self.entry(file_id)))
        return shown.await_args.args[1]

    def test_vetting_approve(self):
        self.assertEqual(self.vet(self.unvetted, ["\r"]), "unvetted.zip is now in the library.")  # (Approve)
        e = self.entry(self.unvetted)
        self.assertEqual((e.root, e.path), ("uploads", "unvetted.zip"))
        self.assertTrue(os.path.isfile(os.path.join(self.lib.files_dir, "unvetted.zip")))

    def test_vetting_reject(self):
        from keyboard_codes import right, tab
        # Tab round the five buttons back to Approve, Right to Reject, Enter; then Delete, the first button
        self.assertEqual(self.vet(self.unvetted, [tab] * 5 + [right, "\r", "\r"]), "unvetted.zip was deleted.")
        self.assertIsNone(self.entry(self.unvetted))
        self.assertFalse(os.path.exists(os.path.join(self.lib.pending_dir, "unvetted.zip")))

    def press(self, keys, work):
        """Run work() (a coroutine function) with these keys pressed, in
        the forms and in the lists. Returns the message boxes shown."""
        import input_fields
        f = self.file
        keys = iter(keys)
        shown = []

        async def key(user, *args, **kwargs):
            return next(keys)

        async def show(user, text, *args, **kwargs):
            shown.append(text)
        with mock.patch.object(input_fields, "get_input_key", key), mock.patch.object(f, "get_input_key", key), \
                mock.patch.object(f, "show_message_box", show):
            asyncio.run(work())
        return shown

    def test_editing_from_the_vetting_screen(self):
        from keyboard_codes import tab, insert
        f = self.file
        sysop = self.user("boss", {"sysop"})
        keys = ([tab, tab, "\r"]                         # Approve, Reject, Edit
                + list("a fine tool") + [tab]            # the description, then the tags
                + [insert] + list("utility") + ["\r"]    # a tag added
                + [tab, "\r"]                            # Save
                + [tab, tab, tab, tab, "\r"])            # back at the vetting screen: Back
        shown = self.press(keys, lambda: f._vet_one(sysop, self.entry(self.unvetted)))
        e = self.entry(self.unvetted)
        self.assertEqual((e.description, e.tags, e.edited, e.root), ("a fine tool", ("utility",), True, "pending"))
        self.assertIn("Saved the details of unvetted.zip.", shown)

    def test_e_edits_from_a_list_for_a_sysop_only(self):
        from array import array
        from keyboard_codes import tab
        f = self.file
        caller, sysop = self.user(), self.user("boss", {"sysop"})
        self.press(["e", "q"], lambda: f._pick_files(caller, f._Items(array("q", [self.game])), "t"))
        self.assertFalse(self.entry(self.game).edited)
        self.press(["e"] + list("ok") + [tab, tab, "\r", "q"],
                   lambda: f._pick_files(sysop, f._Items(array("q", [self.game])), "t"))
        self.assertEqual((self.entry(self.game).description, self.entry(self.game).edited), ("ok", True))

    def test_edit_files_is_the_search_with_the_same_form(self):
        f = self.file
        seen = {}

        async def search(user, open_file=None, heading=None):
            seen["open_file"] = open_file
        with mock.patch.object(f, "_search_files", search):
            asyncio.run(f.edit_files(self.user("boss", {"sysop"})))
            self.assertIs(seen.pop("open_file"), f._edit_details)
            asyncio.run(f.edit_files(self.user()))  # (not a sysop: nothing)
            self.assertEqual(seen, {})

    def test_a_list_keeps_the_rows_on_screen_when_its_cache_is_full(self):
        f = self.file
        from array import array
        items = f._Items(array("q", range(1, 30)))
        items.CACHE = 8

        async def fetch(work, ids):
            return [self.library.Entry(id=i, root="uploads", path=f"{i}.zip", name=f"{i}.zip", size=1,
                                       mtime=0, description="", uploader="", added=0, source=None,
                                       source_key=None, fingerprint=None, tags=()) for i in ids]
        with mock.patch.object(f, "_db", fetch):
            asyncio.run(items.load(0, 8))
            asyncio.run(items.load(1, 9))  # (one more row: past the cache's size)
        self.assertEqual([items.item(i)[0] for i in range(1, 9)], ["file"] * 8)

    def test_a_sysop_who_refuses_pages_still_hears_of_an_upload(self):
        import common
        f = self.file
        sysop, caller = self.user("boss", {"sysop"}), self.user("someone")
        sent = mock.AsyncMock(return_value=(True, None))
        with mock.patch.dict(common.global_data.users, {"boss": sysop, "someone": caller}, clear=True), \
                mock.patch("bbs_msg.send_popup", sent):
            asyncio.run(f._tell_sysops("x uploaded y"))
        sent.assert_awaited_once()
        self.assertIs(sent.await_args.args[0], sysop)
        self.assertTrue(sent.await_args.kwargs.get("skip_checks"))  # (allow_pages: false doesn't stop it)

    def test_a_tenth_digit_keeps_the_number_typed(self):
        from array import array
        f = self.file
        items = f._Items(array("q", range(1, 16)))
        keys = iter(list("200000000") + ["0"] + ["\x08"] * 8 + ["\r", "\r"])  # (go to file 2, open it)

        async def key(user, *args, **kwargs):
            return next(keys)

        async def fetch(work, ids):
            return [self.library.Entry(id=i, root="uploads", path=f"{i}.zip", name=f"{i}.zip", size=1,
                                       mtime=0, description="", uploader="", added=0, source=None,
                                       source_key=None, fingerprint=None, tags=()) for i in ids]
        with mock.patch.object(f, "get_input_key", key), mock.patch.object(f, "_db", fetch):
            action, item, _ = asyncio.run(f._show_list(self.user(), items, "t", "controls"))
        self.assertEqual((action, item[1].name), ("open", "2.zip"))

    def test_sizes_fit_their_column(self):
        f = self.file
        for size in (0, 1023, 1024 ** 2 - 1, 999 * 1024 ** 2, 9 * 1024 ** 3, 100 * 1024 ** 3,
                     1023 * 1024 ** 3 + 10 ** 6, 5 * 1024 ** 4, 999 * 1024 ** 4):
            self.assertLessEqual(len(f._format_size(size)), 7, size)

    def test_the_search_counts_the_files_once(self):
        f = self.file
        queries = iter(["tag:none", "also:", "nothing", ""])
        counted = []
        real = self.library.listed_count

        async def form(user, query, count, heading):
            return next(queries)
        with mock.patch.object(f, "_search_form", form), \
                mock.patch.object(f, "show_message_box", mock.AsyncMock()), \
                mock.patch.object(self.library, "listed_count", lambda con: counted.append(1) or real(con)):
            asyncio.run(f._search_files(self.user()))
        self.assertEqual(counted, [1])

    def test_a_sysop_logging_in_hears_of_uploads_waiting(self):
        f = self.file
        sent = mock.AsyncMock()
        with mock.patch("bbs_msg.send_popup", sent):
            asyncio.run(f.tell_sysop_of_pending(self.user("boss", {"sysop"})))
            asyncio.run(f.tell_sysop_of_pending(self.user("caller")))
        sent.assert_awaited_once()
        self.assertIn("1 upload is waiting", sent.await_args.args[1])


if __name__ == "__main__":
    unittest.main()
