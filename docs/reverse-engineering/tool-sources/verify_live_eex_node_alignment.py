#!/usr/bin/env python3
"""Match live dispatcher instruction pointers to decoded R_00 EEX node offsets."""
import json,struct,sys
from pathlib import Path
if len(sys.argv)!=2: raise SystemExit('usage: verify_live_eex_node_alignment.py events.jsonl')
events=[]
for line in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
 try:
  p=json.loads(line).get('payload',{})
  if p.get('event')=='eex-dispatch' and p.get('arg0_bytes') and p.get('arg0')=='0x492f90': events.append(p)
 except: pass
nodes=json.loads((Path(__file__).resolve().parents[1]/'analysis/eex-bodies/R_00.json').read_text(encoding='utf-8'))
offsets={n['offset']:n['opcode'] for seg in nodes for n in seg.get('nodes',[])}
base_ptr=0
for line in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
 try:
  p=json.loads(line).get('payload',{})
  if p.get('event')=='eex-interpreter-return': base_ptr=int(p['param1'],16); break
 except: pass
matches=[]
for e in events:
 b=bytes(e['arg0_bytes']); ptr=struct.unpack_from('<I',b,12)[0]
 off=ptr-base_ptr
 matches.append({'return_address':e.get('return_address'),'cursor_field':struct.unpack_from('<I',b,8)[0], 'cursor_ptr':hex(ptr),'offset':off,'opcode':offsets.get(off),'node_match':off in offsets})
node_matches=[x for x in matches if x['node_match']]
header_matches=[x for x in matches if x['offset'] in (18,47)]
print(json.dumps({'base_ptr':hex(base_ptr),'dispatch_nodes':matches,'matched':len(node_matches),'total_nodes':len(node_matches),'header_records':len(header_matches)},ensure_ascii=False,indent=2))
if not node_matches or len(node_matches) != len(matches)-len(header_matches): raise SystemExit(1)
