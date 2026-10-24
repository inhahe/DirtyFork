"""file_transfer.py's upload policy: names, sizes, publishing. (Transfers
themselves: test_zmodem*.py, test_web_transfers.py.)"""
import os
import shutil
import tempfile
import unittest

import _setup  # noqa: F401
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


if __name__ == "__main__":
    unittest.main()
