"""Length-prefixed JSON protocol for localhost TCP file transfer."""
import json
import struct

MAX_HEADER = 4096
MAX_FILE = 50 * 1024 * 1024

def receive_exact(sock, length):
    result = bytearray()
    while len(result) < length:
        part = sock.recv(min(65536, length - len(result)))
        if not part:
            raise EOFError("Connection closed before full payload arrived")
        result.extend(part)
    return bytes(result)

def send_message(sock, value):
    payload = json.dumps(value, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_HEADER:
        raise ValueError("Header too large")
    sock.sendall(struct.pack("!I", len(payload)) + payload)

def receive_message(sock):
    size = struct.unpack("!I", receive_exact(sock, 4))[0]
    if not 2 <= size <= MAX_HEADER:
        raise ValueError("Invalid header length")
    value = json.loads(receive_exact(sock, size).decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Expected JSON object")
    return value
