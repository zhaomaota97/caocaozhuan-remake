"""Compare actual post-load memory serialized by native code to save/resource data."""
import hashlib
import json
import sys
from pathlib import Path
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]


def main(folder,slot):
    save=(ROOT/f'Sv{slot:02d}s.e5s').read_bytes();map_id=save[35]
    terrain_raw=dict(entries(ROOT/'Hexzmap.e5'))[map_id]
    width,height=terrain_raw[0]//3,terrain_raw[1]//3
    terrain=bytearray(terrain_raw[2:]);artwork=bytearray((ROOT/f'Hm{map_id:02d}.e5').read_bytes())
    gates=None
    for index in range(250):
        x,y,value,unused,appearance=save[51+index*5:56+index*5]
        if appearance==255:continue
        terrain[x+y*width]=value
        if appearance>=4:
            if gates is None:gates=dict(entries(ROOT/'Gate.e5'))
            tiles=gates[appearance*2-8]
            for tile in range(9):
                tx,ty=x+tile%3-1,y+tile//3-1
                if 0<=tx<width and 0<=ty<height:
                    pos=(tx+ty*width)*2304
                    artwork[pos:pos+2304]=tiles[tile*2304:(tile+1)*2304]
    expected={'roster':(ROOT/f'Sv{slot:02d}d.e5s').read_bytes()[0x14dc:],
              'actors':save[1301:4291],'state':save[35:1301],
              'terrain':terrain,'artwork':artwork}
    rows=[]
    for kind,wanted in expected.items():
        actual=(folder/f'snapshot-{kind}.bin').read_bytes()
        changed=[i for i,(a,b) in enumerate(zip(actual,wanted)) if a!=b]
        rows.append(dict(kind=kind,size=len(actual),expected_size=len(wanted),
            match=actual==wanted,differences=len(changed),first_differences=changed[:20],
            actual_sha256=hashlib.sha256(actual).hexdigest(),expected_sha256=hashlib.sha256(wanted).hexdigest()))
    result=dict(slot=slot,map_id=map_id,width=width,height=height,buffers=rows,
                bytes_compared=sum(len(b) for b in expected.values()),passed=all(r['match'] for r in rows))
    (folder/'snapshot-validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(f'Actual live snapshot: {sum(r["match"] for r in rows)}/{len(rows)} buffers; '
          f'{result["bytes_compared"]} bytes compared')
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main(Path(sys.argv[1]),int(sys.argv[2]))
