"""Summarize EEX handlers by static parameter/global/call fingerprints."""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = json.loads((ROOT / 'analysis/eex-handler-semantics.json').read_text(encoding='utf-8'))
clusters = defaultdict(list)
for row in rows:
    key = (row.get('classification',''), row.get('parameter_tags',''),
           tuple(row.get('suspected_global_writes',[])))
    clusters[key].append(row['opcode'])
result = []
for (classification,tags,writes), opcodes in sorted(clusters.items(), key=lambda item:min(item[1])):
    result.append({'classification':classification,'parameterTags':tags,
                   'globalWrites':list(writes),'opcodes':sorted(opcodes)})
out={'handlerCount':len(rows),'clusterCount':len(result),'clusters':result,
     'method':'static fingerprint only; cluster membership is not a runtime semantic claim'}
(ROOT/'analysis/eex-static-clusters.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# EEX static handler clusters','',f"Handlers: `{len(rows)}`; clusters: `{len(result)}`.",'',
       '| Classification | Parameter tags | Global writes | Opcodes |','|---|---|---|---|']
for c in result:
    lines.append(f"| `{c['classification']}` | `{c['parameterTags']}` | `{', '.join(c['globalWrites'])}` | `{', '.join(map(str,c['opcodes']))}` |")
lines += ['', 'Clusters are static fingerprints and do not replace dynamic story evidence.']
(ROOT/'analysis/eex-static-clusters.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f'EEX static clusters: {len(result)}')
