"""Rebuild saved terrain mutations and 3x3 Gate overlays (not units/fire sprites)."""
import csv
import json
from pathlib import Path
from PIL import Image
from export_map_layouts import entries
from export_terrain_names import terrain_names

ROOT = Path(__file__).resolve().parents[1]


def main():
    maps = dict(entries(ROOT / 'Hexzmap.e5'))
    gates = dict(entries(ROOT / 'Gate.e5'))
    names = terrain_names()
    out = ROOT / 'analysis/saved-battlefields'
    out.mkdir(exist_ok=True)
    summaries = []
    with (out / 'overlays.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['save','map_id','object_id','x','y','terrain','terrain_name',
                         'field3','appearance','gate_entry'])
        for path in sorted(ROOT.glob('Sv??s.e5s')):
            data = path.read_bytes()
            # Native serializers: 35-byte save header, 1266-byte battle state,
            # 115*26-byte battle actors, then 1600-byte occupancy map.
            if len(data) != 35+1266+115*26+1600 or data[0] != 5:
                raise ValueError(f'{path.name}: unexpected layout')
            map_id = data[35]
            raw = maps[map_id]
            width,height = raw[0]//3,raw[1]//3
            grid = bytearray(raw[2:])
            image = Image.open(ROOT / f'analysis/battle-maps/battle-{map_id:02d}.png').copy()
            active = gate_count = 0
            for i in range(250):
                x,y,terrain,field3,appearance = data[51+i*5:56+i*5]
                if appearance == 255:
                    continue
                if x >= width or y >= height:
                    raise ValueError(f'{path.name}: overlay {i} outside map')
                active += 1
                grid[y*width+x] = terrain
                entry = (appearance*2-8) if appearance >= 4 else None
                writer.writerow([path.name,map_id,i,x,y,terrain,
                    names[terrain] if terrain < 30 else 'unknown',field3,appearance,entry])
                if entry is not None:
                    tiles = gates[entry]
                    if len(tiles) != 9*2304:
                        raise ValueError(f'Gate {entry}: unexpected tile count')
                    for tile in range(9):
                        tx,ty=x+tile%3-1,y+tile//3-1
                        if 0 <= tx < width and 0 <= ty < height:
                            block=Image.frombytes('P',(48,48),tiles[tile*2304:(tile+1)*2304])
                            image.paste(block,(tx*48,ty*48))
                    gate_count += 1
            image.save(out / f'{path.stem}-gates.png')
            (out / f'{path.stem}-terrain.bin').write_bytes(grid)
            summaries.append(dict(save=path.name,map_id=map_id,active_overlays=active,
                gate_overlays=gate_count,other_overlays=active-gate_count,
                units_and_low_type_sprites_rendered=False))
    (out / 'manifest.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8')
    print(f'Rebuilt {len(summaries)} save maps, '
          f'{sum(r["active_overlays"] for r in summaries)} active terrain overlays, '
          f'{sum(r["gate_overlays"] for r in summaries)} gate overlays')


if __name__ == '__main__':
    main()
