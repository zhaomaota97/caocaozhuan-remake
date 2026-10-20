"""Execute native palette container selection and nibble conversion with real resource bytes."""
import hashlib
import json
from pathlib import Path
import frida
from export_map_layouts import entries
from game_palette import color_lookup
ROOT=Path(__file__).resolve().parents[1]
cases=[]
for mode,name in enumerate(['Pmpalet.e5','Spalet.e5','Logo_p.e5']):
 raw=next(raw for i,raw in entries(ROOT/name) if i==0)
 assert len(raw)<=768
 cases.append(dict(mode=mode,file=name,opened=True,bytes=list(raw)))
cases.extend([dict(mode=0,file='Pmpalet.e5',opened=False,bytes=cases[0]['bytes']),dict(mode=3,file=None,opened=True,bytes=[])])
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(cases){
 const b=Process.mainModule.base,keep=[],rows=[];let current=null,events=[];
 const open=new NativeCallback((_obj,name)=>{events.push({kind:'open',file:name.readCString()});return current.opened?1:0;},'uint',['pointer','pointer'],'thiscall');
 const load=new NativeCallback((_obj,index,dst)=>{events.push({kind:'load',index});dst.writeByteArray(current.bytes);return 1;},'uint',['pointer','uint','pointer'],'thiscall');
 keep.push(open,load);Interceptor.replace(b.add(0x1fb35),open);Interceptor.replace(b.add(0x1fc89),load);Interceptor.flush();
 const controller=new NativeFunction(b.add(0x1e050),'void',['uint','int8'],'mscdecl');
 for(const c of cases){current=c;events=[];b.add(0xbd044).writeU32(0);b.add(0x97770).writeByteArray(new Uint8Array(768).fill(0xa5));b.add(0xb1b28).writeByteArray(new Uint8Array(4096).fill(0xa5));controller(0,c.mode);
  rows.push({mode:c.mode,opened:c.opened,events,pixelMode:b.add(0xb88b8).readU32(),palette:Array.from(new Uint8Array(b.add(0x97770).readByteArray(768))),lookup:Array.from(new Uint8Array(b.add(0xb1b28).readByteArray(4096)))});
 }
 return rows;
}};''');script.load();rows=script.exports_sync.verify(cases)
 for case,row in zip(cases,rows):
  loaded=case['mode']<3 and case['opened'];expected_palette=bytes(v>>4 for v in (case['bytes']+[0xa5]*(768-len(case['bytes'])))) if loaded else bytes([0xa5])*768
  expected_lookup=color_lookup(expected_palette) if loaded else bytes([0xa5])*4096
  expected_events=[] if case['mode']==3 else [dict(kind='open',file=case['file'].upper())]
  if loaded:expected_events.append(dict(kind='load',index=0))
  events=[{**e,'file':e['file'].upper()} if e['kind']=='open' else e for e in row['events']]
  palette=bytes(row.pop('palette'));lookup=bytes(row.pop('lookup'))
  row['match']=(palette==expected_palette and lookup==expected_lookup and events==expected_events and row['pixelMode']==7)
  row['paletteSha256']=hashlib.sha256(palette).hexdigest();row['lookupSha256']=hashlib.sha256(lookup).hexdigest()
 out={'scope':'Original palette controller, nibble shift, lookup generator and pixel-mode setter; container open/read replaced with real decoded resource bytes','rows':rows,'passed':len(rows)==5 and all(r['match'] for r in rows)}
 (ROOT/'analysis/native-palette-load-controller.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(f"Native palette selection/conversion/controller: {sum(r['match'] for r in rows)}/5")
 if not out['passed']:
  print(next(row for row in rows if not row['match']));raise SystemExit(1)
finally:
 device.kill(pid)
 if session:session.detach()
