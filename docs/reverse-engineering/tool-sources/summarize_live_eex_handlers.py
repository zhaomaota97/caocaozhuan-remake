#!/usr/bin/env python3
import json,sys,collections
from pathlib import Path
if len(sys.argv)!=2: raise SystemExit('usage: summarize_live_eex_handlers.py events.jsonl')
c=collections.Counter(); samples={}; errors=collections.Counter()
for l in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
 try: p=json.loads(l).get('payload',{})
 except: continue
 if p.get('event')=='eex-handler': c[(p.get('opcode'),p.get('handler_rva'))]+=1; samples.setdefault((p.get('opcode'),p.get('handler_rva')),p)
 if p.get('event')=='eex-handler-error': errors[p.get('handler_rva')]+=1
print(json.dumps({'handlers':[{'opcode':k[0],'handler_rva':k[1],'calls':n,'sample':samples[k]} for k,n in c.most_common()],'errors':dict(errors)},ensure_ascii=False,indent=2))
