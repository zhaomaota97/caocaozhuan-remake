"""Extract load-dialog control snapshots from observe_live_game events."""
import json,sys
from pathlib import Path

if len(sys.argv)!=2:
    raise SystemExit('usage: summarize_live_load_controls.py <events.jsonl>')
source=Path(sys.argv[1])
rows=[]
for line in source.read_text(encoding='utf-8').splitlines():
    try:
        record=json.loads(line)
        payload=record.get('payload',record)
    except json.JSONDecodeError:
        continue
    if payload.get('event')!='controls':
        continue
    controls=payload.get('controls',[])
    interesting=[c for c in controls if c.get('id') in (2,6,7,1332,1487)
                 or c.get('kind') in ('SysListView32','Button')]
    if interesting:
        rows.append({'seconds':payload.get('seconds'),'parent':payload.get('parent'),
                     'controls':interesting})
result={'source':str(source),'snapshots':rows}
out=source.parent/'load-control-summary.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Load control snapshots: {len(rows)} -> {out}')
