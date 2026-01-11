import socket
import os

HOST = '127.0.0.1'
PORT = 5001
STORAGE_DIR = 'storage'

os.makedirs(STORAGE_DIR, exist_ok=True)

server = socket.socket()
server.bind((HOST, PORT))
server.listen(1)

print("Server listening on", PORT)

conn, addr = server.accept()
print("Connected by", addr)

while True:
    data = conn.recv(1024)
    if not data:
        break
    filename = data.decode()
    filedata = conn.recv(4096)
    with open(os.path.join(STORAGE_DIR, filename), 'wb') as f:
        f.write(filedata)
    conn.send(b'File received')

conn.close()
