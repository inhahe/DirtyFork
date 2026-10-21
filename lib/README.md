# Vendored libraries

The file-transfer protocol libraries `file_transfer.py` uses. It puts this directory on `sys.path`, so they import as `modem` and `ymodem`. Neither is available as a working package on PyPI in the form used here. Both are unmodified copies, under the MIT license (see the `LICENSE` in each).

## modem: ZMODEM

- **What:** Wijnand Modderman-Lenstra's `modem` package (XMODEM, YMODEM and ZMODEM; `__version__` 0.2.4, `setup.py` version 1.0), from the `multi-protocol` branch of https://github.com/tehmaze/modem.
- **Python 3 port:** by Enix Yu. The port itself is commit `2e2e46d`, "apply PEP8; port to python3", and this copy is the state at `c20ea54`, both from 2018-11-07. Upstream never merged it. It survives in the branches of two open pull requests that build on it: #2 (devotip, "Py3.7 multi protocol") and #13 (heimir-sverrisson, "Fix ymodem issues").
- **License:** the package declares MIT (`__license__` in `modem/__init__.py`, `license` in its `setup.py`) but ships no license text. `modem/LICENSE` is the standard MIT text with the package's own copyright notices.
- **Used by DirtyFork:** `modem.protocol.zmodem.ZMODEM` only.
- **Not included:** the later commits on those pull requests (2019 to 2022), which change only XMODEM, YMODEM and `Modem.calc_checksum` in `base.py`. That function still calls `ord()` on bytes, which fails under Python 3; ZMODEM never calls it.

## ymodem: YMODEM-G

- **What:** Alex Woo's `ymodem`, https://github.com/alexwoo1900/ymodem, master at `1d9611b` (2024-07-19, version 1.5). PyPI's `ymodem` 1.5.3 is a different version of the code.
- **License:** MIT, `ymodem/LICENSE` (upstream's own file).
- **Needs:** `ordered-set` (listed in the project's `requirements.txt`).
- **Used by DirtyFork:** `ymodem.Socket.ModemSocket` and `ymodem.Protocol.ProtocolType`.
