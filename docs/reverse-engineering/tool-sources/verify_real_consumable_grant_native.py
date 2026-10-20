"""Run native consumable grants with original DATA definitions and price getter."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(bytes){
 const b=Process.mainModule.base,obj=Memory.alloc(0x400),input=Memory.alloc(bytes.length);input.writeByteArray(bytes);
 const load=new NativeFunction(b.add(0xc537),'pointer',['pointer','pointer'],'thiscall');
 const grant=new NativeFunction(b.add(0xda45),'uint8',['pointer','uint8'],'thiscall');
 const money=new NativeFunction(b.add(0xe1d0),'int',['pointer'],'fastcall');
 const setMoney=new NativeFunction(b.add(0xe1a0),'void',['pointer','int'],'thiscall');
 const rows=[];
 for(let id=87;id<=103;id++){
  load(b.add(0xa1140+id*25),input.add(id*25));
  for(const count of [0,1,98,99,100,255])for(const initialMoney of [0,999998,999999]){
   obj.writeByteArray(new Uint8Array(0x400));obj.add(0x26b+id-87).writeU8(count);setMoney(obj,initialMoney);
   const returned=grant(obj,id);rows.push({id,count,initialMoney,returned,stock:obj.add(0x26b+id-87).readU8(),money:money(obj)});
  }
 }
 return rows;
}};
''');script.load();raw=dict(entries(ROOT/'Data.e5'))[1];rows=script.exports_sync.capture(list(raw))
    for row in rows:
        price_byte=raw[row['id']*25+0x13];price=65535 if price_byte==255 else price_byte*75
        room=row['count']<99
        row['match']=row['stock']==(row['count']+1 if room else row['count']) and row['returned']==(row['count']+1 if room else 0) and row['money']==(row['initialMoney'] if room else min(999999,row['initialMoney']+price))
    result=dict(total=len(rows),passed=sum(row['match'] for row in rows),rows=rows,scope='native original DATA loader, 0x40DA45 grant, real price getter and money writes; no patched leaf functions; isolated common object')
    text=json.dumps(result,indent=2)+'\n'
    (ROOT/'analysis/native-real-consumable-grant.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-real-consumable-grant.json').write_text(text,encoding='utf-8')
    print(f'Native original-item consumable grants: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(row for row in rows if not row['match']))
finally:
    device.kill(pid)
    if session:session.detach()
