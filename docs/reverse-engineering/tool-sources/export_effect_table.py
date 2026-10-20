"""Export Data.e5 entry 5 using the 0x40DDAF native record layout."""
import csv
import struct
from pathlib import Path
from extract_e5 import decode

ROOT = Path(__file__).resolve().parents[1]


def main():
    data = (ROOT / 'Data.e5').read_bytes()
    packed, size, offset = struct.unpack_from('>III', data, 0x110 + 5 * 12)
    raw = decode(data, offset, packed, size)
    if len(raw) % 70:
        raise ValueError('Effect table is not a multiple of 70 bytes')
    learning = []
    with (ROOT / 'analysis/effects.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['id', 'name_gbk', 'loaded_by_41b84f', 'budget_cost_candidate',
                    'effect_type', 'disk_hex', 'runtime_hex'])
        for index in range(len(raw) // 70):
            disk = raw[index * 70:(index + 1) * 70]
            runtime = bytearray(70)
            runtime[:10] = disk[:10]
            runtime[11:15] = disk[12:16]
            runtime[15] = disk[11]
            runtime[16:] = disk[16:]
            name = disk[:10].split(b'\0', 1)[0].decode('gbk', errors='strict')
            w.writerow([index, name, index < 68, runtime[14], runtime[15],
                        disk.hex(), runtime.hex()])
            for class_id, threshold in enumerate(runtime[17:]):
                learning.append([index, name, class_id, threshold,
                                 threshold != 0, index < 68])
    with (ROOT / 'analysis/effect-learning.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['effect_id', 'name_gbk', 'class_id', 'required_level',
                    'learnable', 'loaded_by_41b84f'])
        w.writerows(learning)
    print(f'Exported {len(raw) // 70} effects; startup loader consumes first 68')


if __name__ == '__main__':
    main()
