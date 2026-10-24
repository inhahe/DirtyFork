# Vendored libraries

The file-transfer protocol library `file_transfer.py` uses for YMODEM-G. It puts this directory on `sys.path`, so it imports as `ymodem`. It is not available as a working package on PyPI in the form used here.

ZMODEM is DirtyFork's own, `zmodem.py`. Until 2026-10 it came from Wijnand Modderman-Lenstra's `modem` package (vendored here as `lib/modem`), whose ZMODEM could only receive, and failed under Python 3 on the first data packet; it was removed then. Being a package named `modem`, it also hid DirtyFork's own `modem.py` from imports made after `file_transfer` had put this directory first on `sys.path`.

## ymodem: YMODEM-G

- **What:** Alex Woo's `ymodem`, https://github.com/alexwoo1900/ymodem, master at `1d9611b` (2024-07-19, version 1.5). PyPI's `ymodem` 1.5.3 is a different version of the code.
- **License:** MIT, `ymodem/LICENSE` (upstream's own file).
- **Needs:** `ordered-set` (listed in the project's `requirements.txt`).
- **Used by DirtyFork:** `ymodem.Socket.ModemSocket` and `ymodem.Protocol.ProtocolType`.
- **Changed here** (each marked "DirtyFork" in `ymodem/Socket.py`):
  - The receiver saves each file as `file<number>` in the folder it is given, and records the name the sender gave it in `received_names`; `file_transfer` publishes it under that name only as its upload policy allows. Upstream joined the sender's name to the folder as it was, so `..\..\DirtyFork.yaml` or an absolute path was written outside it, `PRN` or `COM1` opened the device (Windows does so in any folder), and two files of one name in a batch overwrote each other. A name that is not UTF-8 is read as CP437 instead of stopping the transfer.
  - A cancel (CAN) and the sender's timeout waiting to start return False, not True, both ways: upstream reported a cancelled transfer as a success, so a half-received file looked whole.
  - The sender streams (YMODEM-G) only when the receiver asked with G: upstream streamed whenever it was set up for G, file name packet included, so a receiver that asked with C (plain YMODEM) lost sync, and a NAK of the name packet was taken as the go-ahead in checksum mode.
  - Before the end-of-batch packet the sender waits for the receiver to ask (C or G), and for a plain YMODEM receiver's ACK after it: one that clears its input before asking lost it.
