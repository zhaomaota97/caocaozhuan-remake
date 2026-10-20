#!/usr/bin/env python3
import json,sys
from pathlib import Path
if len(sys.argv)!=2: raise SystemExit('usage: summarize_story_message_timeline.py events.jsonl')
rows=[]; counts={}
for i,line in enumerate(Path(sys.argv[1]).read_text(encoding='utf-8').splitlines()):
 try: p=json.loads(line).get('payload',{})
 except: continue
 ev=p.get('event')
 if ev=='window-message-api' and p.get('message') in (641,642):
  rows.append({'line':i,'kind':f"message-{p['message']}",'hwnd':p.get('hwnd'),'wparam':p.get('wparam'),'lparam':p.get('lparam')})
 elif ev in ('eex-interpreter','eex-interpreter-return','eex-dispatch'):
  rows.append({'line':i,'kind':ev})
print(json.dumps({'events':len(rows),'message_641':sum(x['kind']=='message-641' for x in rows),'message_642':sum(x['kind']=='message-642' for x in rows),'timeline':rows[:200]},ensure_ascii=False,indent=2))
