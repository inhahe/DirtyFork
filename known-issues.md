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

## Modem support is untested

- **Where:** `modem.py`, `DirtyFork.py` (`modem_listener`).
- **What:** written against the AT command set but never run with a modem.
- **Fix:** test with real hardware, or a null-modem pair and a terminal program that emulates one.

## `lib/modem` carries a Python 3 bug outside ZMODEM

- **Where:** `lib/modem/base.py`, `Modem.calc_checksum` (vendored; see `lib/README.md`).
- **What:** it calls `ord()` on the items of a bytes object, which fails under Python 3. Its XMODEM and YMODEM classes use it; ZMODEM, the only part DirtyFork uses, doesn't.
- **Fix:** take the later upstream fixes listed in `lib/README.md` if XMODEM or YMODEM from that package is ever used.
