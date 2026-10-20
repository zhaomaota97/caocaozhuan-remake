"""Export the 53 class-growth records loaded at 0x41b72f."""
import csv
import struct
from pathlib import Path
from extract_e5 import decode

data = Path('Data.e5').read_bytes()
packed, size, offset = struct.unpack_from('>III', data, 0x110+3*12)
raw = decode(data, offset, packed, size)
assert len(raw) == 53*27
with Path('analysis/class-growth.csv').open('w', encoding='utf-8-sig', newline='') as stream:
    writer = csv.writer(stream)
    writer.writerow(['class_id']+[f'growth_{i}' for i in range(7)]+['raw_hex'])
    for i in range(53):
        record = raw[i*27:(i+1)*27]
        writer.writerow([i, *record[2:9], record.hex(' ')])
print('53 class growth records exported')
