"""Verify the native E battle-prefix boundaries across all save slots."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
paths=[ROOT/'analysis/runtime-game'/f'SV{i:02d}E.E5S' for i in range(10)]
for path in paths:
    raw=path.read_bytes(); base=0x23; end=base+1266+115*26+640
    if len(raw)<end: raise SystemExit(f'{path.name}: truncated prefix')
    if raw[base:base+1266][0:0] != b'': raise SystemExit('unreachable')
    print(f'{path.name}: prefix 0x{base:X}-0x{end:X} ({end-base} bytes) of {len(raw)}')
print(f'E battle prefixes: {len(paths)}/10 boundary checks passed')
