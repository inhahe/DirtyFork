"""A Hayes-compatible modem on a serial port, for tests/test_modem.py.

FakeModem stands in for pyserial's Serial as pyserial-asyncio's transport
uses it (read, write, in_waiting, out_waiting, flush, close) and as modem.py
does (dtr, cd), with the other end of the line for the test: ring(),
type() what the caller types, to_caller what reached the caller, and
hang_up() for the caller hanging up. plugged_in() installs it, for a port
name, where pyserial-asyncio opens ports.

Like a real modem it takes AT commands in command mode (echo until E0,
results in words, or digits until V1 if *numeric*), answers a call with ATA
(CONNECT, after a CARRIER message if given; carrier up), passes data online
at the line's speed (cps; None: at once; 0: held), hangs up when DTR drops
(unless follows_dtr is False) and goes back to command mode on the +++
escape between two silences of *guard* seconds. Switched off (*powered*
False) it takes nothing and says nothing. Its flush() waits, as
pyserial's does on Windows, without a time limit until all written has
gone.

pyserial-asyncio polls the port on Windows only: elsewhere it waits on a
file descriptor, which this has not got (test_modem skips there).
"""
import contextlib
import time
from unittest import mock

import serial
import serial_asyncio


class FakeModem:
    def __init__(self, *, connect="CONNECT 33600/ARQ", carrier=None, cps=None, answers=True,
                 results=True, numeric=False, dcd=True, follows_dtr=True, guard=1.0,
                 powered=True, hangup_delay=0.0, rejects=()):
        self.hangup_delay = hangup_delay  # seconds after DTR drops before it is on hook
        self.rejects = rejects      # settings it does not know: a command with one is ERROR
        self.failing_reads = False  # reads fail (the port is failing), in_waiting still works
        self.connect = connect      # what ATA says when it connects
        self.carrier_message = carrier  # what it says before that (CARRIER 2400), if anything
        self.cps = cps              # the line's speed, bytes a second (None: at once; 0: held)
        self.answers = answers      # ATA connects (else NO CARRIER)
        self.results = results      # it answers commands at all
        self.numeric = numeric      # results as digits (V0) until V1
        self.dcd = dcd              # DCD follows the carrier (&C1 and wired)
        self.follows_dtr = follows_dtr  # dropping DTR hangs up (&D2)
        self.guard = guard          # the +++ escape's guard time, seconds
        self.powered = powered      # off: takes nothing (CTS low), says nothing
        self.commands = []          # AT commands received
        self.to_caller = bytearray()  # what reached the caller
        self.dtr_drops = []         # len(unsent) each time DTR dropped
        self.opened = 0             # times opened
        self.open_options = None    # the options of the last opening
        self.broken = False
        self._reset_port()

    def _reset_port(self):
        self.rx = bytearray()       # from the modem to the computer
        self.unsent = bytearray()   # written, not across the line yet
        self.online = False
        self.ringing = False
        self.echo = True
        self.is_open = True
        self.timeout = self.write_timeout = None
        self._carrier = False
        self._dtr = True
        self._command = bytearray()
        self._escape_at = None
        self._last_write = 0.0
        self._sent_at = time.monotonic()
        self._on_hook_at = None  # (when a hang-up by DTR completes)

    # -- the caller's side ----------------------------------------------

    def ring(self, message="RING"):
        self.ringing = True
        self._result(message)

    def type(self, data):
        """The caller types *data* (only when connected)."""
        if self.online:
            self.rx += data

    def hang_up(self, quietly=False):
        """The caller hangs up: the carrier drops (and the modem says NO CARRIER)."""
        self._lose_carrier(quietly)

    def unplug(self):
        self.broken = True

    @property
    def carrier(self):
        return self._carrier

    # -- pyserial's Serial, as pyserial-asyncio and modem.py use it -------

    @property
    def in_waiting(self):
        self._check()
        return len(self.rx)

    def read(self, size=1):
        self._check()
        if self.failing_reads:
            raise serial.SerialException("ReadFile failed (the device is failing)")
        data = bytes(self.rx[:size])
        del self.rx[:size]
        return data

    def write(self, data):
        self._check()
        data = bytes(data)
        now = time.monotonic()
        if not self.powered:
            self.unsent += data  # (the port's driver holds it: CTS is low)
        elif self.online:
            self._online_write(data, now)
        else:
            self._command_bytes(data)
        self._last_write = now
        return len(data)

    @property
    def out_waiting(self):
        self._check()
        self._transmit()
        return len(self.unsent)

    def flush(self):
        """As pyserial's on Windows: waits, without a time limit, until all
        that was written has gone (for ever, if the line holds it)."""
        while self.out_waiting:
            time.sleep(0.05)

    def reset_output_buffer(self):
        self._check()
        self.unsent.clear()

    def close(self):
        self.is_open = False

    @property
    def dtr(self):
        return self._dtr

    @dtr.setter
    def dtr(self, value):
        if not self.is_open:
            raise serial.PortNotOpenError()
        if self._dtr and not value:
            self._transmit()
            self.dtr_drops.append(len(self.unsent))
            if self.online and self.follows_dtr and self.powered:
                self._on_hook_at = time.monotonic() + self.hangup_delay
                self._hook()
        self._dtr = value

    def _hook(self):
        """A hang-up by DTR completes once its delay has passed."""
        if self._on_hook_at is not None and time.monotonic() >= self._on_hook_at:
            self._on_hook_at = None
            self._lose_carrier(quietly=False)

    @property
    def cd(self):
        if self.broken:
            raise serial.SerialException("GetCommModemStatus failed (the device is gone)")
        if not self.is_open:
            raise serial.PortNotOpenError()
        self._hook()
        return self._carrier and self.dcd and self.powered

    # -- the modem ---------------------------------------------------------

    def _check(self):
        if self.broken:
            raise serial.SerialException("the device is not connected")
        if not self.is_open:
            raise serial.PortNotOpenError()

    _CODES = {"OK": "0", "CONNECT": "1", "RING": "2", "NO CARRIER": "3", "ERROR": "4"}

    def _result(self, text):
        if not (self.results and self.powered):
            return
        if self.numeric:  # (V0: the code, and a CR alone)
            code = next((c for word, c in self._CODES.items() if text.startswith(word)), "4")
            self.rx += code.encode("ascii") + b"\r"
        else:
            self.rx += b"\r\n" + text.encode("ascii") + b"\r\n"

    def _lose_carrier(self, quietly):
        self._transmit()
        self.unsent.clear()  # (what had not gone is lost)
        self.online = False
        self._carrier = False
        if not quietly:
            self._result("NO CARRIER")

    def _transmit(self):
        """Move across the line what its speed has let through since last time."""
        now = time.monotonic()
        if not self.unsent:
            self._sent_at = now  # (an idle line saves up no time)
            return
        if not self.powered:
            return
        if self.cps is None:
            n = len(self.unsent)
        else:
            n = min(len(self.unsent), int((now - self._sent_at) * self.cps))
        if n:
            self.to_caller += self.unsent[:n]
            del self.unsent[:n]
            self._sent_at = now if not self.unsent else self._sent_at + n / self.cps

    def _online_write(self, data, now):
        self._transmit()
        if self._escape_at is not None:
            if now - self._escape_at >= self.guard:  # (an escape: command mode, still connected)
                self._escape_at = None
                self.online = False
                self._result("OK")
                self._command_bytes(data)
                return
            self._escape_at = None
            self.unsent += b"+++"  # (it was data after all)
        quiet = now - self._last_write >= self.guard and not self.unsent
        if data == b"+++" and quiet:
            self._escape_at = now
        else:
            self.unsent += data
            self._transmit()

    def _command_bytes(self, data):
        for b in data:
            if self.echo:
                self.rx.append(b)
            if b == 0x0D:
                line = self._command.decode("ascii", "replace").strip()
                self._command.clear()
                if line.upper().startswith("AT"):
                    self._execute(line)
            elif b != 0x0A:
                self._command.append(b)

    def _execute(self, line):
        self.commands.append(line)
        body = line[2:].upper()
        if any(setting in body for setting in self.rejects):
            self._result("ERROR")  # (and, as many modems do, none of the line applied)
            return
        if body.startswith("Z"):
            self.echo = True
        if "E0" in body:
            self.echo = False
        if "V1" in body:
            self.numeric = False
        if body.startswith("A"):
            if self.ringing and self.answers:
                self.online = True
                self._carrier = True
                self._sent_at = time.monotonic()
                if self.carrier_message:
                    self._result(self.carrier_message)
                self._result(self.connect)
            else:
                self._result("NO CARRIER")
            self.ringing = False
            return
        if body.startswith("H"):
            self.online = False
            self._carrier = False
        self._result("OK")

    # -- opening -----------------------------------------------------------

    def _opened(self, options):
        if self.broken:
            raise serial.SerialException("could not open port: the device is not connected")
        self._reset_port()
        self.opened += 1
        self.open_options = options
        return self


@contextlib.contextmanager
def plugged_in(ports):
    """Open the FakeModems in *ports* (port name -> FakeModem) where
    pyserial-asyncio opens ports; other names fail as absent ports do."""
    def serial_for_url(url, *args, **options):
        if url not in ports:
            raise serial.SerialException(f"could not open port {url!r}: FileNotFoundError")
        return ports[url]._opened(options)
    with mock.patch.object(serial_asyncio.serial, "serial_for_url", serial_for_url):
        yield
