#!/usr/bin/env python3
import json,sys
from pathlib import Path
if len(sys.argv)!=2: raise SystemExit('usage: verify_live_eex_handlers.py events.jsonl')
rows=[]
for l in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
 try:
  p=json.loads(l).get('payload',{})
  if p.get('event')=='eex-handler': rows.append(p)
 except: pass
checks=[]
for p in rows:
 try: checks.append({'opcode':p['opcode'],'handler_rva':p['handler_rva'],'arg1':int(p['args'][1],16),'match':int(p['args'][1],16)==p['opcode']})
 except: checks.append({'opcode':p.get('opcode'),'handler_rva':p.get('handler_rva'),'match':False})
print(json.dumps({'handlers':len(rows),'unique_opcodes':sorted({p['opcode'] for p in rows}),'checks':checks,'passed':sum(x['match'] for x in checks),'total':len(checks)},ensure_ascii=False,indent=2))
if not rows or not all(x['match'] for x in checks): raise SystemExit(1)
