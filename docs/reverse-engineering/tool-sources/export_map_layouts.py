"""Recover Hexzmap terrain grids and Pmap three-dimensional uint16 arrays."""
import csv
import json
import struct
from pathlib import Path
from collections import Counter
from extract_e5 import decode
from export_terrain_names import terrain_names

ROOT = Path(__file__).resolve().parents[1]


def entries(path):
    data = path.read_bytes()
    if data[:4] != b'Ls12':
        raise ValueError(f'{path.name}: invalid magic')
    first = struct.unpack_from('>III', data, 0x110)[2]
    if first < 0x11C or first > len(data):
        raise ValueError(f'{path.name}: unsupported index span')
    for index in range((first-0x110)//12):
        packed, size, offset = struct.unpack_from('>III', data, 0x110+index*12)
        if offset < first or not packed:
            raise ValueError(f'{path.name}: invalid resource span at {index}')
        yield index, decode(data, offset, packed, size)


def main():
    target = ROOT / 'analysis/map-layouts'
    target.mkdir(exist_ok=True)
    names = terrain_names()
    summary = dict(hexzmap=[], pmap=[])
    with (target / 'terrain-cells.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['map_id','x','y','terrain_id','terrain_name'])
        for index, raw in entries(ROOT / 'Hexzmap.e5'):
            width, height = raw[0]//3, raw[1]//3
            if not width or not height or len(raw) != 2+width*height:
                raise ValueError(f'Hexzmap {index}: size mismatch')
            grid = raw[2:]
            counts = Counter(grid)
            summary['hexzmap'].append(dict(id=index, width=width, height=height,
                raw_dimensions=list(raw[:2]), size=len(raw), terrain_counts=dict(counts)))
            (target / f'hexzmap-{index:03d}.bin').write_bytes(raw)
            for pos, terrain in enumerate(grid):
                writer.writerow([index,pos%width,pos//width,terrain,
                                 names[terrain] if terrain < len(names) else 'unknown'])
    for index, raw in entries(ROOT / 'Pmap.e5'):
        header = struct.unpack_from('<8H', raw)
        width, height, depth = header[1:4]
        if len(raw) != 16+2*width*height*depth:
            raise ValueError(f'Pmap {index}: size mismatch')
        (target / f'pmap-{index:03d}.bin').write_bytes(raw)
        summary['pmap'].append(dict(id=index, width=width, height=height, depth=depth,
                                    header=list(header), size=len(raw)))
    (target / 'layouts.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(f'Validated {len(summary["hexzmap"])} terrain grids and {len(summary["pmap"])} Pmap arrays')


if __name__ == '__main__':
    main()
