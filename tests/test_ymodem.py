"""file_transfer's YMODEM-G (lib/ymodem, patched) against small fake peers
written here, over an in-memory link: what a sender's or receiver's cancel
does, names Windows takes for devices, a plain YMODEM receiver that
refuses a packet once and asks late for the end of the batch, and a
connection that closes."""
import asyncio
import binascii
import os
import shutil
import tempfile
import threading
import time
import unittest

import _setup  # noqa: F401
import file_transfer
from definitions import success
from test_zmodem import End, Pipe

SOH, STX, EOT, ACK, NAK, CAN, C, G = 0x01, 0x02, 0x04, 0x06, 0x15, 0x18, 0x43, 0x67


def block(seq, data, crc=True):
    """A 1 KiB YMODEM block (data padded with NULs for block 0, else ^Z)."""
    pad = b"\0" if seq == 0 else b"\x1a"
    data = data.ljust(1024, pad)[:1024]
    check = binascii.crc_hqx(data, 0).to_bytes(2, "big") if crc else bytes([sum(data) & 0xFF])
    return bytes([STX, seq & 0xFF, 0xFF - (seq & 0xFF)]) + data + check


class Peer:
    """The fake side: reads what file_transfer sends, writes back."""

    def __init__(self, end):
        self.end = end
        self.buf = bytearray()

    async def take(self, n, timeout=10):
        while len(self.buf) < n:
            self.buf += await asyncio.wait_for(self.end.read(), timeout)
        data = bytes(self.buf[:n])
        del self.buf[:n]
        return data

    async def until(self, byte, timeout=15):
        """Skip to (and past) *byte*."""
        while True:
            if byte in self.buf:
                del self.buf[:self.buf.index(byte) + 1]
                return
            self.buf += await asyncio.wait_for(self.end.read(), timeout)

    async def quiet(self, seconds):
        """True if nothing arrives for *seconds*."""
        if self.buf:
            return False
        try:
            self.buf += await asyncio.wait_for(self.end.read(), seconds)
        except asyncio.TimeoutError:
            return True
        return False

    def send(self, data):
        self.end.write(data)


