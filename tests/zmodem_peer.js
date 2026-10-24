// A ZMODEM peer for tests/test_zmodem_interop.py, using zmodem.js: the same
// file the web terminal loads (web/site/bbs-term/vendor/zmodem-0.1.10.js).
// The protocol travels on stdin/stdout; progress goes to stderr.
//
//   node zmodem_peer.js receive <directory>    take every file offered
//   node zmodem_peer.js send <file>...         offer these files (<file>::<name>
//                                              offers it under another name)
//   node zmodem_peer.js cancel-receive         start receiving, then cancel
//
// With "--ws <url>" first, it plays the web terminal page instead: it opens a
// WebSocket to the bridge (web/terminal_bridge.py), sends its size, and runs
// the protocol over binary messages, as web/site/bbs-term/bbs.js does.
"use strict";
const fs = require("fs");
const path = require("path");

// zmodem.js logs with console.*, which Node writes to stdout: the protocol's
// channel here. (In a browser it goes to the developer console.)
for (const level of ["log", "debug", "info", "warn", "error"]) {
    console[level] = (...a) => process.stderr.write(a.map(String).join(" ") + "\n");
}

global.window = global;
require(path.join(__dirname, "..", "web", "site", "bbs-term", "vendor", "zmodem-0.1.10.js"));
const Zmodem = global.Zmodem;

let argv = process.argv.slice(2);
let wsUrl = null;
if (argv[0] === "--ws") {
    wsUrl = argv[1];
    argv = argv.slice(2);
}
const [mode, ...args] = argv;
const say = (...a) => process.stderr.write(a.join(" ") + "\n");
let ws = null;

function finish(code) {
    if (ws) {
        ws.close();
        setTimeout(() => process.exit(code), 200);
        return;
    }
    // Let stdout drain before leaving
    process.stdout.write("", () => process.exit(code));
}

function output(octets) {
    if (ws) ws.send(new Uint8Array(octets));
    else process.stdout.write(Buffer.from(octets));
}

const sentry = new Zmodem.Sentry({
    to_terminal() {},
    sender: output,
    on_retract() { say("retracted"); },
    on_detect(detection) {
        const session = detection.confirm();
        session.on("session_end", () => { say("session_end"); finish(0); });
        if (session.type === "receive") {
            if (mode === "cancel-receive") {
                session.on("offer", () => { say("cancelling"); session.abort(); setTimeout(() => finish(0), 500); });
            } else {
                session.on("offer", (xfer) => {
                    const name = xfer.get_details().name;
                    xfer.accept().then((chunks) => {
                        const data = Buffer.concat(chunks.map((c) => Buffer.from(c)));
                        fs.writeFileSync(path.join(args[0], name), data);
                        say("received", name, data.length);
                    });
                });
            }
            session.start();
        } else {
            (async () => {
                const files = args.map((arg) => {
                    const [p, name] = arg.split("::");
                    return { name: name || path.basename(p), data: fs.readFileSync(p) };
                });
                let left = files.reduce((n, f) => n + f.data.length, 0);
                for (let i = 0; i < files.length; i++) {
                    const { name, data } = files[i];
                    const xfer = await session.send_offer({
                        name, size: data.length,
                        mtime: new Date(), files_remaining: files.length - i, bytes_remaining: left,
                    });
                    left -= data.length;
                    if (!xfer) { say("skipped", name); continue; }
                    // In pieces, as the browser sends a file it reads
                    for (let at = 0; at < data.length; at += 65536) {
                        xfer.send(new Uint8Array(data.subarray(at, Math.min(at + 65536, data.length))));
                    }
                    await xfer.end();
                    say("sent", name, data.length);
                }
                await session.close();
            })().catch((e) => { say("send failed:", e && (e.message || e)); finish(1); });
        }
    },
});

function input(bytes) {
    try {
        sentry.consume(bytes);
    } catch (e) {
        say("error:", e && (e.message || e));
        finish(2);
    }
}

if (wsUrl) {
    ws = new WebSocket(wsUrl, "dirtyfork-terminal");
    ws.binaryType = "arraybuffer";
    ws.onopen = () => ws.send(JSON.stringify({ cols: 80, rows: 25 }));
    ws.onmessage = (e) => { if (typeof e.data !== "string") input(new Uint8Array(e.data)); };
    ws.onclose = (e) => { say("closed", e.code, e.reason); process.exit(0); };
    ws.onerror = () => { say("websocket error"); process.exit(4); };
} else {
    process.stdin.on("data", input);
    process.stdin.on("end", () => finish(3));
}
