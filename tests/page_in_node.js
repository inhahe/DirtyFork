// Runs web/site/bbs-term/bbs.js as a page at the given address would (from
// the page's <head>, while the document loads), with stand-ins that accept
// anything for the page's elements, the browser, xterm.js and zmodem.js.
// Prints, as JSON, the WebSockets it opened, what its status line says, and
// which of the bar's controls it hid. (tests/test_web_site.py)
//
//   node page_in_node.js <bbs.js> <protocol> <host> [loaded|missing]
"use strict";
const vm = require("vm");
const fs = require("fs");

const [script, protocol, host, libraries = "loaded"] = process.argv.slice(2);

// An object that takes any property, call or construction, keeps what is
// set on it, and reads as 0 in arithmetic.
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

const elements = {}, sockets = [], onLoaded = [];
class WebSocket { constructor(url) { sockets.push(url); } }
WebSocket.OPEN = 1;
const document = {
    readyState: "loading",
    addEventListener(type, listener) { if (type === "DOMContentLoaded") onLoaded.push(listener); },
    getElementById(id) { return elements[id] || (elements[id] = anything()); },
};
const page = {
    location: { protocol, host }, document,
    window: anything(), navigator: anything(), getComputedStyle: anything(),
    localStorage: { getItem() { return null; }, setItem() {} },
    Terminal: anything(), WebglAddon: anything(), Zmodem: anything(), WebSocket,
    console, TextEncoder, setTimeout, clearTimeout,
};
if (libraries === "missing") delete page.Terminal;

vm.runInNewContext(fs.readFileSync(script, "utf8"), page);
document.readyState = "interactive";
onLoaded.forEach(listener => listener());

const controls = {
    size: () => document.getElementById("size").parentNode,
    sharp: () => document.getElementById("sharp").parentNode,
    fullscreen: () => document.getElementById("fullscreen"),
};
console.log(JSON.stringify({
    sockets,
    status: document.getElementById("status").textContent,
    hidden: Object.keys(controls).filter(name => controls[name]().hidden === true),
}));
