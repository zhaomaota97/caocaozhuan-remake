#!/usr/bin/env python3
"""Verify runtime EEX buffer/cursor alignment against the extracted R_00 file."""
import json, sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit('usage: verify_live_eex_alignment.py <events.jsonl>')
events = [json.loads(x) for x in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines() if x.strip()]
enters = [x['payload'] for x in events if x.get('payload', {}).get('event') == 'eex-interpreter']
returns = [x['payload'] for x in events if x.get('payload', {}).get('event') == 'eex-interpreter-return']
dispatch = [x['payload'] for x in events if x.get('payload', {}).get('event') == 'eex-dispatch']
dispatch_ret = [x['payload'] for x in events if x.get('payload', {}).get('event') == 'eex-dispatch-return']
disk = Path(__file__).resolve().parents[1] / 'R_00.eex'
raw = disk.read_bytes()
checks = []
for e in enters + returns:
    b = bytes(e.get('bytes', e.get('param_bytes', [])))
    checks.append(('runtime_prefix_matches_R_00', b == raw[:len(b)]))
    if e.get('cursor_delta', 0) > 0:
        checks.append(('cursor_delta_is_0x0e', e['cursor_delta'] == 14))
        cb = bytes(e.get('cursor_bytes', []))
        checks.append(('cursor_starts_with_header_cursor', cb[:4] == raw[14:18]))
print(json.dumps({
    'events': str(Path(sys.argv[1])), 'interpreter_enter': len(enters),
    'interpreter_return': len(returns), 'dispatcher': len(dispatch),
    'dispatcher_return': len(dispatch_ret),
    'checks': [{'name': n, 'passed': bool(v)} for n, v in checks],
    'passed': sum(bool(v) for _, v in checks), 'total': len(checks)
}, ensure_ascii=False, indent=2))
if not enters or not returns or not checks or not all(v for _, v in checks):
    raise SystemExit(1)
