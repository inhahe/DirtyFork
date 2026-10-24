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

    def test_zmodem_over_a_modem_drains_every_subpacket(self):
        """What is queued beyond the line's own buffer holds up a repair or a
        cancel: at modem speeds 16 KiB is a minute."""
        user = _setup.make_user()
        user.connection_type = "telnet"
        self.assertEqual(file_transfer._settings(user).drain_every,
                         file_transfer.zmodem.Settings().drain_every)
        user.connection_type = "modem"
        self.assertEqual(file_transfer._settings(user).drain_every, file_transfer.MODEM_DRAIN_EVERY)


class LibraryFiles(unittest.TestCase):
    """file.py: what a caller can download, and the catalogue."""

    def setUp(self):
        import file
        self.file = file
        self.dir = tempfile.mkdtemp(prefix="library-")
        self.lib = os.path.join(self.dir, "files")
        os.makedirs(self.lib)
        with open(os.path.join(self.lib, "game.zip"), "wb") as f:
            f.write(b"a game")
        with open(os.path.join(self.lib, ".upload-x.part"), "wb") as f:
            f.write(b"someone's upload in progress")
        with open(os.path.join(self.dir, "secret.db"), "wb") as f:
            f.write(b"password hashes")
        self.patches = [mock.patch.object(file, "_files_dir", lambda: self.lib),
                        mock.patch.object(file, "_meta_path", lambda: os.path.join(self.lib, "meta.yaml"))]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_only_files_the_library_lists_can_be_downloaded(self):
        f = self.file
        self.assertEqual(f._library_path("game.zip"), os.path.realpath(os.path.join(self.lib, "game.zip")))
        for name in ("../secret.db", "..\\secret.db", os.path.join(self.dir, "secret.db"),
                     ".upload-x.part", "meta.yaml", "nothing.zip", ""):
            self.assertIsNone(f._library_path(name), name)

    def test_a_typed_path_out_of_the_library_sends_nothing(self):
        f = self.file
        user = _setup.make_user()
        shown, sent = mock.AsyncMock(), mock.AsyncMock()
        with mock.patch.object(f, "show_message_box", shown), \
                mock.patch.object(f, "send_files_zmodem", sent), \
                mock.patch.object(f, "send_files_ymodem", sent), \
                mock.patch.object(f, "_choose_protocol", mock.AsyncMock(return_value="zmodem")):
            asyncio.run(f._do_download(user, "../secret.db"))
        sent.assert_not_awaited()
        self.assertIn("File not found", shown.await_args.args[1])

    def test_cataloguing_keeps_what_others_catalogued_meanwhile(self):
        f = self.file
        user = _setup.make_user()
        user.handle = "A"
        with open(os.path.join(self.lib, "mine.bin"), "wb") as fh:
            fh.write(b"x")

        async def receive(user, policy):
            policy.saved.append("mine.bin")
            return f.RetVals(status=f.success, message="Transfer complete.")
        answers = iter(["my description", ""])

        async def read_line(user, max_len=200):
            # While caller A types, caller B catalogues their own upload
            meta = f._load_meta()
            meta["theirs.zip"] = {"keys": [], "description": "B's file"}
            f._save_meta(meta)
            return next(answers)
        with mock.patch.object(f, "_choose_protocol", mock.AsyncMock(return_value="zmodem")), \
                mock.patch.object(f, "receive_files_zmodem", receive), \
                mock.patch.object(f, "show_message_box", mock.AsyncMock()), \
                mock.patch.object(f, "_read_line", read_line):
            asyncio.run(f._upload_file(user))
        meta = f._load_meta()
        self.assertEqual(meta["mine.bin"]["description"], "my description")
        self.assertEqual(meta["theirs.zip"]["description"], "B's file")


if __name__ == "__main__":
    unittest.main()
