"""Inspect the EEX command stream used by the game."""
from __future__ import annotations

import struct
import sys
from pathlib import Path


def inspect(path: str) -> None:
    data = Path(path).read_bytes()
    if data[:4] != b"EEX\0":
        raise SystemExit(f"{path}: invalid EEX magic")
    print(f"file={path} size={len(data)} version={data[4:6].hex(' ')}")
    # The interpreter receives a pointer to the command area after the fixed
    # 16-byte EEX header; bytes at 0x0a/0x0e are header metadata.
    pos = 0x10
    records = 0
    while pos + 4 <= len(data):
        opcode, units = struct.unpack_from("<HH", data, pos)
        payload_start = pos + 4
        payload_len = units * 2
        end = payload_start + payload_len
        if end > len(data):
            print(f"record={records} offset=0x{pos:X} opcode={opcode} units={units} truncated")
            return
        payload = data[payload_start:end]
        preview = payload.split(b"\0", 1)[0] if opcode == 1 else payload[:16]
        print(f"record={records} offset=0x{pos:X} opcode={opcode} units={units} bytes={payload_len} preview={preview!r}")
        records += 1
        pos = end
        if opcode == 0:
            break
    print(f"records={records} end=0x{pos:X} trailing={len(data)-pos}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: inspect_eex.py FILE [...]")
    for name in sys.argv[1:]:
        inspect(name)
