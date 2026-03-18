"""
Test door game for DirtyFork BBS.
Displays command-line args, finds and shows dropfiles, then does simple I/O.

Usage:
  python testdoor.py --mode stdio [--dropdir PATH] [--node N] [extra args...]
  python testdoor.py --mode socket --port PORT [--dropdir PATH] [--node N] [extra args...]

Modes:
  stdio   - communicate via stdin/stdout (for STDIO communication_type)
  socket  - connect to localhost:PORT (for SOCKET/DOOR32 communication_type)
"""

import sys
import os
import socket
import time
import argparse

DROPFILE_NAMES = [
    "DOOR.SYS", "DOOR32.SYS", "CALLINFO.BBS", "DORINFO1.DEF",
    "CHAIN.TXT", "EXITINFO.BBS", "SFDOORS.DAT",
]

CR = "\r"
LF = "\n"
CRLF = CR + LF


def find_dropfiles(dropdir):
    """Find all recognized dropfiles in the given directory."""
    found = {}
    if not dropdir or not os.path.isdir(dropdir):
        return found
    for name in DROPFILE_NAMES:
        path = os.path.join(dropdir, name)
        if os.path.exists(path):
            try:
                with open(path, "r", errors="replace") as f:
                    found[name] = f.read()
            except Exception as e:
                found[name] = f"<error reading: {e}>"
    return found


def parse_door_sys(content):
    """Parse key fields from DOOR.SYS."""
    lines = content.split("\n")
    fields = {}
    mapping = {
        0: "COM port",
        1: "Baud rate",
        2: "Parity",
        3: "Node number",
        4: "DTE rate",
        5: "Screen display",
        6: "Printer toggle",
        7: "Page bell",
        8: "Caller alarm",
        9: "User full name",
        10: "Location",
        17: "Security level",
        18: "Time remaining (min)",
        19: "ANSI detected",
        24: "Alias/handle",
    }
    for i, label in mapping.items():
        if i < len(lines):
            fields[label] = lines[i].strip()
    return fields


def parse_door32_sys(content):
    """Parse key fields from DOOR32.SYS."""
    lines = content.split("\n")
    fields = {}
    mapping = {
        0: "Comm type (0=local,1=serial,2=telnet,3=socket)",
        1: "Comm handle/socket",
        2: "Baud rate",
        3: "BBS name",
        4: "User ID",
        5: "User full name",
        6: "User handle",
        7: "Security level",
        8: "Time remaining (sec)",
        9: "Emulation (0=Ascii,1=ANSI,2=Avatar,3=RIP,4=Max)",
        10: "Node number",
    }
    for i, label in mapping.items():
        if i < len(lines):
            fields[label] = lines[i].strip()
    return fields


class StdioIO:
    """I/O over stdin/stdout."""
    def send(self, text):
        sys.stdout.write(text)
        sys.stdout.flush()

    def recv(self, timeout=30):
        import select
        if sys.platform == "win32":
            import msvcrt
            end = time.time() + timeout
            buf = ""
            while time.time() < end:
                if msvcrt.kbhit():
                    ch = msvcrt.getwch()
                    return ch
                time.sleep(0.05)
            return None
        else:
            r, _, _ = select.select([sys.stdin], [], [], timeout)
            if r:
                return sys.stdin.read(1)
            return None

    def close(self):
        pass


class SocketIO:
    """I/O over TCP socket."""
    def __init__(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("127.0.0.1", port))
        self.sock.settimeout(30)

    def send(self, text):
        self.sock.sendall(text.encode("cp437", errors="replace"))

    def recv(self, timeout=30):
        self.sock.settimeout(timeout)
        try:
            data = self.sock.recv(1)
            if data:
                return data.decode("cp437", errors="replace")
            return None
        except socket.timeout:
            return None

    def close(self):
        self.sock.close()


