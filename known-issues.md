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

- **Where:** `web/terminal_bridge.py` opens the telnet connection for each web caller, so the BBS's peer address (logs, and anything that ever uses it) is the bridge's.
- **What:** the caller's real address reaches only the bridge (nginx's `X-Real-IP`), which logs it in `web/terminal_bridge.log`.
- **Fix:** have the bridge announce the caller on the connection (a PROXY protocol v1 line, or a telnet NEW-ENVIRON variable such as `IPADDRESS`), and have `DirtyFork.py` accept it only from 127.0.0.1 and record it as the caller's address.

## Modem support is untested with real hardware

- **Where:** `modem.py`; `tests/test_modem.py`, `tests/fake_modem.py`.
- **What:** it is tested against a simulated Hayes modem on pyserial-asyncio's real transport (setting up, answering, hang-ups both ways, flow control at the line's speed, a failing port, a ZMODEM download), but never with a modem: how real modems word their results, how quickly they raise and drop DCD, and Windows' serial driver (rather than the simulation's) are untried. Those tests also run on Windows only: elsewhere pyserial-asyncio waits on the port's file descriptor, which the simulated port has not got.
- **Fix:** test with real hardware (two modems and a line simulator, or a line to call); for the tests elsewhere, give the simulated port a socket pair as its file descriptor.

## The screen size is read only at login

- **Where:** `common.setup_terminal` (`get_screen_size`), once per connection; telnet NAWS updates are ignored.
- **What:** a terminal resized during a session keeps the layout of its first size: growing leaves the new room unused, shrinking cuts the screen off. The web terminal therefore fixes its size for a connection (a new size needs a new one) and only scales its font with the window.
- **Fix:** take NAWS updates (telnetlib3's `on_naws`), resize `user.screen` and the tracking, and have the activity on screen redraw itself for the new size (its `redraw_hook`, which every activity would need; menus, forms, popups and the teleconference lay themselves out from `screen_width`/`screen_height` when drawn).

## YMODEM-G uploads are untested against a real sender

- **Where:** `file_transfer.receive_files_ymodem` (`lib/ymodem`'s receiver, which asks with G).
- **What:** it is tested against `lib/ymodem`'s own sender only: lrzsz's `sb` has no YMODEM-G (it never answers a G), and SyncTERM cannot be driven by a test. YMODEM-G downloads are tested against lrzsz's `rb` (as plain YMODEM). A sender that does not do G gets no answer it understands.
- **Fix:** try an upload from SyncTERM; have the receiver fall back to C (plain YMODEM) when a G goes unanswered.
