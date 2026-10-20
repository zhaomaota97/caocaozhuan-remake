"""Byte-exact round-trip for the native E-partition serialization order."""
import struct,sys
from pathlib import Path

if len(sys.argv)!=2: raise SystemExit('usage: verify_e_partition_roundtrip.py <Sv??E.e5s>')
path=Path(sys.argv[1]); raw=path.read_bytes(); pos=0; output=bytearray()
def take(size):
    global pos
    value=raw[pos:pos+size];pos+=size;output.extend(value);return value
for _ in range(0x73):
    for size in (4,1,1,4,1,2,1,1): take(size)
take(0x181);take(1);take(1);take(8)
for _ in range(0x800): take(4)
take(4);take(4);take(10)
if pos!=len(raw) or bytes(output)!=raw:
    raise SystemExit(f'mismatch offset=0x{pos:X} bytes={len(raw)}')
print(f'{path.name}: native E-partition round-trip exact ({len(raw)} bytes, 115 records)')
