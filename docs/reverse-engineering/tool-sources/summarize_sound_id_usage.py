"""Summarize native SE sound IDs by call-site role without guessing names."""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / 'analysis/native-ui-sound-calls.json').read_text(encoding='utf-8'))
rows = defaultdict(lambda: {'callers': set(), 'modes': set(), 'occurrences': 0})
for call in source.get('calls', []):
    sid = call.get('constantId')
    key = str(sid) if sid is not None else 'dynamic'
    item = rows[key]
    item['callers'].add(call.get('caller'))
    item['modes'].add(call.get('modeExpression'))
    item['occurrences'] += 1
result = {'source': 'analysis/native-ui-sound-calls.json', 'ids': []}
for sid, item in sorted(rows.items(), key=lambda pair: (pair[0] == 'dynamic', pair[0])):
    result['ids'].append({'soundId': sid, 'occurrences': item['occurrences'],
                          'callers': sorted(item['callers']), 'modes': sorted(item['modes'])})
(ROOT / 'analysis/native-sound-id-usage.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f"sound IDs summarized: {len(result['ids'])}")
