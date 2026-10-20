"""Decode camera target tile fields from a native 0x24-byte actor table dump."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('dump',type=Path)
    parser.add_argument('--slots',type=int,default=115)
    args=parser.parse_args()
    raw=args.dump.read_bytes()
    stride=0x24
    if len(raw)<args.slots*stride: raise SystemExit(f'actor dump too small: {len(raw)}')
    rows=[]
    for slot in range(args.slots):
        record=raw[slot*stride:(slot+1)*stride]
        rows.append({'slot':slot,'rosterIndex':int.from_bytes(record[0:4],'little'),
                     'x':record[6],'y':record[7]})
    print(json.dumps(rows,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
