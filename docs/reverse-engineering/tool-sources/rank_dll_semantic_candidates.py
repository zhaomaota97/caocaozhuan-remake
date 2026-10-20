"""Rank DLL functions that are most useful for future runtime semantic tracing."""
import csv, json
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((ROOT/'analysis/dll-calls.csv').open(encoding='utf-8-sig')))
inv = json.loads((ROOT/'analysis/dll-rizin-inventory.json').read_text(encoding='utf-8'))
out = {}
for mod in inv:
    name = mod['file']; rr = [r for r in rows if r['dll'] == name]
    incoming = Counter(r['callee'].lower() for r in rr)
    outgoing = Counter(r['caller'].lower() for r in rr)
    known = {f"0x{x['address']:x}" for x in mod['functions']}
    candidates = []
    for f in mod['functions']:
        key = f"0x{f['address']:x}".lower()
        # High fan-in and fan-out are useful trace points; keep the score transparent.
        fan_in, fan_out = incoming[key], outgoing[key]
        if fan_in or fan_out:
            candidates.append({'address': key, 'name': f['name'], 'size': f['size'],
                               'fanIn': fan_in, 'fanOut': fan_out,
                               'score': fan_in * 3 + fan_out})
    candidates.sort(key=lambda x: (-x['score'], -x['fanIn'], x['address']))
    out[name] = {'functionCount': len(mod['functions']), 'rankedCandidates': candidates[:25]}
(ROOT/'analysis/dll-semantic-candidates.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8')
lines = ['# DLL semantic tracing candidates', '', 'Ranking is derived only from direct call edges: `score = 3*fanIn + fanOut`. It identifies high-value runtime trace points and does not assign speculative business names.', '']
for name, data in out.items():
    lines += [f'## {name}', '', '| Address | Size | Fan-in | Fan-out | Score |', '|---|---:|---:|---:|---:|']
    for x in data['rankedCandidates'][:10]:
        lines.append(f"| `{x['address']}` | {x['size']} | {x['fanIn']} | {x['fanOut']} | {x['score']} |")
    lines.append('')
(ROOT/'analysis/dll-semantic-candidates.md').write_text('\n'.join(lines), encoding='utf-8')
print('ranked', sum(len(x['rankedCandidates']) for x in out.values()), 'candidate rows')
