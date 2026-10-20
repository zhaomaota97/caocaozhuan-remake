from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
base = ROOT / 'analysis/full-extract-56219569-d002-44b4-8b5f-56cb66adac39/Data'
expected = {6:(8704,17,512),7:(1768,17,104),8:(1156,17,68),9:(1218,21,58)}
for index,(size,width,rows) in expected.items():
    data=(base/f'resource_{index:04d}.bin').read_bytes()
    nonzero=[value for value in data if value]
    ok=(len(data)==size and len(data)%width==0 and len(data)//width==rows
        and set(nonzero)=={0xD6,0xD5,0xB6,0xCB} and len(nonzero)==rows*4)
    print(f'entry_{index}: {"PASS" if ok else "FAIL"}')
    if not ok: raise SystemExit(1)
print('DATA.E5 entries 6-9 sparse-shape validation: 4/4')
