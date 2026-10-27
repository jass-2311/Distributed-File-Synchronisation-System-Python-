"""Sync local top-level files with framed TCP transfers and SHA-256."""
import argparse
from pathlib import Path
import socket

from utils.hash_utils import file_hash
from utils.protocol import MAX_FILE, receive_message, send_message

def sync_folder(folder="sync_folder", host="127.0.0.1", port=5001):
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"Not a directory: {folder}")
    stats = {"sent": 0, "skipped": 0}
    with socket.create_connection((host, port), timeout=15) as conn:
        conn.settimeout(15)
        for file in sorted(folder.iterdir()):
            if not file.is_file() or file.is_symlink():
                continue
            size = file.stat().st_size
            if size > MAX_FILE:
                raise ValueError(f"File exceeds 50 MiB limit: {file.name}")
            send_message(conn, {"type": "file", "name": file.name, "size": size, "sha256": file_hash(file)})
            response = receive_message(conn)
            if response.get("action") == "skip":
                stats["skipped"] += 1
                continue
            if response.get("action") != "send":
                raise RuntimeError(f"Unexpected server response: {response}")
            with file.open("rb") as source:
                for block in iter(lambda: source.read(65536), b""):
                    conn.sendall(block)
            confirmation = receive_message(conn)
            if confirmation.get("status") != "ok":
                raise RuntimeError(f"Transfer failed: {confirmation}")
            stats["sent"] += 1
        send_message(conn, {"type": "end"})
    return stats

def main():
    parser = argparse.ArgumentParser(description="Local file-sync client")
    parser.add_argument("--folder", default="sync_folder")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()
    stats = sync_folder(args.folder, args.host, args.port)
    print(f"Sent: {stats['sent']}; skipped unchanged: {stats['skipped']}")

if __name__ == "__main__":
    main()
