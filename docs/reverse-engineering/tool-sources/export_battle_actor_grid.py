#!/usr/bin/env python3
import csv,sys
from pathlib import Path
if len(sys.argv)!=3: raise SystemExit('usage: export_battle_actor_grid.py actors.bin output.csv')
b=Path(sys.argv[1]).read_bytes()
with Path(sys.argv[2]).open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f); w.writerow(['slot','unit_id','pos_x','pos_y','side','status','raw_hex'])
 for i in range(0,len(b),26):
  r=b[i:i+26]
  if len(r)<26: break
  x,y=r[8],r[9]; side=r[7]; unit=int.from_bytes(r[0:2],'little'); status=r[14]
  w.writerow([i//26,unit,x,y,side,status,r.hex()])
print(f'actors={len(b)//26} output={sys.argv[2]}')
