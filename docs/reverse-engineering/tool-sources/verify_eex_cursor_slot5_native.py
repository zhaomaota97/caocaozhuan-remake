"""Verify the native EEX cursor path used by the frequent opcode 20."""
import json
from pathlib import Path
import frida
ROOT=Path(__file__).resolve().parents[1]
device=frida.get_local_device();lab=ROOT/'analysis/runtime-game';pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
try:
 session=device.attach(pid)
 script=session.create_script(r'''rpc.exports={verify(){
 const b=Process.mainModule.base, next=new NativeFunction(b.add(0x183f7),'uint',['pointer','uint'],'thiscall');
 const obj=Memory.alloc(0x40),text=Memory.alloc(64),rows=[];
 const cases=[
  {name:'empty-string',tag:5,bytes:[5,0,0],expectedOffset:3,expectedCount:2,string:[]},
  {name:'CP936-string',tag:5,bytes:[5,0,178,220,178,217,0],expectedOffset:7,expectedCount:2,string:[178,220,178,217]},
  {name:'string-mismatch',tag:5,bytes:[2,0,1,0],expectedOffset:2,expectedCount:2,sentinel:2147483648},
  {name:'dword',tag:4,bytes:[4,0,120,86,52,18],expectedOffset:6,expectedCount:6,scalar:305419896},
  {name:'dword-mismatch',tag:4,bytes:[2,0,1,0],expectedOffset:2,expectedCount:2,sentinel:2147483648},
  {name:'word',tag:2,bytes:[2,0,254,255],expectedOffset:4,expectedCount:4,scalar:65534},
  {name:'word-mismatch',tag:2,bytes:[4,0,1,0,0,0],expectedOffset:2,expectedCount:2,sentinel:32768},
  {name:'raw-opcode',tag:1,bytes:[107,0],expectedOffset:2,expectedCount:2,scalar:107}
 ];
 for(const test of cases){
  obj.writeByteArray(new Uint8Array(0x40));text.writeByteArray(test.bytes);obj.add(0xc).writePointer(text);
  const returned=next(obj,test.tag),cursorOffset=obj.add(0xc).readPointer().sub(text).toInt32(),count=obj.add(8).readU32();
  let value=returned;
  if(test.string!==undefined)value=Array.from(new Uint8Array(ptr(returned).readByteArray(test.string.length)));
  rows.push({...test,returned: test.string!==undefined?'string-pointer':returned,value,cursorOffset,count});
 }
 return rows;
}};''');script.load();result=script.exports_sync.verify()
 for row in result:
  expected=row.get('string',row.get('scalar',row.get('sentinel')))
  row['match']=(row['value']==expected and row['cursorOffset']==row['expectedOffset'] and row['count']==row['expectedCount'])
 out={'scope':'Native 0x4183F7 and underlying readers, no replacements; output strings normalized to byte arrays',
      'rows':result,'passed':len(result)==8 and all(x['match'] for x in result)}
 (ROOT/'analysis/native-eex-cursor-slot5-validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
 if not out['passed']:raise SystemExit(1)
finally:
 device.kill(pid)
 if session:
  try:session.detach()
  except frida.InvalidOperationError:pass
