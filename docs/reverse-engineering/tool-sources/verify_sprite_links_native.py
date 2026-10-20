"""Export and differential-check unit/class/side to animation-resource indices."""
import csv
import json
import struct
from pathlib import Path
import frida
from extract_e5 import decode

ROOT=Path(__file__).resolve().parents[1]
CLASS_SPRITES=[5,5,5,0,1,2,6,7,8,3,4,5,9,10,11,18,19,20,12,13,14,
               15,16,17,21,22,23,24,25,26,27,28,29,23,23,23,14,14,14,
               33,34,32,31,30,23,23,39,35,36,37,38,68,69]
FIXED={34:59,35:56,170:56,171:56,172:56,173:56,72:79,76:60,77:63,81:65,
       99:60,100:60,101:67,119:66,149:68,162:82,169:82,163:80,164:81,
       165:64,166:61,167:61,168:61}
PROMOTED={0:40,1:43,2:46,15:73,16:70,17:49,19:52}


def base_sprite(uid,cls):
    tier=cls%3
    if uid in PROMOTED:return PROMOTED[uid]+tier
    if uid==3:return 57 if tier==0 else 77
    if uid==32:return 76 if tier==0 else 55
    if uid==33:return 58 if tier==0 else 78
    return FIXED.get(uid,CLASS_SPRITES[cls] if cls<53 else 69)


def main():
    data=(ROOT/'Data.e5').read_bytes()
    packed,size,offset=struct.unpack_from('>III',data,0x110)
    raw=decode(data,offset,packed,size)
    if len(raw)!=512*32:raise ValueError('Unexpected unit table size')
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(bytes){
  const b=Process.mainModule.base,source=Memory.alloc(bytes.length);
  source.writeByteArray(bytes);
  const expand=new NativeFunction(b.add(0x8be3),'pointer',
    ['pointer','uint16','pointer','int'],'thiscall');
  const select=new NativeFunction(b.add(0x3fc48),'uint',['pointer'],'fastcall');
  const actor=Memory.alloc(0x24);actor.writeByteArray(new Uint8Array(0x24));
  const rows=[];
  for(let uid=0;uid<512;uid++){
    const unit=b.add(0xa1b68+uid*72);
    unit.writeByteArray(new Uint8Array(72));
    expand(unit,uid,source.add(uid*32),0);actor.writeU32(uid);
    for(const side of [0,1,2,3,255]){
      actor.add(5).writeU8(side);
      rows.push({uid,side,index:select(actor)&255});
    }
  }
  return rows;
}};
''')
        script.load();rows=script.exports_sync.verify(list(raw))
        for row in rows:
            record=raw[row['uid']*32:(row['uid']+1)*32]
            cls=record[26];base=base_sprite(row['uid'],cls)
            wanted=base*3+min(row['side'],2) if base<34 else base+68
            row.update(name=record[:12].split(b'\0',1)[0].decode('gbk',errors='replace'),
                       class_id=cls,base_sprite=base,expected=wanted,match=row['index']==wanted)
        with (ROOT/'analysis/unit-animation-links.csv').open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        result=dict(records=len(rows),matched=sum(r['match'] for r in rows),
                    archive_entries=151,all_indices_in_range=all(r['index']<151 for r in rows),
                    failures=[r for r in rows if not r['match']])
        (ROOT/'analysis/native-sprite-links-validation.json').write_text(
            json.dumps(result,indent=2),encoding='utf-8')
        print(f'Native sprite links: {result["matched"]}/{len(rows)}; '
              f'all within 151-entry archives: {result["all_indices_in_range"]}')
        if len(rows)!=2560 or result['failures'] or not result['all_indices_in_range']:
            raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
