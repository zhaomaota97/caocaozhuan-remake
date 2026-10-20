"""Audit the sparse 0x800-word E-partition tail without assigning business names."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def runs(indices):
    if not indices:
        return []
    result = []
    start = previous = indices[0]
    for value in indices[1:]:
        if value != previous + 1:
            result.append([start, previous])
            start = value
        previous = value
    result.append([start, previous])
    return result

docs = [json.loads(p.read_text(encoding='utf-8'))
        for p in sorted((ROOT / 'analysis' / 'runtime-game').glob('SV*E.E5S.json'))]
rows = []
for doc in docs:
    values = doc['values2038']
    nonzero = [i for i, value in enumerate(values) if value != 0]
    rows.append({
        'file': doc['file'],
        'count': len(values),
        'distinctValues': sorted(set(values)),
        'nonzeroCount': len(nonzero),
        'nonzeroIndices': nonzero,
        'nonzeroRuns': runs(nonzero),
        'tail2038': doc['tail2038'],
        'tail203c': doc['tail203c'],
        'auxUint16': doc['auxUint16'],
    })

sets = [set(row['nonzeroIndices']) for row in rows]
result = {
    'format': 'E.E5S tail 0x2038 word table',
    'evidenceFunction': '0x417A54',
    'files': rows,
    'commonNonzeroIndices': sorted(set.intersection(*sets)),
    'unionNonzeroIndices': sorted(set.union(*sets)),
    'interpretation': 'Sparse per-slot integer/flag table; values are observed only and are not assigned semantic names.',
}
(ROOT / 'analysis' / 'e-partition-tail-audit.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('audited', len(rows), 'files;', 'union', len(result['unionNonzeroIndices']),
      'common', len(result['commonNonzeroIndices']))
