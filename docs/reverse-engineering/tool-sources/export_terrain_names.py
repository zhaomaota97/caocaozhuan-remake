"""Read the terrain-name pointer table used by the native terrain UI."""
import csv
import struct
from pathlib import Path
import pefile

ROOT = Path(__file__).resolve().parents[1]


def terrain_names():
    pe = pefile.PE(str(ROOT / 'Ekd5.exe'))
    pointers = struct.unpack('<30I', pe.get_data(0x8BDB0, 120))
    return [pe.get_data(p - pe.OPTIONAL_HEADER.ImageBase, 64).split(b'\0', 1)[0].decode('gbk')
            for p in pointers]


if __name__ == '__main__':
    names = terrain_names()
    with (ROOT / 'analysis/terrain-names.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['terrain_id', 'name_gbk'])
        w.writerows(enumerate(names))
    print(f'Exported {len(names)} terrain names')
