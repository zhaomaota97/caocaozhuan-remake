import json,sys,struct
from pathlib import Path

path=Path(sys.argv[1])
for line in path.read_text(encoding='utf-8').splitlines():
    p=json.loads(line).get('payload',{})
    if p.get('event') not in {'eex-interpreter','eex-interpreter-return'}: continue
    key='bytes' if p['event']=='eex-interpreter' else 'this_bytes'
    b=bytes(p[key])
    fields={hex(i):hex(struct.unpack_from('<I',b,i)[0]) for i in range(0,min(0x34,len(b)),4)}
    extra=''
    if p.get('state_bytes'):
        sb=bytes(p['state_bytes']); ptrs=[hex(struct.unpack_from('<I',sb,i)[0]) for i in range(0,min(32,len(sb)),4)]
        extra=' state_ptrs='+','.join(ptrs)
    print(p['event'], 'this/param=',p.get('this_ecx',p.get('param1')), fields, extra)
