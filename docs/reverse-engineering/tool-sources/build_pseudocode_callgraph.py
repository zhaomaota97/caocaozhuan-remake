"""Build a conservative call graph from Ghidra pseudocode references."""
from pathlib import Path
import json
import re
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'analysis/native-main/pseudocode'
defined={}
edges=defaultdict(set)
for p in src.glob('*.c'):
    text=p.read_text(encoding='utf-8',errors='ignore')
    m=re.search(r'Address:\s*(004[0-9a-fA-F]{5})',text[:300]) or re.search(r'(004[0-9a-fA-F]{5})',p.name)
    if not m:
        continue
    caller='0x'+m.group(1).lower()
    defined[caller]=p.name
    for ref in re.findall(r'FUN_([0-9A-Fa-f]{8})',text):
        callee='0x'+ref.lower()
        if callee!=caller:
            edges[caller].add(callee)
nodes=set(defined)|set(v for vs in edges.values() for v in vs)
out={'definedCount':len(defined),'nodeCount':len(nodes),'edgeCount':sum(map(len,edges.values())),'defined':defined,'edges':{k:sorted(v) for k,v in sorted(edges.items())}}
(ROOT/'analysis/native-pseudocode-callgraph.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
rank=sorted(((len(v),k) for k,v in edges.items()),reverse=True)
lines=['# Static pseudocode call graph','',f"Defined functions: {len(defined)}; nodes: {len(nodes)}; edges: {out['edgeCount']}.",'', 'The graph is conservative: it only records literal `FUN_XXXXXXXX` references in Ghidra pseudocode. Indirect calls, callbacks and unresolved imports are absent.','', '## Most connected callers','']
for count,node in rank[:40]:
    lines.append(f"- `{node}` -> {count} referenced functions")
(ROOT/'analysis/native-pseudocode-callgraph.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f'Callgraph: {len(defined)} defined, {len(nodes)} nodes, {out["edgeCount"]} edges')
