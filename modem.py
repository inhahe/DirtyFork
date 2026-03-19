"""
Modem/serial connection support via pyserial-asyncio.

Provides SerialReader and SerialWriter adapter classes that match the
telnetlib3 reader/writer interface, plus modem AT command handling
(wait for RING, answer with ATA, hang up with ATH).
"""

import asyncio
import serial_asyncio

from logger import log


class SerialWriter:
  """Adapter wrapping pyserial-asyncio StreamWriter to match telnetlib3 writer interface."""

  def __init__(self, transport, protocol, encoding="cp437"):
    self._transport = transport
    self._protocol = protocol
    self._encoding = encoding
    self._closed = False

  def write(self, data):
    if self._closed:
      return
    if isinstance(data, str):
      data = data.encode(self._encoding, errors="replace")
    self._transport.write(data)

  async def drain(self):
    # pyserial transport writes immediately; drain is a no-op but we yield
    await asyncio.sleep(0)

  def close(self):
    self._closed = True
    if self._transport and not self._transport.is_closing():
      self._transport.close()

  async def wait_closed(self):
    pass

  def get_extra_info(self, name, default=None):
    if name == "TERM":
      return "ansi-bbs"  # modem terminals are typically CP437/ANSI
    if name == "peername":
      return ("serial", 0)
    return default


class SerialReader:
  """Adapter wrapping pyserial-asyncio StreamReader to match telnetlib3 reader interface."""

  def __init__(self, stream_reader, encoding="cp437"):
    self._reader = stream_reader
    self._encoding = encoding

  async def read(self, n=1):
    try:
      data = await self._reader.read(n)
    except (asyncio.CancelledError, Exception):
      return ""
    if not data:
      return ""
    if isinstance(data, bytes):
      return data.decode(self._encoding, errors="replace")
    return data


async def _open_serial(port, baudrate):
  """Open a serial connection and return (SerialReader, SerialWriter)."""
  reader, writer = await serial_asyncio.open_serial_connection(
    url=port,
    baudrate=baudrate,
    bytesize=serial_asyncio.serial.EIGHTBITS,
    parity=serial_asyncio.serial.PARITY_NONE,
    stopbits=serial_asyncio.serial.STOPBITS_ONE,
    rtscts=True,
  )
  # Get transport from writer for our adapter
  transport = writer.transport
  protocol = writer.transport.get_protocol() if hasattr(writer.transport, 'get_protocol') else None
  return (
    SerialReader(reader),
    SerialWriter(transport, protocol),
    writer,  # keep reference to underlying writer for cleanup
  )


async def _send_at(raw_writer, cmd, encoding="cp437"):
  """Send an AT command and flush."""
  raw_writer.write((cmd + "\r").encode(encoding))
  await raw_writer.drain()


async def _read_line(raw_reader, timeout=5.0):
  """Read a line from the serial port with timeout. Returns stripped string or None."""
  buf = b""
  try:
    end = asyncio.get_event_loop().time() + timeout
    while True:
      remaining = end - asyncio.get_event_loop().time()
      if remaining <= 0:
        return None
      try:
        ch = await asyncio.wait_for(raw_reader.read(1), timeout=remaining)
      except asyncio.TimeoutError:
        return None
      if not ch:
        return None
      if isinstance(ch, str):
        ch = ch.encode("cp437", errors="replace")
      buf += ch
      if buf.endswith(b"\r\n") or buf.endswith(b"\n"):
        return buf.decode("cp437", errors="replace").strip()
  except Exception:
    return None


async def wait_for_call(port, baudrate, init_string="ATZ"):
  """Wait for an incoming call on a modem.
  Sends init string, waits for RING, answers with ATA.
  Returns (SerialReader, SerialWriter) on CONNECT, or None on failure."""

  log.info("Modem: opening %s at %d baud", port, baudrate)

  reader, writer = await serial_asyncio.open_serial_connection(
    url=port,
    baudrate=baudrate,
    bytesize=serial_asyncio.serial.EIGHTBITS,
    parity=serial_asyncio.serial.PARITY_NONE,
    stopbits=serial_asyncio.serial.STOPBITS_ONE,
    rtscts=True,
  )

  transport = writer.transport
  protocol = transport.get_protocol() if hasattr(transport, 'get_protocol') else None

  # Initialize modem
  log.info("Modem: sending init string: %s", init_string)
  await _send_at(writer, init_string)
  await asyncio.sleep(1)

  # Read any init response and discard
  try:
    while True:
      line = await _read_line(reader, timeout=0.5)
      if line is None:
        break
      log.debug("Modem init response: %s", line)
  except Exception:
    pass

  # Enable auto-answer off, we'll answer manually
  await _send_at(writer, "ATS0=0")
  await asyncio.sleep(0.5)
  # Drain response
  try:
    while True:
      line = await _read_line(reader, timeout=0.3)
      if line is None:
        break
  except Exception:
    pass

  log.info("Modem: waiting for RING on %s...", port)

  # Wait for RING
  while True:
    line = await _read_line(reader, timeout=60.0)
    if line is None:
      continue  # timeout, keep waiting
    log.debug("Modem: received: %s", line)
    if "RING" in line.upper():
      log.info("Modem: RING detected, answering...")
      await asyncio.sleep(0.5)
      await _send_at(writer, "ATA")

      # Wait for CONNECT
      while True:
        line = await _read_line(reader, timeout=30.0)
        if line is None:
          log.warning("Modem: timeout waiting for CONNECT after ATA")
          break
        log.debug("Modem: %s", line)
        upper = line.upper()
        if "CONNECT" in upper:
          log.info("Modem: %s", line)
          # Connected — return adapted reader/writer
          return (
            SerialReader(reader),
            SerialWriter(transport, protocol),
          )
        if "NO CARRIER" in upper or "ERROR" in upper or "NO ANSWER" in upper:
          log.warning("Modem: connection failed: %s", line)
          break
      # Failed to connect, keep waiting for next ring
      log.info("Modem: resuming wait for RING...")


async def hangup(serial_writer):
  """Send ATH to hang up the modem."""
  try:
    if hasattr(serial_writer, '_transport') and serial_writer._transport:
      await asyncio.sleep(1.1)
      serial_writer._transport.write(b"+++")
      await asyncio.sleep(1.1)
      serial_writer._transport.write(b"ATH\r")
      await asyncio.sleep(0.5)
      log.info("Modem: sent ATH (hangup)")
  except Exception as e:
    log.debug("Modem: hangup error: %s", e)
