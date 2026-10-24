# Vendored libraries

The file-transfer protocol library `file_transfer.py` uses for YMODEM-G. It puts this directory on `sys.path`, so it imports as `ymodem`. It is not available as a working package on PyPI in the form used here.

ZMODEM is DirtyFork's own, `zmodem.py`. Until 2026-10 it came from Wijnand Modderman-Lenstra's `modem` package (vendored here as `lib/modem`), whose ZMODEM could only receive, and failed under Python 3 on the first data packet; it was removed then. Being a package named `modem`, it also hid DirtyFork's own `modem.py` from imports made after `file_transfer` had put this directory first on `sys.path`.

## ymodem: YMODEM-G

- **What:** Alex Woo's `ymodem`, https://github.com/alexwoo1900/ymodem, master at `1d9611b` (2024-07-19, version 1.5). PyPI's `ymodem` 1.5.3 is a different version of the code.
- **License:** MIT, `ymodem/LICENSE` (upstream's own file).
- **Needs:** `ordered-set` (listed in the project's `requirements.txt`).
- **Used by DirtyFork:** `ymodem.Socket.ModemSocket` and `ymodem.Protocol.ProtocolType`.
- **Changed here** (marked "DirtyFork" in `ymodem/Socket.py`): the receiver keeps only the last component of the file name the sender gives, and refuses `.` and `..`. Upstream joins the sender's name to the save folder as it is, so a name such as `..\..\DirtyFork.yaml`, or an absolute path, was written outside it. A name that is not UTF-8 is read as CP437 instead of stopping the transfer.
