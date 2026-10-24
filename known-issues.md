# Known issues and technical debt

Unsolved bugs and debt that couldn't be fixed when found. Fix and remove entries as they are dealt with.

## Trade Wars 2002 doesn't notice the caller hanging up

- **Where:** the door itself (`doors/tw2002`); `door.py` stop logic.
- **What:** when a caller hangs up or aborts with Ctrl+X, the connection to DOSBox-X closes and most doors see the carrier drop and exit. TW2002 doesn't, so it is terminated once the 10 s `HANGUP_EXIT_GRACE` runs out.
- **Fix:** none on the BBS side so far. Check TW2002's own carrier and timeout settings, or give the door a longer grace.

## Stars freeze while a door's launch popup is up

- **Where:** `door.run()` sets `user.in_door` before showing the "Launching …" popup; `stars._showing()` stops drawing whenever `in_door` is set.
- **What:** stars already on screen stop twinkling (and stay) for as long as the launch popup waits for a key, until the door's clear screen removes them.
- **Fix:** set `in_door` after the launch popup, checking that popups and pages during that popup still behave.

## Two copies of the line-feed and scroll-region logic

- **Where:** `input_output._line_feed` (the BBS's own output) and `ansi_emulator`'s `_line_feed`/`_index` (a door's output), each with its own region state: `user.scroll_region_*` and the emulator's `scroll_top`/`scroll_bottom`.
- **What:** the emulator now copies the door's region into `user.scroll_region_*`, so the BBS's tracking follows it, but the two implementations can still drift apart. The emulator also models origin mode, which the BBS tracking doesn't.
- **Fix:** let the emulator keep its region in `user.scroll_region_*` and share one line-feed routine; door.py's `screen_rows` region (`emulator.scroll_bottom = ...`) would then go through `ansi_set_region` alone.

## Web callers all appear to come from 127.0.0.1

- **Where:** `web/jsterm_bridge.py` opens the telnet connection for each web caller, so the BBS's peer address (logs, and anything that ever uses it) is the bridge's.
- **What:** the caller's real address reaches only the bridge (nginx's `X-Real-IP`), which logs it in `web/jsterm_bridge.log`.
- **Fix:** have the bridge announce the caller on the connection (a PROXY protocol v1 line, or a telnet NEW-ENVIRON variable such as `IPADDRESS`), and have `DirtyFork.py` accept it only from 127.0.0.1 and record it as the caller's address.

## ZMODEM downloads always fail

- **Where:** `file_transfer.send_file_zmodem` calls `modem.send(f)` on `lib/modem`'s `ZMODEM`, which (like its base `Modem`) has no `send`: the vendored ZMODEM only receives.
- **What:** every ZMODEM download ends in an `AttributeError` (logged as "ZMODEM send error") and the caller sees "Transfer failed." YMODEM-G downloads are unaffected. Found by the code review of the web terminal (2026-10-23), confirmed in the code, not yet reproduced with a client.
- **Fix:** a ZMODEM sender: from a later revision of the library if one has it (see `lib/README.md`), or another implementation (an `sz` subprocess bridged like a door, or a Python one).

## ZMODEM uploads die on a 60-second pause

- **Where:** `file_transfer._make_getc` returns `None` on a timeout; `lib/modem`'s receive loop (`_recv_raw`) expects `''` or `const.TIMEOUT`, and `lib/modem/const.py` defines `TIMEOUT` twice (`None`, then `-1`, which wins).
- **What:** when no byte arrives within the timeout, the receiver calls `ord(None)` and the upload ends with a `TypeError` instead of retrying. Found by the same review, confirmed in the code.
- **Fix:** have `getc` return what the library expects on a timeout (or fix the duplicate constant in the vendored copy and note it in `lib/README.md`).

## No five-Ctrl+X abort during transfers

- **Where:** `file_transfer.py` defines `CAN_BYTE`, `CAN_CHAR` and `CAN_COUNT_THRESHOLD` (five CANs = the user aborts) and never uses them.
- **What:** a caller cannot abort a stuck transfer the standard way; it ends only when the protocol gives up.
- **Fix:** watch the input during a transfer for five consecutive CAN bytes and cancel the transfer task; or remove the constants if the library's own handling is relied on.

## Modem support is untested

- **Where:** `modem.py`, `DirtyFork.py` (`modem_listener`).
- **What:** written against the AT command set but never run with a modem.
- **Fix:** test with real hardware, or a null-modem pair and a terminal program that emulates one.

## `lib/modem` carries a Python 3 bug outside ZMODEM

- **Where:** `lib/modem/base.py`, `Modem.calc_checksum` (vendored; see `lib/README.md`).
- **What:** it calls `ord()` on the items of a bytes object, which fails under Python 3. Its XMODEM and YMODEM classes use it; ZMODEM, the only part DirtyFork uses, doesn't.
- **Fix:** take the later upstream fixes listed in `lib/README.md` if XMODEM or YMODEM from that package is ever used.
