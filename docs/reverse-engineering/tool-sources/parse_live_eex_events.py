import json,sys,struct
from pathlib import Path

if len(sys.argv)!=2: raise SystemExit('usage: parse_live_eex_events.py EVENTS.JSONL')
rows=[]
for line in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
    item=json.loads(line).get('payload',{})
    if item.get('event')!='eex-interpreter': continue
    b=bytes(item['bytes']); out={'param1':item['param1'],'magic':b[:4].decode('ascii','replace'),
        'header_hex':b[:16].hex(),'bytes':len(b)}
    if b[:4]==b'EEX\0' and len(b)>=16:
        out.update(header_u16=[struct.unpack_from('<H',b,i)[0] for i in (4,6,8,10,12,14)],
                  cursor_candidate_u16=struct.unpack_from('<H',b,14)[0] if len(b)>=16 else None,
                  first_body_u16=struct.unpack_from('<H',b,16)[0] if len(b)>=18 else None)
    rows.append(out)
print(json.dumps(rows,ensure_ascii=False,indent=2))
print(f'parsed EEX interpreter snapshots: {len(rows)}')
