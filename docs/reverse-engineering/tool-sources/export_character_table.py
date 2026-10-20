"""Export raw character records without guessing unnamed attribute semantics."""
import csv
from pathlib import Path

from extract_e5 import decode
import struct


def main():
    data = Path('Data.e5').read_bytes()
    packed, size, offset = struct.unpack_from('>III', data, 0x110)
    decoded = decode(data, offset, packed, size)
    assert len(decoded) == 512 * 32
    target = Path('analysis/characters.csv')
    target.parent.mkdir(exist_ok=True)
    with target.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['id', 'name_gbk', 'name_raw', 'record_hex'])
        for index in range(512):
            record = decoded[index * 32:(index + 1) * 32]
            name = record[:12].split(b'\0', 1)[0]
            writer.writerow([index, name.decode('gbk', errors='replace'), name.hex(), record.hex(' ')])
    print(target)


if __name__ == '__main__':
    main()
