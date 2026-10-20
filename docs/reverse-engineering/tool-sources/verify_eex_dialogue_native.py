"""Check native dialogue parsing with actual tagged strings and recorded UI leaves."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
cases=[
 dict(name='narration',condition=0,text='曹操',expected=[['plain',65535,'曹操']],ret=1),
 dict(name='battle-narration',condition=1,text='曹操',expected=[['plain',65535,'曹操']],ret=1),
 dict(name='actor-speaker',condition=1,text='&03\n曹操',expected=[['portrait',99,'曹操']],ret=1),
 dict(name='multiple-speakers',condition=1,text='&03\n曹操\n&04\n夏侯惇',expected=[['portrait',99,'曹操'],['portrait',100,'夏侯惇']],ret=1),
 dict(name='inactive-speaker',condition=1,text='&05\n曹操',expected=[],ret=1),
 dict(name='wrong-tag',condition=1,text='曹操',tag=2,expected=[],ret=5),
 dict(name='named-speaker',condition=1,text='&曹操\n出发',expected=[['portrait',99,'出发']],ret=1),
 dict(name='named-story-speaker',condition=0,text='&曹操\n出发',expected=[['plain',99,'出发']],ret=1),
 dict(name='unknown-name',condition=1,text='&未知\n出发',expected=[['plain',65535,'出发']],ret=1),
 dict(name='current-speaker',condition=1,text='&\n出发',expected=[['portrait',99,'出发']],ret=1),
 dict(name='dead-current-speaker',condition=1,text='&\n出发',hp=0,expected=[['plain',65535,'出发']],ret=1),
]
for case in cases:
 case['bytes']=[case.get('tag',5),0,*case['text'].encode('cp936'),0]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(cases){
 const b=Process.mainModule.base;let condition=0,calls=[];const keep=[];
 function bytes(p){const a=[];for(let i=0;i<1024;i++){const v=p.add(i).readU8();if(v===0)return a;a.push(v);}throw new Error('Unterminated dialogue');}
 const cond=new NativeCallback(()=>condition,'uint',[],'mscdecl');keep.push(cond);Interceptor.replace(b.add(0xb922),cond);
 const plain=new NativeCallback((text,speaker,style)=>{calls.push({kind:'plain',speaker,style,bytes:bytes(text)});},'void',['pointer','uint','uint'],'mscdecl');keep.push(plain);Interceptor.replace(b.add(0x2d5f1),plain);
 const portrait=new NativeCallback((text,speaker)=>{calls.push({kind:'portrait',speaker,bytes:bytes(text)});},'void',['pointer','uint'],'mscdecl');keep.push(portrait);Interceptor.replace(b.add(0x5965d),portrait);Interceptor.flush();
 const handler=new NativeFunction(b.add(0x13661),'uint',['pointer'],'mscdecl'),rows=[];
 for(let id=0;id<512;id++)b.add(0xa1b68+id*72+8).writeByteArray(new Uint8Array(16));
 b.add(0xa1b68+99*72+8).writeByteArray([178,220,178,217,0]);
 for(const c of cases){
  const obj=Memory.alloc(64),input=Memory.alloc(c.bytes.length);obj.writeByteArray(new Uint8Array(64));input.writeByteArray(c.bytes);obj.add(12).writePointer(input);
  for(const [slot,id,status] of [[3,99,2],[4,100,2],[5,101,1]]){const a=b.add(0xb2c50+slot*36);a.writeU32(id);a.add(12).writeU8(status);}
  b.add(0xb2c50+3*36+16).writeU32(c.hp===undefined?100:c.hp);b.add(0xb5df0).writeU32(99);
  condition=c.condition;calls=[];const ret=handler(obj);
  rows.push({name:c.name,ret,calls,offset:obj.add(12).readPointer().sub(input).toInt32(),counter:obj.add(8).readU32()});
 }
 return rows;
}};''');script.load();rows=script.exports_sync.verify(cases)
 for case,row in zip(cases,rows):
  rendered=[[call['kind'],call['speaker'],bytes(call['bytes']).decode('cp936')] for call in row['calls']]
  row['rendered']=rendered
  row['match']=(rendered==case['expected'] and row['ret']==case['ret'] and row['counter']==2
                and row['offset']==(2 if case.get('tag')==2 else len(case['bytes']))
                and all(call.get('style',32)==32 for call in row['calls']))
 out={'scope':'Native opcode 20, reader, text splitting and numeric actor lookup; condition and UI leaves controlled','rows':rows,'passed':all(row['match'] for row in rows)}
 (ROOT/'analysis/native-eex-dialogue-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f"Native opcode 20 dialogue parsing: {sum(row['match'] for row in rows)}/{len(rows)}")
 if not out['passed']:
  print(next(row for row in rows if not row['match']));raise SystemExit(1)
finally:
 device.kill(pid)
 if session:session.detach()
