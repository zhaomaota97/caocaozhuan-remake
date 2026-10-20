"""Extract Ls12 .e5 resources using the loader-compatible bit/LZ codec."""
from __future__ import annotations

import struct
import sys
from pathlib import Path


class Bits:
    def __init__(self, data: bytes, start: int):
        self.data, self.pos, self.bits, self.left = data, start, 0, 0

    def read(self, n: int) -> int:
        value = 0
        for _ in range(n):
            if not self.left:
                if self.pos >= len(self.data):
                    raise EOFError("compressed stream ended")
                self.bits, self.pos, self.left = self.data[self.pos], self.pos + 1, 8
            value = (value << 1) | ((self.bits >> 7) & 1)
            self.bits = (self.bits << 1) & 0xFF
            self.left -= 1
        return value


def varint(bits: Bits) -> int:
    value = 0
    width = 0
    while True:
        value = value * 2 + bits.read(1)
        width += 1
        if (value & 1) == 0:
            return value + bits.read(width)


def decode(data: bytes, offset: int, compressed: int, output_size: int) -> bytes:
    if offset < 0 or compressed < 0 or offset + compressed > len(data):
        raise ValueError('resource span outside container')
    if compressed == output_size:
        return data[offset:offset + compressed]
    bits = Bits(data[: offset + compressed], offset)
    dictionary = data[0x10:0x110]
    out = bytearray()
    while len(out) < output_size:
        prefix = 0
        width = 0
        while True:
            prefix = prefix * 2 + bits.read(1)
            width += 1
            if (prefix & 1) == 0:
                break
        token = prefix + bits.read(width)
        if token < 0x100:
            out.append(dictionary[token])
        else:
            distance = token - 0x100
            length = varint(bits) + 3
            if distance <= 0 or distance > len(out):
                raise ValueError(f"invalid back-reference distance={distance}")
            for _ in range(length):
                out.append(out[-distance])
                if len(out) > output_size:
                    raise ValueError("decoded output exceeds declared size")
    return bytes(out)


def main(path: str, out_dir: str) -> None:
    source = Path(path)
    data = source.read_bytes()
    if data[:4] != b"Ls12":
        raise SystemExit("not an Ls12 container")
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    index = 0x110
    count = 0
    while index + 12 <= len(data):
        compressed, output_size, offset = struct.unpack(">III", data[index:index + 12])
        if not compressed or offset < 0x110 or offset + compressed > len(data):
            break
        result = decode(data, offset, compressed, output_size)
        (target / f"resource_{count:04d}.bin").write_bytes(result)
        print(f"{count}: offset=0x{offset:X} compressed={compressed} output={len(result)}")
        index += 12
        count += 1


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: extract_e5.py FILE [OUT_DIR]")
    main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else "extracted_e5")
