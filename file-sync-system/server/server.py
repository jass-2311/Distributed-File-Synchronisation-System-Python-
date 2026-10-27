"""Receive and verify files over a localhost TCP socket."""
import argparse
import hashlib
import os
from pathlib import Path
import socket
import tempfile

from utils.hash_utils import file_hash
from utils.protocol import MAX_FILE, receive_message, send_message

def valid_header(message):
    name, size, digest = message.get("name"), message.get("size"), message.get("sha256")
    if not isinstance(name, str) or not name or len(name) > 255 or name in {".", ".."}:
        raise ValueError("Invalid filename")
    if name != Path(name).name or "/" in name or "\\" in name:
        raise ValueError("Only simple filenames are allowed")
    if type(size) is not int or not 0 <= size <= MAX_FILE:
        raise ValueError("Invalid file size")
    if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError("Invalid SHA-256 digest")
    return name, size, digest

def receive_file(conn, storage, name, size, digest):
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=storage, prefix=".incoming-", delete=False) as target:
            temp_path = Path(target.name)
            hasher = hashlib.sha256()
            remaining = size
            while remaining:
                chunk = conn.recv(min(65536, remaining))
                if not chunk:
                    raise EOFError("Transfer interrupted")
                target.write(chunk)
                hasher.update(chunk)
                remaining -= len(chunk)
        if hasher.hexdigest() != digest:
            send_message(conn, {"status": "error", "message": "Checksum mismatch"})
            return False
        os.replace(temp_path, storage / name)
        temp_path = None
        send_message(conn, {"status": "ok"})
        return True
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()

def serve_connection(conn, storage):
    while True:
        header = receive_message(conn)
        if header.get("type") == "end":
            return
        if header.get("type") != "file":
            raise ValueError("Unsupported message type")
        name, size, digest = valid_header(header)
        destination = storage / name
        if destination.is_file() and destination.stat().st_size == size and file_hash(destination) == digest:
            send_message(conn, {"action": "skip"})
            continue
        send_message(conn, {"action": "send"})
        if not receive_file(conn, storage, name, size, digest):
            return

def serve_once(host="127.0.0.1", port=5001, storage="storage", ready_event=None):
    directory = Path(storage)
    directory.mkdir(parents=True, exist_ok=True)
    with socket.socket() as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(1)
        server.settimeout(15)
        if ready_event is not None:
            ready_event.set()
        with server.accept()[0] as conn:
            conn.settimeout(15)
            serve_connection(conn, directory)

def main():
    parser = argparse.ArgumentParser(description="Local file-sync server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--storage", default="storage")
    args = parser.parse_args()
    print(f"Waiting for one client on {args.host}:{args.port}")
    serve_once(args.host, args.port, args.storage)
    print("Session completed")

if __name__ == "__main__":
    main()
