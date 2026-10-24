"""zmodem.py against other implementations: zmodem.js (the web terminal's,
run with Node) and lrzsz's sz and rz (the reference, run in WSL).

Each test runs the other side as a child process with the protocol on its
stdin and stdout. A test is skipped when its tool is missing: Node on PATH;
lrzsz in WSL, on its PATH or unpacked in ~/lrzsz (`apt-get download lrzsz &&
dpkg -x lrzsz_*.deb ~/lrzsz/root` needs no root).
"""
import asyncio
import os
import random
import shutil
import subprocess
import tempfile
import unittest

import _setup  # noqa: F401
import zmodem

HERE = os.path.dirname(os.path.abspath(__file__))
PEER = os.path.join(HERE, "zmodem_peer.js")
SETTINGS = zmodem.Settings(start_timeout=20, header_timeout=5, retries=10)


def _find_lrzsz():
    """The directory holding sz and rz inside WSL, or None."""
    if not shutil.which("wsl"):
        return None
    script = ('for d in "$(dirname "$(command -v sz 2>/dev/null)")" "$HOME/lrzsz/root/usr/bin"; do '
              '[ -x "$d/sz" ] && [ -x "$d/rz" ] && { echo "$d"; exit 0; }; done; exit 1')
    try:
        out = subprocess.run(["wsl", "--exec", "sh", "-c", script], capture_output=True,
                             timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    found = out.stdout.decode("utf-8", "replace").strip()
    return found if out.returncode == 0 and found else None


LRZSZ = _find_lrzsz()
NODE = shutil.which("node")


def wsl_path(path):
    """C:\\x\\y -> /mnt/c/x/y"""
    drive, rest = os.path.splitdrive(os.path.abspath(path))
    return "/mnt/" + drive[0].lower() + rest.replace("\\", "/")


def lrzsz(tool, *args, cwd=None):
    """The command running lrzsz's *tool* in WSL (in *cwd*, a Windows path)."""
    command = f'cd "{wsl_path(cwd)}" && ' if cwd else ""
    command += f'exec "{LRZSZ}/{tool}" ' + " ".join(f'"{a}"' for a in args)
    return ["wsl", "--exec", "sh", "-c", command]


class ProcessLink:
    """A Link to a child process's stdin/stdout. *damage(data, offset)*, if
    given, changes what we send on its way."""

    def __init__(self, proc, damage=None):
        self.proc = proc
        self.damage = damage
        self.sent = 0

    async def read(self):
        return await self.proc.stdout.read(65536)

    def write(self, data):
        if self.damage:
            data = self.damage(bytes(data), self.sent)
        self.sent += len(data)
        self.proc.stdin.write(data)

    async def drain(self):
        await self.proc.stdin.drain()


def flip_bytes_at(*offsets):
    """A damage function that corrupts the bytes at these stream offsets."""
    def damage(chunk, start):
        chunk = bytearray(chunk)
        for at in offsets:
            if start <= at < start + len(chunk):
                chunk[at - start] ^= 0x5A
        return bytes(chunk)
    return damage


class FileSink:
    def __init__(self, path):
        self.path = path
        self.f = open(path, "wb")

    def write(self, data):
        self.f.write(data)

    def finish(self):
        self.f.close()

    def discard(self):
        self.f.close()
        os.remove(self.path)


class Interop(unittest.TestCase):
    def setUp(self):
        self.src = tempfile.mkdtemp(prefix="zmodem-src-")
        self.dst = tempfile.mkdtemp(prefix="zmodem-dst-")
        self.rng = random.Random(42)

    def tearDown(self):
        shutil.rmtree(self.src, ignore_errors=True)
        shutil.rmtree(self.dst, ignore_errors=True)

    def make_files(self, sizes):
        files = {}
        for n, size in enumerate(sizes):
            data = (bytes(range(256)) * 2 + self.rng.randbytes(size))[:size]
            path = os.path.join(self.src, f"file{n}-{size}.bin")
            with open(path, "wb") as f:
                f.write(data)
            files[path] = data
        return files

    def assert_arrived(self, files):
        for path, data in files.items():
            with open(os.path.join(self.dst, os.path.basename(path)), "rb") as f:
                self.assertEqual(f.read(), data, os.path.basename(path))

    async def _run(self, argv, session, cwd=None):
        """Start argv; run session(link) against it; return (result, stderr)."""
        proc = await asyncio.create_subprocess_exec(
            *argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
        # Read its stderr all along: a peer that logs a lot would otherwise
        # block once the pipe filled, and stall the protocol.
        stderr = asyncio.create_task(proc.stderr.read())
        try:
            result = await asyncio.wait_for(session(proc), 120)
            proc.stdin.close()
            try:
                await asyncio.wait_for(proc.wait(), 20)
            except asyncio.TimeoutError:
                proc.kill()
            err = await asyncio.wait_for(stderr, 20)
            return result, err.decode("utf-8", "replace")
        except BaseException:
            proc.kill()
            await proc.wait()
            stderr.cancel()
            raise

    def send_to(self, argv, files, damage=None, cwd=None):
        async def session(proc):
            return await zmodem.send_files(ProcessLink(proc, damage), list(files), SETTINGS)
        return asyncio.run(self._run(argv, session, cwd))

    def receive_from(self, argv, damage=None):
        def accept(offer):
            return FileSink(os.path.join(self.dst, os.path.basename(offer.name)))

        async def session(proc):
            return await zmodem.receive_files(ProcessLink(proc, damage), accept, SETTINGS)
        return asyncio.run(self._run(argv, session))

    # -- zmodem.js ---------------------------------------------------------

    @unittest.skipUnless(NODE, "node is not on PATH")
    def test_zmodemjs_downloads_from_us(self):
        files = self.make_files([0, 1, 1023, 1025, 300000])
        results, err = self.send_to(["node", PEER, "receive", self.dst], files)
        self.assertEqual([r.status for r in results], ["sent"] * 5, err)
        self.assert_arrived(files)

    @unittest.skipUnless(NODE, "node is not on PATH")
    def test_zmodemjs_uploads_to_us(self):
        files = self.make_files([0, 5, 8192, 8193, 200000])
        results, err = self.receive_from(["node", PEER, "send", *files])
        self.assertEqual([r.status for r in results], ["received"] * 5, err)
        self.assert_arrived(files)

    @unittest.skipUnless(NODE, "node is not on PATH")
    def test_zmodemjs_cancelling_a_download_stops_us(self):
        files = self.make_files([500000])
        with self.assertRaises(zmodem.Aborted):
            self.send_to(["node", PEER, "cancel-receive"], files)

    # -- lrzsz -------------------------------------------------------------

    def lrzsz(self, tool, *args, cwd=None):
        return lrzsz(tool, *args, cwd=cwd)

    @unittest.skipUnless(LRZSZ, "lrzsz is not available in WSL")
    def test_rz_receives_from_us(self):
        files = self.make_files([0, 1, 1024, 70000])
        results, err = self.send_to(self.lrzsz("rz", "--binary", "--overwrite", cwd=self.dst), files)
        self.assertEqual([r.status for r in results], ["sent"] * 4, err)
        self.assert_arrived(files)

    @unittest.skipUnless(LRZSZ, "lrzsz is not available in WSL")
    def test_rz_asking_for_escaped_control_characters(self):
        files = self.make_files([20000])
        results, err = self.send_to(self.lrzsz("rz", "--binary", "--escape", "--overwrite",
                                               cwd=self.dst), files)
        self.assertEqual([r.status for r in results], ["sent"], err)
        self.assert_arrived(files)

    @unittest.skipUnless(LRZSZ, "lrzsz is not available in WSL")
    def test_rz_repairs_damage_we_suffer_on_the_way(self):
        files = self.make_files([120000])
        with self.assertLogs("dirtyfork.zmodem", "INFO") as logs:
            results, err = self.send_to(
                self.lrzsz("rz", "--binary", "--overwrite", cwd=self.dst), files,
                damage=flip_bytes_at(30000, 90000))
        self.assertTrue(any("again" in line for line in logs.output), logs.output)
        self.assert_arrived(files)

    @unittest.skipUnless(LRZSZ, "lrzsz is not available in WSL")
    def test_sz_sends_to_us(self):
        files = self.make_files([0, 1, 1024, 70000])
        results, err = self.receive_from(self.lrzsz("sz", "--binary", *map(wsl_path, files)))
        self.assertEqual([r.status for r in results], ["received"] * 4, err)
        self.assert_arrived(files)

    @unittest.skipUnless(LRZSZ, "lrzsz is not available in WSL")
    def test_sz_with_every_control_character_escaped(self):
        files = self.make_files([30000])
        results, err = self.receive_from(self.lrzsz("sz", "--binary", "--escape",
                                                    *map(wsl_path, files)))
        self.assertEqual([r.status for r in results], ["received"], err)
        self.assert_arrived(files)

    @unittest.skipUnless(LRZSZ, "lrzsz is not available in WSL")
    def test_sz_resends_what_arrived_damaged(self):
        files = self.make_files([150000])
        # Damage what *sz* sends: wrap the read side
        original_read = ProcessLink.read
        state = {"seen": 0, "hit": [40000, 100000]}

        async def damaged_read(self):
            data = bytearray(await original_read(self))
            for at in state["hit"]:
                if state["seen"] <= at < state["seen"] + len(data):
                    data[at - state["seen"]] ^= 0x5A
            state["seen"] += len(data)
            return bytes(data)
        ProcessLink.read = damaged_read
        try:
            results, err = self.receive_from(self.lrzsz("sz", "--binary", *map(wsl_path, files)))
        finally:
            ProcessLink.read = original_read
        self.assertEqual([r.status for r in results], ["received"], err)
        self.assert_arrived(files)


@unittest.skipUnless(LRZSZ, "lrzsz is not available in WSL")
class YmodemInterop(unittest.TestCase):
    """file_transfer's YMODEM-G (lib/ymodem in a thread, on the byte link)
    against lrzsz: sb streams to our G receiver; rb asks with C, which our
    sender answers as plain YMODEM."""

    def setUp(self):
        self.src = tempfile.mkdtemp(prefix="ymodem-src-")
        self.dst = tempfile.mkdtemp(prefix="ymodem-dst-")

    def tearDown(self):
        shutil.rmtree(self.src, ignore_errors=True)
        shutil.rmtree(self.dst, ignore_errors=True)

    def run_against(self, argv, job, cwd=None):
        import file_transfer

        async def go():
            proc = await asyncio.create_subprocess_exec(
                *argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            err = asyncio.ensure_future(proc.stderr.read())
            link = ProcessLink(proc)

            async def direct(user, text, work):  # (no screen to save: straight to the link)
                return await work(link)
            original = file_transfer._with_screen
            file_transfer._with_screen = direct
            try:
                return await asyncio.wait_for(job(file_transfer), 120), proc, err
            finally:
                file_transfer._with_screen = original
                proc.stdin.close()
                try:
                    await asyncio.wait_for(proc.wait(), 20)
                except asyncio.TimeoutError:
                    proc.kill()
        result, proc, err = asyncio.run(go())
        return result

    def test_our_ymodem_g_receiver(self):
        """lrzsz's sb has no YMODEM-G (it never answers a G), so the sender here
        is lib/ymodem's own, in G mode, on the other end of an in-memory link."""
        import file_transfer
        from test_zmodem import End, Pipe
        from ymodem.Protocol import ProtocolType
        from ymodem.Socket import ModemSocket
        data = bytes(range(256)) * 300 + b"\x18" * 50 + b"tail"  # (CANs in the data are data)
        path = os.path.join(self.src, "yfile.bin")
        with open(path, "wb") as f:
            f.write(data)
        policy = file_transfer.UploadPolicy(directory=self.dst, keep_free=0)

        async def go():
            a, b = Pipe(), Pipe()
            ours, theirs = End(a, b), End(b, a)

            async def direct(user, text, work):
                return await work(ours)
            original = file_transfer._with_screen
            file_transfer._with_screen = direct
            loop = asyncio.get_running_loop()
            sender_link = file_transfer._ThreadedLink(theirs, loop, watch_cancel=True)
            await sender_link.start()
            sender = ModemSocket(sender_link.read, sender_link.write,
                                 protocol_type=ProtocolType.YMODEM, protocol_type_options=["g"])
            try:
                sent, received = await asyncio.wait_for(asyncio.gather(
                    asyncio.to_thread(sender.send, [path]),
                    file_transfer.receive_files_ymodem(object(), policy)), 60)
                return sent, received
            finally:
                file_transfer._with_screen = original
                await sender_link.stop()
        sent, received = asyncio.run(go())
        self.assertEqual(received.status, 1, received.message)  # (success)
        self.assertEqual(policy.saved, ["yfile.bin"])
        with open(os.path.join(self.dst, "yfile.bin"), "rb") as f:
            self.assertEqual(f.read()[:len(data)], data)  # (YMODEM pads the last block)
        self.assertEqual(os.listdir(self.dst), ["yfile.bin"])  # (the staging folder is gone)

    def test_rb_receives_from_our_sender(self):
        data = bytes(range(256)) * 200
        path = os.path.join(self.src, "out.bin")
        with open(path, "wb") as f:
            f.write(data)
        result = self.run_against(lrzsz("rb", "--ymodem", cwd=self.dst),
                                  lambda ft: ft.send_files_ymodem(object(), [path]))
        self.assertEqual(result.status, 1, result.message)
        with open(os.path.join(self.dst, "out.bin"), "rb") as f:
            got = f.read()
        self.assertEqual(got[:len(data)], data)  # (YMODEM pads to the block; rb trims to the size sent)


if __name__ == "__main__":
    unittest.main()
