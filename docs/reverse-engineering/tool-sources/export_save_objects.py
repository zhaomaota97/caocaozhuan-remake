"""Export native 32-byte object records from version-5 d save partitions."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START, STRIDE, COUNT = 0x14DC, 0x20, 512


def main():
    output = ROOT / 'analysis' / 'save-objects.csv'
    checks = []
    with output.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['file', 'object_id', 'file_offset', 'runtime_04',
                         'runtime_02', 'runtime_2a', 'runtime_1c',
                         'class_2b', 'level_2c', 'runtime_2d',
                         'slot0_hex', 'slot1_hex', 'slot2_hex', 'record_hex'])
        for source in sorted(ROOT.glob('Sv??d.e5s')):
            data = source.read_bytes()
            expected = START + STRIDE * COUNT
            if len(data) != expected or data[0] != 5:
                raise ValueError(f'{source.name}: unsupported size/version')
            for index in range(COUNT):
                offset = START + STRIDE * index
                row = data[offset:offset + STRIDE]
                writer.writerow([source.name, index, hex(offset),
                                 int.from_bytes(row[0:2], 'little'), row[2], row[3],
                                 int.from_bytes(row[14:16], 'little'),
                                 row[17], row[18], row[19],
                                 row[20:23].hex(), row[23:26].hex(),
                                 row[26:29].hex(), row.hex()])
            checks.append(dict(file=source.name, records=COUNT, stride=STRIDE,
                               start=START, end=expected, file_size=len(data)))
    if not checks:
        raise ValueError('No save files found')
    (ROOT / 'analysis' / 'save-object-validation.json').write_text(
        json.dumps(checks, indent=2), encoding='utf-8')
    print(f'Exported {len(checks) * COUNT} records from {len(checks)} saves')


if __name__ == '__main__':
    main()
