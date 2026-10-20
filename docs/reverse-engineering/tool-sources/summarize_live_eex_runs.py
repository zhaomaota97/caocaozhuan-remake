"""Summarize observed EEX opcodes across all bounded live runs."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
runs=[]; union={}
for path in sorted((ROOT/'analysis').glob('live-startup-*/events.jsonl')):
    ops=set()
    try:
        for line in path.open(encoding='utf-8',errors='replace'):
            try:
                event=json.loads(line); payload=event.get('payload',event)
                if payload.get('event')=='eex-handler' and payload.get('opcode') is not None:
                    op=int(payload['opcode']);ops.add(op);union.setdefault(str(op),str(path.parent.relative_to(ROOT)))
            except (ValueError,TypeError):
                continue
    except OSError:
        continue
    if ops:runs.append({'run':str(path.parent.relative_to(ROOT)),'opcodes':sorted(ops),'count':len(ops)})
result={'runCount':len(runs),'union':sorted(map(int,union)),
        'unionCount':len(union),'firstEvidence':{k:union[k] for k in sorted(union,key=lambda x:int(x))},'runs':runs}
(ROOT/'analysis/live-eex-opcode-union.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'live EEX union: {len(union)} opcodes across {len(runs)} runs')
