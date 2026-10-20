"""Independent E-partition decoder/encoder round-trip from structured fields."""
import json,struct,sys
from pathlib import Path

def encode(doc):
 out=bytearray()
 for row in doc['records']:
  out+=struct.pack('<IBBIBHB B',row['word0'],row['byte4'],row['byte5'],row['word6'],row['byte10'],row['word11'],row['byte13'],row['byte14'])
 out+=bytes.fromhex(doc['block3d10']);out+=bytes([doc['byte3d0e'],doc['byte3d0f']]);out+=bytes.fromhex(doc['block3d04'])
 out+=b''.join(struct.pack('<I',v) for v in doc['values2038'])
 out+=struct.pack('<II',doc['tail2038'],doc['tail203c']);out+=bytes.fromhex(doc['aux10'])
 return bytes(out)
if len(sys.argv)!=2:raise SystemExit('usage: verify_e_partition_codec.py <Sv??E.e5s.json>')
jsonPath=Path(sys.argv[1]);doc=json.loads(jsonPath.read_text(encoding='utf-8'));raw=encode(doc);original=jsonPath.with_suffix('')
if raw!=original.read_bytes():raise SystemExit(f'mismatch: encoded {len(raw)} bytes for {original.name}')
print(f'{original.name}: structured E codec round-trip exact ({len(raw)} bytes)')