def run(io, args, dropdir):
    """Main test door logic."""
    def out(text):
        io.send(text + CRLF)

    def separator():
        out("=" * 60)

    # Header
    separator()
    out("  DirtyFork Test Door v1.0")
    separator()
    out("")

    # Show command line
    out("COMMAND LINE ARGUMENTS:")
    out(f"  sys.argv = {sys.argv}")
    out(f"  mode = {args.mode}")
    if args.port:
        out(f"  port = {args.port}")
    if args.node:
        out(f"  node = {args.node}")
    if args.dropdir:
        out(f"  dropdir = {args.dropdir}")
    out("")

    # Show environment variables of interest
    out("ENVIRONMENT VARIABLES:")
    for var in ["TWNODE", "COMSPEC", "PATH"]:
        val = os.environ.get(var)
        if val:
            out(f"  {var} = {val}")
    out("")

    # Find and display dropfiles
    out(f"DROPFILE DIRECTORY: {dropdir or '(not specified)'}")
    dropfiles = find_dropfiles(dropdir)
    if not dropfiles:
        out("  No dropfiles found.")
    else:
        for name, content in dropfiles.items():
            separator()
            out(f"DROPFILE: {name}")
            separator()

            # Parse known formats
            if name == "DOOR.SYS":
                fields = parse_door_sys(content)
                for label, value in fields.items():
                    out(f"  {label}: {value}")
            elif name == "DOOR32.SYS":
                fields = parse_door32_sys(content)
                for label, value in fields.items():
                    out(f"  {label}: {value}")
            else:
                # Show raw content (first 20 lines)
                lines = content.split("\n")[:20]
                for line in lines:
                    out(f"  {line.rstrip()}")
                if len(content.split("\n")) > 20:
                    out(f"  ... ({len(content.split(chr(10)))} lines total)")
            out("")

    # Show communication info
    separator()
    out(f"COMMUNICATION MODE: {args.mode.upper()}")
    if args.mode == "socket":
        out(f"  Connected to 127.0.0.1:{args.port}")
    elif args.mode == "stdio":
        out(f"  Using stdin/stdout")
    separator()
    out("")

    # Interactive echo loop
    out("INTERACTIVE TEST - Type text and press Enter (Q to quit):")
    out("")

    buf = ""
    while True:
        io.send("> ")
        buf = ""
        while True:
            ch = io.recv(timeout=120)
            if ch is None:
                out("")
                out("Timeout - exiting.")
                return
            if ch in ("\r", "\n"):
                io.send(CRLF)
                break
            if ch == "\x08" or ch == "\x7f":
                if buf:
                    buf = buf[:-1]
                    io.send("\x08 \x08")
                continue
            buf += ch
            io.send(ch)

        line = buf.strip()
        if line.lower() == "q":
            out("Goodbye from Test Door!")
            return
        elif line.lower() == "help":
            out("Commands: Q=quit, HELP=this, INFO=show dropfile info again")
        elif line.lower() == "info":
            for name, content in dropfiles.items():
                out(f"--- {name} ---")
                for raw_line in content.split("\n")[:10]:
                    out(f"  {raw_line.rstrip()}")
        else:
            out(f"Echo: {line}")
            out(f"  Length: {len(line)} chars")
            out(f"  Hex: {' '.join(f'{ord(c):02x}' for c in line[:40])}")


def main():
    parser = argparse.ArgumentParser(description="DirtyFork Test Door")
    parser.add_argument("--mode", choices=["stdio", "socket"], default="stdio",
                        help="Communication mode")
    parser.add_argument("--port", type=int, default=None,
                        help="TCP port for socket mode")
    parser.add_argument("--node", type=str, default=None,
                        help="Node number")
    parser.add_argument("--dropdir", type=str, default=None,
                        help="Directory containing dropfiles")
    args, extra = parser.parse_known_args()

    # If dropdir not specified, try current directory
    dropdir = args.dropdir or os.getcwd()

    io = None
    try:
        if args.mode == "socket":
            if not args.port:
                print("Error: --port required for socket mode", file=sys.stderr)
                sys.exit(1)
            io = SocketIO(args.port)
        else:
            io = StdioIO()

        run(io, args, dropdir)
    except (BrokenPipeError, ConnectionResetError, ConnectionRefusedError) as e:
        print(f"Connection error: {e}", file=sys.stderr)
    except KeyboardInterrupt:
        pass
    finally:
        if io:
            io.close()


if __name__ == "__main__":
    main()
