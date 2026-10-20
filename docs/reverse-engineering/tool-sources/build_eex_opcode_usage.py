"""Count opcode occurrences in decoded EEX bodies."""
import json,csv
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
counts=defaultdict(int);files=defaultdict(set)
def walk_nodes(block):
    for node in block.get('nodes',[]):
        yield node
        if 'condition' in node:
            yield node['condition']
        if 'body' in node:
            yield from walk_nodes(node['body'])
source_files=sorted(p for p in (ROOT/'analysis/eex-bodies').glob('*.json') if p.name!='summary.json')
terminators=branches=0
for p in source_files:
    segments=json.loads(p.read_text(encoding='utf-8'))
    for segment in segments:
        branches+=1
        for node in walk_nodes(segment):
            op=node.get('opcode')
            if op is None:continue
            if op==0:
                terminators+=1
                continue
            counts[op]+=1;files[op].add(p.name)
index=list(csv.DictReader((ROOT/'analysis/eex/opcode-index.csv').open(encoding='utf-8-sig')))
rows=[]
for row in index:
    op=int(row['opcode']);rows.append({'opcode':op,'handler':row['handler'] or None,'classification':row['classification'],'occurrences':counts[op],'files':len(files[op])})
summary=json.loads((ROOT/'analysis/eex-bodies/summary.json').read_text(encoding='utf-8'))
assert branches==summary['bodies'], (branches,summary['bodies'])
assert set(counts)<=set(int(row['opcode']) for row in index)
out={'sourceFiles':len(source_files),'bodies':branches,'includesNestedConditions':True,'totalOpcodes':len(rows),'usedOpcodes':sum(r['occurrences']>0 for r in rows),'unusedOpcodes':sum(r['occurrences']==0 for r in rows),'terminatorCount':terminators,'rows':rows}
(ROOT/'analysis/eex-opcode-usage.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
lines=['# EEX opcode usage','',f"Scanned {len(source_files)} files and {branches} bodies, including nested conditions and bodies. Used slots: {out['usedOpcodes']}; absent slots: {out['unusedOpcodes']}. Opcode 0 terminators are counted separately; opcode 1 is structural conditional control.",'', 'Earlier counts of 37 used / 71 absent were invalid: they included only R_ files and omitted nested blocks.','', '| Opcode | Handler | Occurrences | Files |','|---:|---|---:|---:|']
for r in sorted(rows,key=lambda x:(-x['occurrences'],x['opcode'])):
    lines.append(f"| {r['opcode']} | `{r['handler'] or '-'}` | {r['occurrences']} | {r['files']} |")
(ROOT/'analysis/eex-opcode-usage.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f"EEX usage: {out['usedOpcodes']} used, {out['unusedOpcodes']} unused")
