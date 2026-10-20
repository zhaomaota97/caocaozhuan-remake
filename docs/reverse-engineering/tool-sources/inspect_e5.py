"""Dump the fixed header and candidate 12-byte DATA.E5 index fields.

This is deliberately an inspector, not an extractor: the executable's loader
must still validate which fields represent stream offsets and lengths.
"""
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
                    raise EOFError
                self.bits, self.pos, self.left = self.data[self.pos], self.pos + 1, 8
            value = (value << 1) | ((self.bits >> 7) & 1)
            self.bits = (self.bits << 1) & 0xFF
            self.left -= 1
        return value


def decode_lz(data: bytes, start: int, output_size: int, dictionary: bytes) -> bytes:
    """Exploratory decoder only; the game's dictionary initialization is unknown."""
    bits = Bits(data, start)
    out = bytearray()
    while len(out) < output_size:
        prefix = 0
        width = 0
        while True:
            bit = bits.read(1)
            prefix = prefix * 2 + bit
            width += 1
            if (prefix & 1) == 0:
                break
        token = prefix + bits.read(width)
        if token < 0x100:
            out.append(dictionary[token])
        else:
            distance = token - 0xFF
            length = decode_var(bits) + 3
            if distance > len(out):
                raise ValueError("back-reference before output")
            for _ in range(length):
                out.append(out[-distance])
                if len(out) > output_size:
                    raise ValueError("output overrun")
    return bytes(out)


def decode_var(bits: Bits) -> int:
    value = 0
    width = 0
    while True:
        part = bits.read(1)
        value = value * 2 + part
        width += 1
        if (value & 1) == 0:
            break
    return value + bits.read(width)


def main(path: str) -> None:
    data = Path(path).read_bytes()
    if data[:4] != b"Ls12":
        raise SystemExit(f"{path}: not an Ls12 container")
    print(f"file={path} size={len(data)} header={data[:16]!r}")
    start = 0x110
    count = min((len(data) - start) // 12, 32)
    previous_offset = None
    for index in range(count):
        raw = data[start + index * 12 : start + (index + 1) * 12]
        be = struct.unpack(">III", raw)
        le = struct.unpack("<III", raw)
        print(f"{index:04d} raw={raw.hex(' ')} be={be} le={le}")
        if previous_offset is not None:
            expected = previous_offset + previous_length
            if be[2] != expected:
                print(f"  invariant=FAIL expected_cumulative={expected}")
        previous_length = be[0]
        previous_offset = be[2]
        if index < count - 1 and be[2] < len(data):
            next_offset = struct.unpack(">III", data[start + (index + 1) * 12 : start + (index + 2) * 12])[2]
            segment = data[be[2] : next_offset]
            if len(segment) == be[0]:
                print(f"  segment=raw-uncompressed start=0x{be[2]:X} size={len(segment)}")
    if len(data) >= 0x11C:
        length, capacity, offset = struct.unpack(">III", data[0x110:0x11C])
        print(f"decode_probe compressed={length} output={capacity} offset={offset}")
        for start in (0x110, 0x18C, 0x190, 0x200, 0x300, offset):
            try:
                decoded = decode_lz(data, start, capacity, data[0x10:0x110])
                print(f"  candidate_start=0x{start:X} decoded={len(decoded)} head={decoded[:16].hex(' ')}")
            except (EOFError, ValueError, IndexError) as exc:
                print(f"  candidate_start=0x{start:X} failed={exc}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: inspect_e5.py FILE")
    main(sys.argv[1])