class Ymodem(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ymodem-test-")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_with(self, job, peer):
        """Run file_transfer's *job(link)* against *peer(Peer)*; return the job's result."""
        async def go():
            a, b = Pipe(), Pipe()
            ours, theirs = End(a, b), End(b, a)

            async def direct(user, text, work):
                return await work(ours)
            original = file_transfer._with_screen
            file_transfer._with_screen = direct
            try:
                result, _ = await asyncio.wait_for(asyncio.gather(job(), peer(Peer(theirs))), 60)
                return result
            finally:
                file_transfer._with_screen = original
        return asyncio.run(go())

    def test_a_sender_cancelling_midway_publishes_nothing(self):
        policy = file_transfer.UploadPolicy(directory=self.dir, keep_free=0)

        async def sender(p):
            await p.until(bytes([G]))
            p.send(block(0, b"half.bin\x003000 0 0"))
            await p.until(bytes([G]))
            p.send(block(1, b"x" * 1024))
            p.send(bytes([CAN, CAN]))
        result = self.run_with(lambda: file_transfer.receive_files_ymodem(object(), policy), sender)
        self.assertNotEqual(result.status, success)
        self.assertEqual(policy.saved, [])
        self.assertEqual(os.listdir(self.dir), [])  # (the staging folder is gone too)

    def test_a_device_name_is_stored_as_a_file(self):
        policy = file_transfer.UploadPolicy(directory=self.dir, keep_free=0)

        async def sender(p):
            await p.until(bytes([G]))
            p.send(block(0, b"NUL\x0010 0 0"))
            await p.until(bytes([G]))
            p.send(block(1, b"0123456789"))
            p.send(bytes([EOT]))
            await p.until(bytes([G]))
            p.send(block(0, b""))  # end of the batch
        result = self.run_with(lambda: file_transfer.receive_files_ymodem(object(), policy), sender)
        self.assertEqual(result.status, success, result.message)
        self.assertEqual(policy.saved, ["_NUL"])
        with open(os.path.join(self.dir, "_NUL"), "rb") as f:
            self.assertEqual(f.read(), b"0123456789")

    def test_two_files_of_one_name_in_a_batch_keep_the_first(self):
        """The library saves each file under a number, so the second no longer
        overwrites the first; the policy refuses the second, saying why. A
        path name loses its folders."""
        policy = file_transfer.UploadPolicy(directory=self.dir, keep_free=0)

        async def sender(p):
            for i, (name, body) in enumerate(((b"docs/readme.txt", b"first"),
                                              (b"..\\src\\readme.txt", b"second"))):
                await p.until(bytes([G]))
                p.send(block(0, name + b"\x00" + str(len(body)).encode() + b" 0 0"))
                await p.until(bytes([G]))
                p.send(block(1, body))
                p.send(bytes([EOT]))
            await p.until(bytes([G]))
            p.send(block(0, b""))
        result = self.run_with(lambda: file_transfer.receive_files_ymodem(object(), policy), sender)
        self.assertEqual(result.status, success, result.message)
        self.assertEqual(policy.saved, ["readme.txt"])
        self.assertEqual([name for name, _ in policy.refused], ["..\\src\\readme.txt"])
        with open(os.path.join(self.dir, "readme.txt"), "rb") as f:
            self.assertEqual(f.read(), b"first")

    def test_a_receiver_cancelling_is_not_a_success(self):
        path = os.path.join(self.dir, "out.bin")
        with open(path, "wb") as f:
            f.write(b"y" * 3000)

        async def receiver(p):
            p.send(bytes([C]))
            await p.take(1029)          # the file name packet
            p.send(bytes([ACK, CAN, CAN]))
        result = self.run_with(lambda: file_transfer.send_files_ymodem(object(), [path]), receiver)
        self.assertNotEqual(result.status, success)

    def test_a_plain_ymodem_receiver_is_waited_for(self):
        """It refuses the name packet once (it must come again, not be taken
        as refused data), acknowledges each packet, and asks for the end of
        the batch only after a pause (it must not arrive before)."""
        data = bytes(range(256)) * 10
        path = os.path.join(self.dir, "plain.bin")
        with open(path, "wb") as f:
            f.write(data)
        got = bytearray()

        async def receiver(p):
            p.send(bytes([C]))
            first = await p.take(1029)
            p.send(bytes([NAK]))
            again = await p.take(1029)
            self.assertEqual(first, again)
            self.assertTrue(again.startswith(bytes([STX, 0, 0xFF]) + b"plain.bin\x00"))
            p.send(bytes([ACK, C]))
            while True:
                head = await p.take(1)
                if head[0] == EOT:
                    p.send(bytes([ACK]))
                    break
                rest = await p.take(1028)
                self.assertEqual(binascii.crc_hqx(rest[2:1026], 0), int.from_bytes(rest[1026:], "big"))
                got.extend(rest[2:1026])
                p.send(bytes([ACK]))
            self.assertTrue(await p.quiet(0.5))  # nothing until asked
            p.send(bytes([C]))
            end = await p.take(1029)
            self.assertEqual(end[:4], bytes([STX, 0, 0xFF, 0]))
            p.send(bytes([ACK]))
        result = self.run_with(lambda: file_transfer.send_files_ymodem(object(), [path]), receiver)
        self.assertEqual(result.status, success, result.message)
        self.assertEqual(bytes(got[:len(data)]), data)


class ClosedLink(unittest.TestCase):
    def test_reads_stop_once_the_connection_has_closed(self):
        """Not None, which lib/ymodem would poll at full speed until its
        timeouts end: the read stops the library."""
        async def go():
            pipe = Pipe()
            link = file_transfer._ThreadedLink(End(pipe, Pipe()), asyncio.get_running_loop(),
                                               watch_cancel=False)
            await link.start()
            pipe.close()  # (the caller hangs up)
            await asyncio.sleep(0.1)
            outcome = {}

            def reader():
                started = time.monotonic()
                try:
                    link.read(1, timeout=5)
                    outcome["result"] = "returned"
                except file_transfer._Cancelled:
                    outcome["result"] = "cancelled"
                outcome["seconds"] = time.monotonic() - started
            thread = threading.Thread(target=reader)
            thread.start()
            await asyncio.to_thread(thread.join, 10)
            await link.stop()
            return outcome
        outcome = asyncio.run(go())
        self.assertEqual(outcome["result"], "cancelled")
        self.assertLess(outcome["seconds"], 1)


if __name__ == "__main__":
    unittest.main()
