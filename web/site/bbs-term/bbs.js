// The DirtyFork BBS web terminal: xterm.js for the screen, zmodem.js for file
// transfers, and a WebSocket to DirtyFork's bridge (web/terminal_bridge.py in
// the DirtyFork project), which speaks telnet to the BBS.
//
// The bridge's protocol: the first message is text, {"cols": C, "rows": R};
// after that, binary messages carry the terminal's bytes both ways.
//
// The screen's size (columns x rows) is fixed for a connection: the BBS reads
// it once, at login. Resizing the window scales the font instead; a new size
// takes effect on the next connection.
(function () {
    "use strict";

    var FONT = "WebPlus IBM VGA 8x16";  // 8x16 cells: width = size / 2
    var SUBPROTOCOL = "dirtyfork-terminal";
    var PRESETS = ["80x25", "80x43", "80x50", "132x37", "132x52", "fill"];
    var MIN_COLS = 80, MIN_ROWS = 25;           // what "fill" never goes below
    var MAX_COLS = 400, MAX_ROWS = 200;         // what the bridge accepts
    var UPLOAD_CHUNK = 64 * 1024;
    var HIGH_WATER = 1024 * 1024;               // bytes queued on the socket before an upload waits
    var VGA = {
        background: "#000000", foreground: "#aaaaaa", cursor: "#aaaaaa", cursorAccent: "#000000",
        selectionBackground: "#5555ff88",
        black: "#000000", red: "#aa0000", green: "#00aa00", yellow: "#aa5500",
        blue: "#0000aa", magenta: "#aa00aa", cyan: "#00aaaa", white: "#aaaaaa",
        brightBlack: "#555555", brightRed: "#ff5555", brightGreen: "#55ff55", brightYellow: "#ffff55",
        brightBlue: "#5555ff", brightMagenta: "#ff55ff", brightCyan: "#55ffff", brightWhite: "#ffffff"
    };

    // zmodem.js 0.1.10's published build logs every chunk it parses
    // (console.log("consuming", [...])), which on a big transfer costs time
    // and memory (the console keeps it all). Drop just those.
    var consoleLog = console.log;
    console.log = function (first) {
        if (first === "consuming") return;
        return consoleLog.apply(console, arguments);
    };

    var $ = function (id) { return document.getElementById(id); };
    var settings = loadSettings();
    var term = null, ws = null, sentry = null, zsession = null;
    var grid = null;           // [cols, rows] of the current connection
    var ctrlX = 0;             // Ctrl+X pressed in a row during a transfer
    // After the caller cancels a download, what the BBS had already sent still
    // arrives, and the Sentry would show it as text. It is dropped until 300 ms
    // pass without any (the BBS itself waits for a second of quiet before it
    // redraws the screen, so that redraw is not lost).
    var dropping = null;

    function dropTheRest() {
        clearTimeout(dropping);
        dropping = setTimeout(function () { dropping = null; }, 300);
    }
    var encoder = new TextEncoder();

    // -- settings -------------------------------------------------------------

    function loadSettings() {
        var s = { size: "80x25", sharp: true };
        try {
            var saved = JSON.parse(localStorage.getItem("dirtyfork-terminal") || "{}");
            if (PRESETS.indexOf(saved.size) >= 0) s.size = saved.size;
            if (typeof saved.sharp === "boolean") s.sharp = saved.sharp;
        } catch (e) { /* (private browsing, or nothing saved) */ }
        return s;
    }

    function saveSettings() {
        try { localStorage.setItem("dirtyfork-terminal", JSON.stringify(settings)); } catch (e) { }
    }

    // -- sizing ---------------------------------------------------------------

    // The room the terminal has: #screen's content box (inside its padding)
    function room() {
        var el = $("screen"), style = getComputedStyle(el);
        var w = el.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
        var h = el.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
        return [Math.max(64, w), Math.max(64, h)];
    }

    // The largest font size at which cols x rows fits in w x h. "Sharp": a
    // whole number of device pixels per font pixel (16 per cell height).
    function fontSizeFor(cols, rows, w, h) {
        var biggest = Math.min(w * 2 / cols, h / rows);
        if (settings.sharp) {
            var dpr = window.devicePixelRatio || 1;
            var k = Math.floor(biggest * dpr / 16);
            if (k >= 1) return 16 * k / dpr;
        }
        return Math.max(6, Math.floor(biggest * 4) / 4);
    }

    // The grid "fill" gives: the biggest sharp font that still fits 80x25,
    // then as many cells as fit.
    function fillGrid() {
        var r = room();
        var size = fontSizeFor(MIN_COLS, MIN_ROWS, r[0], r[1]);
        var cols = Math.floor(r[0] / (size / 2)), rows = Math.floor(r[1] / size);
        return [Math.min(MAX_COLS, Math.max(MIN_COLS, cols)), Math.min(MAX_ROWS, Math.max(MIN_ROWS, rows))];
    }

    function chosenGrid() {
        if (settings.size === "fill") return fillGrid();
        var p = settings.size.split("x");
        return [parseInt(p[0], 10), parseInt(p[1], 10)];
    }

    function fitFont() {
        if (!term || !grid) return;
        var r = room();
        var size = fontSizeFor(grid[0], grid[1], r[0], r[1]);
        if (term.options.fontSize !== size) term.options.fontSize = size;
    }

    // -- the terminal ---------------------------------------------------------

    function makeTerminal() {
        term = new Terminal({
            fontFamily: '"' + FONT + '", monospace',
            fontSize: 16, lineHeight: 1, letterSpacing: 0,
            theme: VGA, drawBoldTextInBrightColors: true, minimumContrastRatio: 1,
            customGlyphs: false,          // the VGA font's own line and block glyphs
            cursorBlink: true, cursorStyle: "underline",
            scrollback: 1000, allowProposedApi: false,
            macOptionIsMeta: true
        });
        term.open($("screen"));
        try {
            var webgl = new WebglAddon.WebglAddon();
            webgl.onContextLoss(function () { webgl.dispose(); });  // (falls back to the DOM renderer)
            term.loadAddon(webgl);
        } catch (e) { /* no WebGL: the DOM renderer draws it */ }

        // Ctrl+V pastes and Ctrl+C copies a selection (the browser does both);
        // without a selection Ctrl+C is the BBS's.
        term.attachCustomKeyEventHandler(function (e) {
            if (e.type !== "keydown" || !e.ctrlKey || e.altKey || e.metaKey) return true;
            var k = e.key.toLowerCase();
            if (k === "v") return false;
            if (k === "c" && term.hasSelection()) {
                navigator.clipboard && navigator.clipboard.writeText(term.getSelection());
                return false;
            }
            return true;
        });
        term.onData(function (text) {
            if (!zsession) {
                send(encoder.encode(text));
                return;
            }
            // During a transfer the keys are not the BBS's; five Ctrl+X cancel
            // it, as the BBS tells callers (the same as the panel's button).
            ctrlX = text === "\x18" ? ctrlX + 1 : 0;
            if (ctrlX >= 5 && $("xfer-cancel").onclick) $("xfer-cancel").onclick();
        });
        term.onBinary(function (text) {  // mouse reports with bytes over 127
            var bytes = new Uint8Array(text.length);
            for (var i = 0; i < text.length; i++) bytes[i] = text.charCodeAt(i) & 255;
            send(bytes);
        });
        window.addEventListener("resize", fitFont);
    }

    function send(bytes) {
        if (ws && ws.readyState === WebSocket.OPEN) ws.send(bytes);
    }

    // -- the connection -------------------------------------------------------

    function setStatus(text, offerConnect) {
        $("status").textContent = text;
        $("connect").hidden = !offerConnect;
    }

    function connect() {
        if (ws) { ws.onclose = null; ws.close(); ws = null; }
        endTransfer();
        grid = chosenGrid();
        term.reset();
        term.resize(grid[0], grid[1]);
        fitFont();
        $("pending").hidden = true;
        setStatus("Connecting...", false);

        var url = (location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/bbs-ws";
        var socket = ws = new WebSocket(url, SUBPROTOCOL);
        socket.binaryType = "arraybuffer";
        held = [];
        skipping = 0;
        sentry = new Zmodem.Sentry({
            to_terminal: function (octets) { term.write(withoutZmodemHeaders(octets)); },
            sender: function (octets) { send(new Uint8Array(octets)); },
            on_detect: onDetect,
            on_retract: onRetract
        });
        socket.onopen = function () {
            socket.send(JSON.stringify({ cols: grid[0], rows: grid[1] }));
            setStatus("Connected (" + grid[0] + "x" + grid[1] + ").", false);
            term.focus();
        };
        socket.onmessage = function (e) {
            if (typeof e.data === "string") {  // the bridge's own notices (busy, BBS down)
                term.write(e.data);
                return;
            }
            if (dropping) {  // (the rest of a transfer the caller cancelled)
                dropTheRest();
                return;
            }
            try {
                sentry.consume(e.data);
            } catch (err) {
                // A transfer that broke: give the terminal back
                console.error(err);
                endTransfer("The transfer failed: " + (err.message || err));
            }
        };
        socket.onclose = function (e) {
            if (ws !== socket) return;
            ws = null;
            endTransfer();
            var why = {
                1000: e.reason ? "Disconnected: " + e.reason + "." : "Disconnected.",
                1011: "The BBS is not answering.",
                1013: "The web terminal is busy.",
                1008: "The connection was refused."
            }[e.code] || "The connection was lost.";
            setStatus(why, true);
        };
    }

    // -- file transfers -------------------------------------------------------

    function showTransfer(title) {
        $("xfer-title").textContent = title;
        $("xfer-name").textContent = "";
        $("xfer-bar").value = 0;
        $("xfer-count").textContent = "";
        $("xfer-choose").hidden = true;
        $("xfer").hidden = false;
    }

    function progress(name, done, total) {
        $("xfer-name").textContent = name;
        $("xfer-bar").max = total || 1;
        $("xfer-bar").value = done;
        $("xfer-count").textContent = human(done) + (total ? " of " + human(total) : "");
    }

    function human(n) {
        if (n < 1024) return n + " bytes";
        if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
        return (n / 1048576).toFixed(1) + " MB";
    }

    // Close the transfer panel; *message* (if any) is left in the status line.
    function endTransfer(message) {
        zsession = null;
        pending = null;
        retracting = false;
        ctrlX = 0;
        $("xfer").hidden = true;
        $("xfer-files").value = "";
        $("xfer-cancel").onclick = null;
        $("xfer-files").onchange = null;
        if (message) setStatus(message, !ws);
        if (term) term.focus();
    }

    // The Sentry shows the first ZMODEM header as text (it cannot know yet that
    // the caller will accept): leave out hex headers ("**", ZDLE, "B", 14 hex
    // digits, CR LF, XON), which are never meant to be seen.
    // A header can straddle two messages: a message ending in what may be
    // its start keeps those bytes back (written after 50 ms if nothing
    // completes them: a star drawn last must not wait), and the rest of one
    // is dropped from the next.
    var HEADER_START = [0x2A, 0x2A, 0x18, 0x42];
    var TRAILER = [0x0D, 0x0A, 0x8A, 0x11];
    var held = [], heldTimer = null;
    var skipping = 0;  // header bytes still to drop: hex digits, then up to 3 of CR LF XON

    function withoutZmodemHeaders(octets) {
        var input = held.length ? held.concat(Array.prototype.slice.call(octets)) : octets;
        held = [];
        clearTimeout(heldTimer);
        var out = [], i = 0, n = input.length;
        while (i < n) {
            if (skipping > 0) {
                if (skipping > 3 || TRAILER.indexOf(input[i]) >= 0) {
                    skipping--;
                    i++;
                } else {
                    skipping = 0;  // (a header without all its trailer)
                }
                continue;
            }
            if (input[i] === 0x2A) {
                var k = 0;
                while (k < 4 && i + k < n && input[i + k] === HEADER_START[k]) k++;
                if (k === 4) {
                    skipping = 14 + 3;
                    i += 4;
                    continue;
                }
                if (i + k === n) {  // the message ends in what may be a header's start
                    held = Array.prototype.slice.call(input, i);
                    heldTimer = setTimeout(flushHeld, 50);
                    break;
                }
            }
            out.push(input[i++]);
        }
        return new Uint8Array(out);
    }

    function flushHeld() {
        if (!held.length) return;
        var bytes = held;
        held = [];
        term.write(new Uint8Array(bytes));
    }

    // A BBS waiting for an upload says so again every few seconds, and the
    // Sentry takes each repeat for a new offer: it retracts the old one and
    // detects the new one, both in the same consume(). Such a pair keeps the
    // panel and swaps in the new detection; a retraction alone (the BBS gave
    // up) closes it.
    var retracting = false, pending = null;

    function onRetract() {
        if (!pending) return;  // (nothing waits on the page: the caller declined it already)
        retracting = true;
        Promise.resolve().then(function () {
            if (retracting) {
                retracting = false;
                pending = null;
                endTransfer("The BBS stopped waiting for the transfer.");
            }
        });
    }

    function onDetect(detection) {
        var role = detection.get_session_role();
        if (retracting && pending && pending.get_session_role() === role) {
            retracting = false;
            pending = detection;
            return;
        }
        retracting = false;
        if (role === "receive") download(detection);
        else upload(detection);
    }

    // The BBS sends: take every file it offers, and save each one.
    function download(detection) {
        var session = zsession = detection.confirm();
        var saved = [];
        showTransfer("Downloading");
        $("xfer-cancel").onclick = function () {
            try { session.abort(); } catch (e) { }
            dropTheRest();
            endTransfer("Download cancelled.");
        };
        session.on("offer", function (offer) {
            var info = offer.get_details(), chunks = [], got = 0;
            progress(info.name, 0, info.size);
            offer.accept({
                on_input: function (payload) {
                    chunks.push(new Uint8Array(payload));
                    got += payload.length;
                    progress(info.name, got, info.size);
                }
            }).then(function () {
                Zmodem.Browser.save_to_disk(chunks, info.name);
                saved.push(info.name);
            });
        });
        session.on("session_end", function () {
            if (zsession === session) {
                endTransfer(saved.length ? "Downloaded " + saved.join(", ") + "." : "Nothing was downloaded.");
            }
        });
        session.start();
    }

    // The BBS is ready to receive: ask which files (a click opens the file
    // dialog, which browsers allow only from a click), or take dropped ones.
    function upload(detection) {
        pending = detection;  // (replaced if the BBS repeats itself: see onDetect)
        showTransfer("The BBS is ready for your upload");
        $("xfer-choose").hidden = false;
        $("xfer-name").textContent = "Choose the files to send, or drop them here.";
        var started = false;
        $("xfer-cancel").onclick = function () {
            if (started) { try { zsession.abort(); } catch (e) { } } else if (pending) { pending.deny(); }
            dropTheRest();
            pending = null;
            endTransfer("Upload cancelled.");
        };
        var go = function (files) {
            if (started || !files || !files.length || !pending) return;
            started = true;
            $("xfer-choose").hidden = true;
            $("xfer-title").textContent = "Uploading";
            var session = pending.confirm();
            pending = null;
            sendFiles(zsession = session, Array.prototype.slice.call(files));
        };
        $("xfer-files").onchange = function () { go($("xfer-files").files); };
        $("xfer").ondragover = function (e) { e.preventDefault(); };
        $("xfer").ondrop = function (e) { e.preventDefault(); go(e.dataTransfer.files); };
    }

    function sendFiles(session, files) {
        var sent = [], skipped = [];
        var left = files.reduce(function (n, f) { return n + f.size; }, 0);
        var i = 0;

        function next() {
            if (i >= files.length) return session.close();
            var file = files[i];
            var offer = {
                name: file.name, size: file.size, mtime: new Date(file.lastModified),
                files_remaining: files.length - i, bytes_remaining: left
            };
            i++;
            left -= file.size;
            return session.send_offer(offer).then(function (xfer) {
                if (!xfer) { skipped.push(file.name); return next(); }
                return sendOne(xfer, file).then(function () { sent.push(file.name); return next(); });
            });
        }

        // The file in pieces, waiting while the socket has a backlog, so a big
        // file neither sits whole in memory nor floods the connection.
        function sendOne(xfer, file) {
            var offset = xfer.get_offset();
            progress(file.name, offset, file.size);
            return new Promise(function (resolve, reject) {
                function piece() {
                    if (zsession !== session) return reject(new Error("cancelled"));
                    if (ws && ws.bufferedAmount > HIGH_WATER) return setTimeout(piece, 20);
                    var end = Math.min(file.size, offset + UPLOAD_CHUNK);
                    file.slice(offset, end).arrayBuffer().then(function (buf) {
                        var bytes = new Uint8Array(buf);
                        offset = end;
                        progress(file.name, offset, file.size);
                        if (offset >= file.size) {
                            xfer.end(bytes).then(resolve, reject);
                        } else {
                            xfer.send(bytes);
                            piece();
                        }
                    }, reject);
                }
                piece();
            });
        }

        next().then(function () {
            var text = sent.length ? "Uploaded " + sent.join(", ") + "." : "Nothing was uploaded.";
            if (skipped.length) text += " The BBS did not take " + skipped.join(", ") + ".";
            endTransfer(text);
        }, function (err) {
            if (zsession === session) endTransfer("The upload failed: " + (err && err.message || err));
        });
    }

    // -- controls -------------------------------------------------------------

    function setUpControls() {
        var size = $("size"), sharp = $("sharp");
        size.value = settings.size;
        sharp.checked = settings.sharp;
        size.onchange = function () {
            settings.size = size.value;
            saveSettings();
            var wanted = chosenGrid();
            // The BBS knows the size it was told at login: a new one needs a new connection
            $("pending").hidden = !ws || (grid && wanted[0] === grid[0] && wanted[1] === grid[1]);
            if (!ws) connect();
            term.focus();
        };
        sharp.onchange = function () {
            settings.sharp = sharp.checked;
            saveSettings();
            fitFont();
            term.focus();
        };
        $("connect").onclick = connect;
        $("reconnect").onclick = connect;
        $("fullscreen").onclick = function () {
            if (document.fullscreenElement) document.exitFullscreen();
            else document.documentElement.requestFullscreen().catch(function () { });
            term.focus();
        };
    }

    function start() {
        makeTerminal();
        setUpControls();
        connect();
    }

    // The terminal measures its cells from the font: load it first.
    function whenFontReady(then) {
        if (!document.fonts || !document.fonts.load) return then();
        var done = false;
        var once = function () { if (!done) { done = true; then(); } };
        document.fonts.load("16px \"" + FONT + "\"").then(once, once);
        setTimeout(once, 3000);
    }

    if (typeof Terminal === "undefined" || typeof Zmodem === "undefined") {
        // The libraries did not load (a blocked CDN, say): say so rather than hang.
        document.addEventListener("DOMContentLoaded", function () {
            $("status").textContent = "The terminal could not load its scripts. Try bbs-local.html, or reload.";
        });
        return;
    }
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () { whenFontReady(start); });
    } else {
        whenFontReady(start);
    }
})();
