"""Inventory explicit switch cases from the saved Ghidra dispatcher."""
import json
import re
from pathlib import Path

root = Path('analysis/native-main/pseudocode')
source = (root / '004109ef.c').read_text()
matches = list(re.finditer(r'case (0x[0-9a-f]+|[0-9]+):', source))
rows = []
for i, match in enumerate(matches):
    block = source[match.end():matches[i+1].start() if i+1 < len(matches) else source.index('default:')]
    handler = re.search(r'FUN_([0-9a-f]{8})\(', block)
    address = handler[1] if handler else None
    body = (root / (address + '.c')).read_text() if address else ''
    tags = [int(value, 0) for value in re.findall(r'FUN_004183f7\([^,\n]+,(0x[0-9a-f]+|[0-9]+)\)', body)]
    rows.append({'opcode': int(match[1], 0), 'handler': address,
                 'parameter_tag_calls_in_source_order': tags,
                 'warning': 'tag calls are static observations; branches and loops may change runtime order'})
Path('analysis/eex-handlers.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
print('cases', len(rows), 'handlers', sum(r['handler'] is not None for r in rows))
