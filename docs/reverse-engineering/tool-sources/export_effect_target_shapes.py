"""Export native effect geometry fields, without substituting default shapes."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = []
with (ROOT / 'analysis/effects.csv').open(encoding='utf-8-sig') as stream:
    for row in csv.DictReader(stream):
        record = bytes.fromhex(row['runtime_hex'])
        rows.append({'effectId': int(row['id']), 'name': row['name_gbk'],
                     'targetShape': record[12], 'effectShape': record[13]})
result = {'evidence': {'targetReader': '0x418C90', 'effectReader': '0x425B50',
                       'nativeCaller': '0x4391DC', 'recordStride': 70}, 'effects': rows}
destination = ROOT.parent / 'caocaozhuan-remake/data/rules/effect-target-shapes.json'
destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Exported {len(rows)} native effect geometry records')
