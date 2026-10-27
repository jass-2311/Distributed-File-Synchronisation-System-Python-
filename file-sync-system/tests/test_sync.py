"""Loopback integration tests for local file transfers."""
import socket, tempfile, threading, unittest
from pathlib import Path
from client.client import sync_folder
from server.server import serve_once, valid_header
from utils.hash_utils import file_hash

class FileSyncTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.input = Path(temp.name) / "input"
        self.output = Path(temp.name) / "output"
        self.input.mkdir()
        self.output.mkdir()

    def run_session(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        ready = threading.Event()
        worker = threading.Thread(target=serve_once, args=("127.0.0.1",port,self.output,ready))
        worker.start()
        self.assertTrue(ready.wait(timeout=5))
        try:
            result = sync_folder(self.input, port=port)
        finally:
            worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        return result

    def test_multiple_files_and_skip_unchanged(self):
        (self.input / "note.txt").write_text("hello")
        (self.input / "large.bin").write_bytes(b"abc123" * 150000)
        (self.input / "empty.txt").write_bytes(b"")
        self.assertEqual(self.run_session(), {"sent": 3, "skipped": 0})
        for path in self.input.iterdir():
            self.assertEqual(file_hash(path), file_hash(self.output / path.name))
        self.assertEqual(self.run_session(), {"sent": 0, "skipped": 3})
        (self.input / "note.txt").write_text("edited")
        self.assertEqual(self.run_session(), {"sent": 1, "skipped": 2})
        self.assertEqual((self.output / "note.txt").read_text(), "edited")

    def test_path_traversal_rejected(self):
        for name in ("../secret.txt", "nested/file.txt", "..", "bad\\name"):
            with self.assertRaises(ValueError):
                valid_header({"name":name,"size":1,"sha256":"a"*64})
