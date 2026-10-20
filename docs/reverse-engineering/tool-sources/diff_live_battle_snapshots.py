#!/usr/bin/env python3
import sys,json
from pathlib import Path
if len(sys.argv)!=3: raise SystemExit('usage: diff_live_battle_snapshots.py before_dir after_dir')
a,b=map(Path,sys.argv[1:]); out={}
for p in a.glob('snapshot-*.bin'):
 q=b/(p.name.replace('snapshot-','postmove-snapshot-'))
 if not q.exists(): continue
 x,y=p.read_bytes(),q.read_bytes(); changes=[i for i,(u,v) in enumerate(zip(x,y)) if u!=v]
 out[p.stem]={'before_bytes':len(x),'after_bytes':len(y),'changed_bytes':len(changes),'first_offsets':changes[:32]}
print(json.dumps(out,ensure_ascii=False,indent=2))
(b/'battle-snapshot-diff.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
