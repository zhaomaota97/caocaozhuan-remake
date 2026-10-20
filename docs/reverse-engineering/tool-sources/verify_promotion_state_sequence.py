"""Execute promotion numerical helper sequence with original class growth table."""
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
 const b=Process.mainModule.base,input=Memory.alloc(bytes.length);input.writeByteArray(bytes);
 const load=new NativeFunction(b.add(0x93ef),'pointer',['pointer','pointer'],'thiscall');
 const growth=new NativeFunction(b.add(0x95a0),'uint',['pointer','int'],'thiscall');
 const increase=new NativeFunction(b.add(0x6e17),'void',['pointer','uint8','int'],'thiscall');
 const change=new NativeFunction(b.add(0xdff0),'void',['pointer','uint8'],'thiscall');
 const u=Memory.alloc(72),rows=[],classes=[];let cursor=input;
 for(let id=0;id<53;id++){
  const c=b.add(0xabfa0+id*27);cursor=load(c,cursor);const hpGrowth=growth(c,5)&255,mpGrowth=growth(c,6)&255;classes.push({id,hpGrowth,mpGrowth});
  for(const hp of [10,499,500])for(const mp of [10,249,250]){
   u.writeByteArray(new Uint8Array(72));u.add(43).writeU8(id);u.add(28).writeU32(hp);u.add(32).writeU8(mp);
   increase(u,5,(hpGrowth*2)&255);increase(u,6,(mpGrowth*2)&255);change(u,(id+1)&255);
   rows.push({classId:id,hp,mp,finalClass:u.add(43).readU8(),finalHp:u.add(28).readU32(),finalMp:u.add(32).readU8()});
  }
 }
 return {classes,rows};
}};
''');script.load();result=script.exports_sync.capture(list(dict(entries(ROOT/'Data.e5'))[3]))
    for r in result['rows']:
        c=result['classes'][r['classId']]
        r['match']=r['finalClass']==r['classId']+1 and r['finalHp']==min(500,r['hp']+((c['hpGrowth']*2)&255)) and r['finalMp']==min(250,r['mp']+((c['mpGrowth']*2)&255))
    result.update(total=len(result['rows']),passed=sum(r['match'] for r in result['rows']),scope='native helper sequence reconstructed from 0x41D4DB, original class loader/growth/increase/class setter; NOT full controller; invalid promotion classes included for helper boundaries')
    text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/native-promotion-state-sequence.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-promotion-state-sequence.json').write_text(text,encoding='utf-8')
    print(f'Native promotion numeric sequence: {result["passed"]}/{result["total"]}')
    if result['passed']!=result['total']:raise RuntimeError(next(r for r in result['rows'] if not r['match']))
finally:
    device.kill(pid)
    if session:session.detach()
