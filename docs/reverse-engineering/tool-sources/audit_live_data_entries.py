"""Summarize DATA.E5 indices observed by a real GUI startup trace."""
import json,sys
from pathlib import Path

if __name__=='__main__':
    path=Path(sys.argv[1]); rows=[]
    for line in (path/'events.jsonl').read_text(encoding='utf-8').splitlines():
        item=json.loads(line).get('payload',{})
        if item.get('event')=='resource-entry' and str(item.get('container','')).upper()=='DATA.E5':rows.append(item['index'])
    result=dict(trace=str(path),requested=sorted(set(rows)),request_count=len(rows),
                not_requested=[i for i in range(10) if i not in rows])
    (path/'data-entry-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(result)
