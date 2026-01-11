import socket
import os
from utils.hash_utils import file_hash

HOST = '127.0.0.1'
PORT = 5001
SYNC_DIR = 'sync_folder'

client = socket.socket()
client.connect((HOST, PORT))

for file in os.listdir(SYNC_DIR):
    path = os.path.join(SYNC_DIR, file)
    if os.path.isfile(path):
        client.send(file.encode())
        with open(path, 'rb') as f:
            client.send(f.read())
        print(f"Sent {file}")

print("Sync complete")
client.close()
