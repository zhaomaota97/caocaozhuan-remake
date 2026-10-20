"""Report byte offsets that differ across the three save partitions."""
from pathlib import Path
import sys

def main():
    names = sorted(Path('.').glob('Sv??s.e5s'))
    blobs = [p.read_bytes() for p in names]
    if not blobs: raise SystemExit('no Sv??s.e5s files')
    for off in range(len(blobs[0])):
        vals = {b[off] for b in blobs}
        if len(vals) > 1:
            print(f"0x{off:04X} " + ' '.join(f'{b[off]:02X}' for b in blobs))

if __name__ == '__main__': main()
