"""Summarize the existing Rizin DLL call-edge extraction."""
import csv,json
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((ROOT/'analysis/dll-calls.csv').open(encoding='utf-8-sig')))
inv={x['file']:x for x in json.loads((ROOT/'analysis/dll-rizin-inventory.json').read_text(encoding='utf-8'))}
stats={}
for module in sorted(inv):
 r=[x for x in rows if x['dll']==module]; callers={x['caller'] for x in r};callees={x['callee'] for x in r}
 known={f'0x{f["address"]:x}' for f in inv[module]['functions']}
 internal=sum(1 for x in r if x['callee'].lower() in known)
 stats[module]={'functions':inv[module]['function_count'],'edges':len(r),'callers':len(callers),'callees':len(callees),
                'internalEdges':internal,'externalOrUnresolvedEdges':len(r)-internal}
(ROOT/'analysis/dll-callgraph-summary.json').write_text(json.dumps(stats,indent=2)+'\n',encoding='utf-8')
lines=['# DLL static callgraph summary','', 'Source: `analysis/dll-calls.csv` generated from Rizin disassembly. Addresses are module virtual addresses.','', '| Module | Functions | Edges | Caller nodes | Callee nodes | Internal | External/unresolved |','|---|---:|---:|---:|---:|---:|---:|']
for n,s in stats.items():lines.append(f"| `{n}` | {s['functions']} | {s['edges']} | {s['callers']} | {s['callees']} | {s['internalEdges']} | {s['externalOrUnresolvedEdges']} |")
lines += ['', '## Interpretation','', '- The four icon/map DLLs share identical `.text` and are resource variants; their repeated edges are common loader/window code.', '- `AutoDLL.dll` has an independent 108-function graph and the exported `ASave` jump bridge documented separately.', '- `Koeicda.dll` has its own exported audio wrapper surface; the CSV is a static edge inventory, not proof of playback timing.', '- These edges are direct disassembly calls only. Indirect calls, imported API behavior and runtime callback edges are not represented.']
(ROOT/'analysis/dll-callgraph-summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f'Summarized {len(stats)} DLL graphs, {len(rows)} edges')
