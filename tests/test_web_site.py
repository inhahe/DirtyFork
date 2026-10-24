"""web/site: the two pages stay the same page, and the CDN's files are the
vendored ones (the integrity hashes in bbs.html match the copies)."""
import base64
import hashlib
import os
import re
import unittest

import _setup

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


if __name__ == "__main__":
    unittest.main()
