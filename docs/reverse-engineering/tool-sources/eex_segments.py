"""Recover EEX extension headers and the absolute script offset table."""
import json
import struct
from pathlib import Path


def inspect(path):
    data = path.read_bytes()
    if data[:4] != b'EEX\0':
        raise ValueError('invalid EEX magic')
    pos = 6
    while True:
        kind, length = struct.unpack_from('<HH', data, pos)
        pos += 4 + length
        if pos > len(data):
            raise ValueError('extension outside file')
        if kind == 0:
            break
    first = struct.unpack_from('<I', data, pos)[0]
    if first <= pos or (first-pos) % 4:
        raise ValueError('invalid table')
    offsets = list(struct.unpack_from('<'+'I'*((first-pos)//4), data, pos))
    if offsets != sorted(offsets) or offsets[-1] >= len(data):
        raise ValueError('invalid offsets')
    segments = []
    for a, b in zip(offsets, offsets[1:] + [len(data)]):
        marker, length = struct.unpack_from('<HH', data, a)
        segments.append({'offset': a, 'size': b-a, 'first_word': marker,
                         'second_word': length,
                         'length_delimited_block': marker == 1 and length == b-a-4})
    return {'file': str(path), 'table_offset': pos, 'segments': segments}


if __name__ == '__main__':
    rows = [inspect(p) for p in sorted(Path('.').glob('*.eex'))]
    Path('analysis/eex-segments.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    print('files', len(rows), 'segments', sum(len(r['segments']) for r in rows))
