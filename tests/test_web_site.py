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


# Runs bbs.js in Node as a page at the given location would, with xterm.js,
# zmodem.js and the page's elements as stand-ins that accept anything, and
# prints the WebSockets it opened and what the status line says.
PAGE_IN_NODE = r"""
const vm = require("vm"), fs = require("fs");
const [script, protocol, host, libraries] = process.argv.slice(1);
function anything() {
    const set = {};
    return new Proxy(function () {}, {
        get(_, key) {
            if (key === Symbol.toPrimitive) return () => 0;
            if (key === "then") return undefined;  // (not a promise)
            if (!(key in set)) set[key] = anything();
            return set[key];
        },
        set(_, key, value) { set[key] = value; return true; },
        apply() { return anything(); },
        construct() { return anything(); },
    });
}
const elements = {}, sockets = [];
class WebSocket { constructor(url) { sockets.push(url); } }
WebSocket.OPEN = 1;
const page = {
    location: { protocol, host },
    document: {
        readyState: "complete",
        addEventListener() {},
        getElementById(id) { return elements[id] || (elements[id] = anything()); },
    },
    window: anything(), navigator: anything(), getComputedStyle: anything(),
    localStorage: { getItem() { return null; }, setItem() {} },
    Terminal: anything(), WebglAddon: anything(), Zmodem: anything(), WebSocket,
    console, TextEncoder, setTimeout, clearTimeout,
};
if (libraries === "missing") delete page.Terminal;
vm.runInNewContext(fs.readFileSync(script, "utf8"), page);
console.log(JSON.stringify({ sockets, status: page.document.getElementById("status").textContent }));
"""


@unittest.skipUnless(NODE, "node is not on PATH")
class Script(unittest.TestCase):
    def run_page(self, protocol, host, libraries="loaded"):
        script = os.path.join(SITE, "bbs-term", "bbs.js")
        done = subprocess.run([NODE, "-e", PAGE_IN_NODE, script, protocol, host, libraries],
                              capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def test_a_served_page_connects_to_its_own_server(self):
        page = self.run_page("https:", "bbs.example")
        self.assertEqual(page["sockets"], ["wss://bbs.example/bbs-ws"])
        self.assertEqual(page["status"], "Connecting...")

    def test_a_page_opened_from_the_disk_says_so_instead_of_connecting(self):
        # (Browsers read "ws:///bbs-ws" as the host "bbs-ws", which fails as
        # "The connection was lost.")
        page = self.run_page("file:", "")
        self.assertEqual(page["sockets"], [])
        self.assertIn("opened from the disk", page["status"])

    def test_a_page_whose_libraries_did_not_load_says_so(self):
        page = self.run_page("https:", "bbs.example", libraries="missing")
        self.assertEqual(page["sockets"], [])
        self.assertIn("could not load its scripts", page["status"])


if __name__ == "__main__":
    unittest.main()
