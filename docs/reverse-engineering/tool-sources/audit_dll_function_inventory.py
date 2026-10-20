"""Produce a machine-readable audit of Rizin DLL function inventories and graph coverage."""
import csv, json, hashlib
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
inventory = json.loads((ROOT / 'analysis' / 'dll-rizin-inventory.json').read_text(encoding='utf-8'))
edges = list(csv.DictReader((ROOT / 'analysis' / 'dll-calls.csv').open(encoding='utf-8-sig')))
by_module = defaultdict(list)
for edge in edges:
    by_module[edge['dll']].append(edge)
rows = []
for module in inventory:
    name = module['file']
    funcs = module['functions']
    addresses = {f"0x{fn['address']:x}" for fn in funcs}
    callers = {row['caller'] for row in by_module[name]}
    rows.append({
        'module': name,
        'functionCount': len(funcs),
        'inventoryCountMatches': len(funcs) == module['function_count'],
        'functionsWithDirectCalls': len(callers),
        'functionsWithoutDirectCalls': len(addresses - callers),
        'directEdges': len(by_module[name]),
        'functionInventorySha256': hashlib.sha256(json.dumps(funcs, sort_keys=True).encode()).hexdigest(),
    })
result = {'source': ['analysis/dll-rizin-inventory.json', 'analysis/dll-calls.csv'], 'modules': rows}
(ROOT / 'analysis' / 'dll-function-inventory-audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print('audited', len(rows), 'DLL inventories and', sum(row['functionCount'] for row in rows), 'functions')
