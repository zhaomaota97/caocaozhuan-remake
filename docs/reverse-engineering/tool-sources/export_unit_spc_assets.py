"""Export Unit_spc.e5 48x48 indexed special-action frames."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]


def main():
    records=[];out=ROOT/'analysis/unit-spc';out.mkdir(exist_ok=True)
    palettes=list(entries(ROOT/'Spalet.e5'))
    palette=palettes[0][1].ljust(768,b'\0')
    rgb=bytes(v & 0xf0 for c in range(256) for v in
              (palette[c*3+1],palette[c*3+2],palette[c*3]))
    for index,raw in entries(ROOT/'Unit_spc.e5'):
        if len(raw)!=48*48*5:
            raise ValueError(f'entry {index} size {len(raw)}')
        frames=[]
        for frame in range(5):
            pixels=raw[frame*2304:(frame+1)*2304]
            image=Image.frombytes('P',(48,48),pixels);image.putpalette(rgb)
            image.save(out/f'{index:03d}-{frame}.png',transparency=0)
            frames.append(dict(frame=frame,sha256=hashlib.sha256(pixels).hexdigest(),zero=pixels.count(0)))
        records.append(dict(index=index,size=len(raw),sha256=hashlib.sha256(raw).hexdigest(),frames=frames))
    result=dict(file='Unit_spc.e5',entries=len(records),frame_size=[48,48],frames_per_entry=5,
                bytes_per_frame=2304,palette='Spalet.e5 entry0 baseline preview only',
                records=records,source='0x43D108 loads entry 0x43FC48(unit) and renders 5 frames at 0x30x0x30')
    (ROOT/'analysis/unit-spc-assets.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(f'Exported {len(records)} Unit_spc entries and {len(records)*5} frames')


if __name__=='__main__':main()
