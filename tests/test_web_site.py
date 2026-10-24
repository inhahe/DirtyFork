"""web/site: the two pages stay the same page, the CDN's files are the
vendored ones (the integrity hashes in bbs.html match the copies), and bbs.js
connects only from a page a web server served."""
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import unittest

import _setup

NODE = shutil.which("node")
SITE = os.path.join(_setup.PROJECT, "web", "site")
VENDOR = "bbs-term/vendor/"
# CDN address -> the vendored copy's name
CDN = {
    "https://cdn.jsdelivr.net/npm/@xterm/xterm@6.0.0/css/xterm.css": "xterm-6.0.0.css",
    "https://cdn.jsdelivr.net/npm/@xterm/xterm@6.0.0/lib/xterm.js": "xterm-6.0.0.js",
    "https://cdn.jsdelivr.net/npm/@xterm/addon-webgl@0.19.0/lib/addon-webgl.js": "addon-webgl-0.19.0.js",
    "https://cdn.jsdelivr.net/npm/zmodem.js@0.1.10/dist/zmodem.js": "zmodem-0.1.10.js",
}


def read(name):
    with open(os.path.join(SITE, name), encoding="utf-8") as f:
        return f.read()


class Pages(unittest.TestCase):
    def test_the_local_page_is_the_cdn_page_with_local_files(self):
        cdn, local = read("bbs.html"), read("bbs-local.html")
        expected = re.sub(r'\n\s+integrity="sha384-[^"]+" crossorigin="anonymous"', "", cdn)
        for url, name in CDN.items():
            expected = expected.replace(url, VENDOR + name)
        expected = expected.replace(
            "<!-- xterm.js and zmodem.js from the jsDelivr CDN (bbs-local.html: the copies in bbs-term/vendor) -->",
            "<!-- xterm.js and zmodem.js from the copies in bbs-term/vendor (bbs.html: from the jsDelivr CDN) -->")
        self.assertEqual(local, expected)

    def test_integrity_hashes_match_the_vendored_copies(self):
        page = read("bbs.html")
        found = re.findall(r'(?:href|src)="(https://[^"]+)"\s+integrity="sha384-([^"]+)"', page)
        self.assertEqual(sorted(url for url, _ in found), sorted(CDN))
        for url, digest in found:
            with open(os.path.join(SITE, VENDOR, CDN[url]), "rb") as f:
                actual = base64.b64encode(hashlib.sha384(f.read()).digest()).decode()
            self.assertEqual(digest, actual, url)

    def test_everything_the_pages_load_from_the_site_exists(self):
        for page in ("bbs.html", "bbs-local.html"):
            for ref in re.findall(r'(?:href|src)="([^":]+)"', read(page)):
                self.assertTrue(os.path.isfile(os.path.join(SITE, ref)), (page, ref))
        for ref in re.findall(r'url\("([^"]+)"\)', read("bbs-term/bbs.css")):
            self.assertTrue(os.path.isfile(os.path.join(SITE, "bbs-term", ref)), ref)


PAGE_IN_NODE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "page_in_node.js")
CONTROLS = ["size", "sharp", "fullscreen"]


@unittest.skipUnless(NODE, "node is not on PATH")
class Script(unittest.TestCase):
    """bbs.js, run in Node by page_in_node.js as the page runs it."""

    def run_page(self, protocol, host, libraries="loaded"):
        script = os.path.join(SITE, "bbs-term", "bbs.js")
        done = subprocess.run([NODE, PAGE_IN_NODE, script, protocol, host, libraries],
                              capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def test_a_served_page_connects_to_its_own_server(self):
        page = self.run_page("https:", "bbs.example")
        self.assertEqual(page["sockets"], ["wss://bbs.example/bbs-ws"])
        self.assertEqual(page["status"], "Connecting...")
        self.assertEqual(page["hidden"], [])

    def test_a_page_opened_from_the_disk_says_so_instead_of_connecting(self):
        # (Browsers read "ws:///bbs-ws" as the host "bbs-ws", which fails as
        # "The connection was lost.")
        page = self.run_page("file:", "")
        self.assertEqual(page["sockets"], [])
        self.assertIn("opened from the disk", page["status"])
        self.assertEqual(page["hidden"], CONTROLS)

    def test_a_page_whose_libraries_did_not_load_says_so(self):
        page = self.run_page("https:", "bbs.example", libraries="missing")
        self.assertEqual(page["sockets"], [])
        self.assertIn("could not load its scripts", page["status"])
        self.assertEqual(page["hidden"], CONTROLS)


if __name__ == "__main__":
    unittest.main()
