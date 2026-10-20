"""Render native tile/bank layouts; palette is an explicit battlefield preview choice."""
import argparse
import json
from pathlib import Path
from PIL import Image
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--palette-map',type=int,default=0)
    args=parser.parse_args()
    palette=dict(entries(ROOT/'Spalet.e5'))[args.palette_map].ljust(768,b'\0')
    rgb=bytes(v & 0xf0 for i in range(0,768,3)
              for v in (palette[i+1],palette[i+2],palette[i]))
    out=ROOT/'analysis/animation-sheets';out.mkdir(exist_ok=True)
    manifest=[]
    for family,side,count in [('mov',48,11),('spc',48,5),('atk',64,12)]:
        for index,raw in entries(ROOT/f'Unit_{family}.e5'):
            if len(raw)!=side*side*count:raise ValueError('Unexpected animation size')
            columns,rows=(3,4) if family=='atk' else (count,1)
            image=Image.new('P',(side*columns,side*rows));image.putpalette(rgb)
            for tile in range(count):
                # Attack data is three consecutive 64x256 banks, four tiles per bank.
                x,y=(tile//4,tile%4) if family=='atk' else (tile,0)
                block=Image.frombytes('P',(side,side),raw[tile*side*side:(tile+1)*side*side])
                image.paste(block,(x*side,y*side))
            image.save(out/f'{family}-{index:03d}.png')
            manifest.append(dict(family=family,index=index,tile_size=side,tile_count=count,
                                 palette_map=args.palette_map,frame_timing_recovered=False))
    (out/'layouts.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f'Rendered {len(manifest)} animation sheets')


if __name__=='__main__':main()
