"""Load actual common save records and query all 17 consumable counts natively."""
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid)
    script=session.create_script('''
rpc.exports={capture(bytes){
 const b=Process.mainModule.base,obj=Memory.alloc(0x400),input=Memory.alloc(bytes.length);obj.writeByteArray(new Uint8Array(0x400));input.writeByteArray(bytes);
 const load=new NativeFunction(b.add(0xcc65),'pointer',['pointer','pointer'],'thiscall');
 const query=new NativeFunction(b.add(0xdb3e),'uint8',['pointer','uint8'],'thiscall');
 const end=load(obj,input);
 return {consumed:end.sub(input).toInt32(),stock:Array.from({length:17},(_,i)=>query(obj,87+i))};
}};
''');script.load();rows=[]
    for slot in range(10):
        path=ROOT/f'Sv{slot:02d}d.e5s';raw=path.read_bytes()
        native=script.exports_sync.capture(list(raw[0x32:0x2da]))
        expected=list(raw[0x32+637:0x32+654])
        if native['stock']!=expected or native['consumed']!=654:raise RuntimeError(dict(slot=slot,native=native,expected=expected))
        rows.append(dict(slot=slot,file=path.name,stock=native['stock'],nativeConsumed=native['consumed']))
    result=dict(scope='actual saved common records loaded by 0x40CC65 and queried by 0x40DB3E; not initial campaign inventory',stockFileOffset=0x32+637,firstItemId=87,count=17,rows=rows)
    text=json.dumps(result,indent=2)+'\n'
    (ROOT/'analysis/saved-consumable-stock.json').write_text(text,encoding='utf-8')
    (ROOT.parent/'caocaozhuan-remake/data/saves/consumable-stock.json').write_text(text,encoding='utf-8')
    print(f'Native saved consumable stocks: {len(rows)}/10 saves, 170/170 counts; offset {0x32+637:#x}')
finally:
    device.kill(pid)
    if session:session.detach()
