The DirtyFork BBS web terminal (bbs.html, bbs-local.html)
==========================================================

The source of these files is the DirtyFork project (web/site there);
web\deploy-site.ps1 copies them into the web site. Change them there.

How the page reaches the BBS
----------------------------
bbs.html -> wss://<this site>/bbs-ws -> nginx -> DirtyFork's web/terminal_bridge.py
(127.0.0.1:8023, a Task Scheduler task) -> telnet to the BBS on 127.0.0.1:23.
See "Web Terminal" in DirtyFork's DOCS.md.

The two pages
-------------
bbs.html        the page in use: loads xterm.js and zmodem.js from the jsDelivr CDN,
                with integrity hashes.
bbs-local.html  the same page loading the copies in vendor\ instead. Nothing links
                to it. To make it the page in use, copy it over bbs.html.

Files
-----
bbs.js     the page's script: the terminal, its size, the connection, file transfers
bbs.css    the page's look, and the font
fonts\WebPlus_IBM_VGA_8x16.woff
           the IBM VGA 8x16 text-mode font, with extra Unicode coverage, from
           VileR's "Ultimate Oldschool PC Font Pack" v2.2, https://int10h.org/oldschool-pc-fonts/
           Licence: CC BY-SA 4.0 (fonts\LICENSE-font.txt). Unchanged.
vendor\xterm-6.0.0.js, xterm-6.0.0.css
           xterm.js 6.0.0 (npm @xterm/xterm), https://github.com/xtermjs/xterm.js
           Licence: MIT (vendor\LICENSE-xterm.txt). Unchanged.
vendor\addon-webgl-0.19.0.js
           xterm.js's WebGL renderer, 0.19.0 (npm @xterm/addon-webgl). Same licence.
           Without WebGL the page falls back to xterm.js's own DOM renderer.
vendor\zmodem-0.1.10.js
           zmodem.js 0.1.10 (npm zmodem.js, its dist/zmodem.js),
           https://github.com/FGasper/zmodemjs. Licence: Apache 2.0
           (vendor\LICENSE-zmodem.txt). Unchanged. Its build logs every chunk it parses
           to the console; bbs.js drops those lines.

The vendored files are byte for byte what the CDN serves for the addresses in
bbs.html (DirtyFork's tests/test_web_site.py checks the hashes).

Updating a library
------------------
Put the new file in vendor\ under its new version's name, change its address and
integrity hash in bbs.html (sha384, base64: openssl dgst -sha384 -binary FILE |
openssl base64 -A), make bbs-local.html the same page again, and run DirtyFork's
tests.
