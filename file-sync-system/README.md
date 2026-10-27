# Distributed File Synchronisation — Local TCP Demo

A Python learning project demonstrating chunked client/server file transfers, framed messages, SHA-256 integrity checks and skipping unchanged files. It synchronises **top-level files only**, from a client directory into a server directory.

## Features

- Transfer binary, text, and empty files (up to 50 MiB each).
- Frame JSON messages using a four-byte length prefix, followed by exact-length file data.
- Compare SHA-256 hashes to skip files already present on the server.
- Verify received checksums before atomically replacing the destination.
- Reject unsafe filenames and traversal paths.
- Loopback end-to-end tests with multiple, large and changed files.

## Run

Requires Python 3.10+; **no external packages**. Run these commands from the file-sync-system directory.

Terminal 1:

    python -m server.server --storage storage

Terminal 2:

    mkdir -p sync_folder
    echo Hello > sync_folder/example.txt
    python -m client.client --folder sync_folder

The server accepts one client per run, so restart it before running the client again. On the second run, unchanged files should be skipped.

## Test

    python -m unittest discover -s tests -v

## Architecture

- client/client.py: scans directory, computes hashes and sends files
- server/server.py: receives, validates, hashes and atomically saves files
- utils/protocol.py: length-prefixed JSON messages and exact reads
- utils/hash_utils.py: chunked SHA-256 hashing
- tests/test_sync.py: real TCP loopback integration tests

## Limitations

**Local demonstration only. Do not expose this server to the internet.** No TLS, authentication, support for nested directories, deletion propagation, conflict resolution or resumable downloads. Supports one connected client per server session. Future work: TLS/authentication, manifests, resumable transfers and concurrency.
