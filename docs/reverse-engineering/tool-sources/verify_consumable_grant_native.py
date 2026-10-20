"""Probe original consumable grant cap and overflow-money branch."""
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(){
 const b=Process.mainModule.base,obj=Memory.alloc(0x400);let price=10;
 const priceLeaf=new NativeCallback(()=>price,'uint',['pointer','int'],'thiscall');Interceptor.replace(b.add(0xc7a9),priceLeaf);Interceptor.flush();
 const grant=new NativeFunction(b.add(0xda45),'uint8',['pointer','uint8'],'thiscall');
 const money=new NativeFunction(b.add(0xe1d0),'int',['pointer'],'fastcall');
 const setMoney=new NativeFunction(b.add(0xe1a0),'void',['pointer','int'],'thiscall');
 const rows=[];
 for(let id=87;id<=103;id++)for(const count of [0,1,98,99,100,255])for(const initialMoney of [0,999998,999999])for(const value of [0,10,255]){
  obj.writeByteArray(new Uint8Array(0x400));obj.add(0x26b+id-87).writeU8(count);setMoney(obj,initialMoney);price=value;
  const returned=grant(obj,id);rows.push({id,count,initialMoney,price:value,returned,stock:obj.add(0x26b+id-87).readU8(),money:money(obj)});
 }
 return rows;
}};
''');script.load();rows=script.exports_sync.capture()
    for row in rows:
        room=row['count']<99
        row['match']=row['stock']==(row['count']+1 if room else row['count']) and row['returned']==(row['count']+1 if room else 0) and row['money']==(row['initialMoney'] if room else min(999999,row['initialMoney']+row['price']))
    result=dict(total=len(rows),passed=sum(row['match'] for row in rows),rows=rows,scope='native 0x40DA45/0x40DAD3 stock and money writes; item resale-price getter controlled; not complete opcode61 dispatch')
    text=json.dumps(result,indent=2)+'\n'
    (ROOT/'analysis/native-consumable-grant.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-consumable-grant.json').write_text(text,encoding='utf-8')
    print(f'Native consumable grant: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(row for row in rows if not row['match']))
finally:
    device.kill(pid)
    if session:session.detach()
