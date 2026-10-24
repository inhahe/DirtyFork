"""File transfers as a web caller makes them, end to end but for the browser:

    zmodem.js (Node, playing bbs.js)  <-WebSocket->  web/terminal_bridge.py
        <-telnet->  telnetlib3 (as DirtyFork runs it)  ->  file_transfer.py  ->  zmodem.py

Skipped without Node on PATH.
"""
import asyncio
import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

import _setup
import common
import file_transfer
import telnetlib3
from definitions import success
from idle import IdleMonitor

sys.path.insert(0, os.path.join(_setup.PROJECT, "web"))
import terminal_bridge as tb  # noqa: E402

PEER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zmodem_peer.js")
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "node is not on PATH")
class WebTransfers(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.src = tempfile.mkdtemp(prefix="web-src-")
        self.dst = tempfile.mkdtemp(prefix="web-dst-")
        self.rng = random.Random(7)
        self.job = None           # what the BBS does with the caller: async (user) -> result
        self.encoding = None      # the caller's encoding to switch to first (None: detected)
        self.done = asyncio.get_running_loop().create_future()
        self.bbs = await telnetlib3.create_server(
            host="127.0.0.1", port=0, shell=self.shell, encoding="cp437",
            encoding_errors="surrogateescape", timeout=0)  # (as DirtyFork.py starts it)
        self.bridge = tb.Bridge(("127.0.0.1", self.bbs.sockets[0].getsockname()[1]), 10, 10)
        self.ws = await tb.serve_bridge(self.bridge, "127.0.0.1", 0)
        self.url = f"ws://127.0.0.1:{self.ws.sockets[0].getsockname()[1]}/"

    async def asyncTearDown(self):
        self.ws.close()
        await self.ws.wait_closed()
        self.bbs.close()
        await self.bbs.wait_closed()
        shutil.rmtree(self.src, ignore_errors=True)
        shutil.rmtree(self.dst, ignore_errors=True)

    async def shell(self, reader, writer):
        """The BBS's side: a user on this connection, set up as setup_terminal
        does, then the test's job."""
        try:
            user = common.User(reader, writer)
            user.reader = IdleMonitor(reader, user)  # (as DirtyFork.user_loop wraps it)
            await common.detect_terminal(user)
            if self.encoding:
                user.encoding = self.encoding
                common._set_connection_encoding(user)
            from definitions import Char
            user.screen_height, user.screen_width = 25, 80
            user.screen = [[Char() for _ in range(80)] for _ in range(25)]
            result = await self.job(user)
            self.done.set_result((user, result))
        except BaseException as exc:
            if not self.done.done():
                self.done.set_exception(exc)
        finally:
            writer.close()

    async def caller(self, *args):
        """Run the Node peer against the bridge; wait for the BBS's job too.
        Returns (user, the job's result, the peer's stderr)."""
        proc = await asyncio.create_subprocess_exec(
            NODE, PEER, "--ws", self.url, *args, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        err = asyncio.ensure_future(proc.stderr.read())
        try:
            user, result = await asyncio.wait_for(self.done, 90)
            await asyncio.wait_for(proc.wait(), 20)
        finally:
            if proc.returncode is None:
                proc.kill()
                await proc.wait()
        return user, result, (await err).decode("utf-8", "replace")

    def make(self, name, size):
        data = (bytes(range(256)) + b"\xff" * 300 + self.rng.randbytes(size))[:size]
        path = os.path.join(self.src, name)
        with open(path, "wb") as f:
            f.write(data)
        return path, data

    def assert_back_to_normal(self, user, encoding):
        self.assertEqual(user.encoding, encoding)
        self.assertFalse(user.in_transfer)
        self.assertEqual(user.writer.fn_encoding(outgoing=True), encoding)

    async def download(self, encoding):
        self.encoding = encoding
        files = [self.make("all-bytes.bin", 70000), self.make("empty.bin", 0)]
        self.job = lambda user: file_transfer.send_files_zmodem(user, [p for p, _ in files])
        user, result, err = await self.caller("receive", self.dst)
        self.assertEqual(result.status, success, (result.message, err))
        for path, data in files:
            with open(os.path.join(self.dst, os.path.basename(path)), "rb") as f:
                self.assertEqual(f.read(), data)
        self.assert_back_to_normal(user, encoding or "utf-8")

    async def test_download_in_utf8(self):
        await self.download(None)  # the web terminal's own: XTERMJS reads as UTF-8

    async def test_download_with_the_caller_in_cp437(self):
        await self.download("cp437")

    async def test_upload_publishes_whole_files_under_safe_names_only(self):
        good, good_data = self.make("good.bin", 50000)
        weird, weird_data = self.make("weird.bin", 300)
        with open(os.path.join(self.dst, "taken.txt"), "wb") as f:
            f.write(b"already here")
        policy = file_transfer.UploadPolicy(directory=self.dst, reserved=frozenset({"meta.yaml"}),
                                            max_bytes=10**6, keep_free=0)
        self.job = lambda user: file_transfer.receive_files_zmodem(user, policy)
        user, result, err = await self.caller(
            "send", good, f"{weird}::..\\..\\evil:stream.bin", f"{weird}::meta.yaml",
            f"{weird}::taken.txt")
        self.assertEqual(result.status, success, (result.message, err))
        self.assertEqual(policy.saved, ["good.bin", "stream.bin"])
        self.assertEqual([name for name, _ in policy.refused], ["meta.yaml", "taken.txt"])
        with open(os.path.join(self.dst, "good.bin"), "rb") as f:
            self.assertEqual(f.read(), good_data)
        with open(os.path.join(self.dst, "stream.bin"), "rb") as f:
            self.assertEqual(f.read(), weird_data)
        with open(os.path.join(self.dst, "taken.txt"), "rb") as f:
            self.assertEqual(f.read(), b"already here")
        self.assertEqual(sorted(os.listdir(self.dst)), ["good.bin", "stream.bin", "taken.txt"])
        self.assert_back_to_normal(user, "utf-8")

    async def test_an_upload_over_the_limit_is_stopped_and_leaves_nothing(self):
        big, _ = self.make("big.bin", 300000)
        policy = file_transfer.UploadPolicy(directory=self.dst, max_bytes=100000, keep_free=0)
        self.job = lambda user: file_transfer.receive_files_zmodem(user, policy)
        # It declares its size: refused before any data
        user, result, err = await self.caller("send", big)
        self.assertEqual(policy.saved, [])
        self.assertIn("larger than", policy.refused[0][1])
        self.assertEqual(os.listdir(self.dst), [])

    async def test_the_page_cancelling_a_download(self):
        path, _ = self.make("cancel.bin", 2_000_000)
        self.job = lambda user: file_transfer.send_files_zmodem(user, [path])
        user, result, err = await self.caller("cancel-receive")
        self.assertNotEqual(result.status, success)
        self.assertEqual(result.message, "The transfer was cancelled.")
        self.assert_back_to_normal(user, "utf-8")


if __name__ == "__main__":
    unittest.main()
