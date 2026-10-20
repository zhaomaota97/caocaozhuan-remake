import json,sys
from pathlib import Path

folder=Path(sys.argv[1])
event=next(json.loads(l).get('payload',{}) for l in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()
           if json.loads(l).get('payload',{}).get('event')=='eex-interpreter')
live=bytes(event['bytes'])
matches=[]
for path in sorted(Path('.').glob('*.eex')):
    if path.read_bytes().startswith(live): matches.append(path.name)
print('matching files:', matches)
if matches != ['R_00.eex']: raise SystemExit(1)
print('live EEX file match: R_00.eex / 128-byte prefix')
