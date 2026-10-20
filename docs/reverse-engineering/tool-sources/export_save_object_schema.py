#!/usr/bin/env python3
"""Emit the native 0x20-byte save-object <-> 0x48-byte runtime mapping."""
import csv
from pathlib import Path

rows = []
def add(disk, runtime, width, note):
    rows.append((disk, runtime, width, note))
add('0x00..0x01', '0x04', 2, 'little-endian uint16')
add('0x02', '0x02', 1, 'byte')
add('0x03', '0x2A', 1, 'byte')
add('0x04..0x08', '0x15..0x19', 5, 'five bytes')
add('0x09..0x0D', '0x21..0x25', 5, 'five bytes')
add('0x0E..0x0F', '0x1C', 2, 'little-endian uint16')
add('0x10', '0x20', 1, 'byte')
add('0x11', '0x2B', 1, 'byte')
add('0x12..0x13', '0x2C..0x2D', 2, 'two bytes')
add('0x14..0x1C', '0x2E..0x36', 9, 'three 3-byte slot records')
add('0x1D..0x1F', '0x27..0x29', 3, 'three bytes')
if sum(row[2] for row in rows) != 0x20:
    raise ValueError('Schema widths must cover exactly 32 serialized bytes')
out = Path(__file__).resolve().parents[1] / 'analysis' / 'save-object-schema.csv'
with out.open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['disk_range','runtime_range','width','encoding']); w.writerows(rows)
print(f'wrote {out}')
