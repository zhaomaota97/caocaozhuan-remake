"""Replay S_00 setup opcodes in a suspended native process and diff state writes."""
import json
from pathlib import Path
import frida
from export_eex_bodies import encode_instruction

ROOT=Path(__file__).resolve().parents[1]


def main():
    raw=json.loads((ROOT/'analysis/s_00-setup-events.json').read_text(encoding='utf-8'))
    events=[e for e in raw['events_list'] if e['opcode'] in {68,69,70,71,72,74,75}]
    cases=[dict(segment=e['segment'],branch=e['branch'],offset=e['offset'],opcode=e['opcode'],bytes=list(encode_instruction(e))) for e in events]
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game';pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={replay(cases){
 const b=Process.mainModule.base,obj=Memory.alloc(0x2040),state=b.add(0x92F90),common=b.add(0xB3D08),dispatch=new NativeFunction(b.add(0x109EF),'uint',['pointer'],'fastcall');
 const rows=[];let input;
 for(const c of cases){
  input=Memory.alloc(c.bytes.length);input.writeByteArray(c.bytes);obj.writeByteArray(new Uint8Array(0x2040));obj.add(12).writePointer(input);
  const before=new Uint8Array(state.readByteArray(0x4000));let status=255,error=null;
  try{status=dispatch(obj)&255;}catch(e){error=String(e);}
  const after=new Uint8Array(state.readByteArray(0x4000));const changed=[];
  for(let i=0;i<after.length;i++)if(after[i]!==before[i])changed.push({offset:i,before:before[i],after:after[i]});
  rows.push({segment:c.segment,branch:c.branch,offset:c.offset,opcode:c.opcode,status,error,consumed:obj.add(12).readPointer().sub(input).toInt32(),changed_count:changed.length,changed:changed.slice(0,4096),state_after:(c.opcode===70||c.opcode===71||c.opcode===75||c.opcode===72)?Array.from(after):undefined,common:Array.from(new Uint8Array(common.readByteArray(32)))});
  if(error)break;
 }
 return rows;
}};
''');script.load();rows=script.exports_sync.replay(cases)
        result=dict(script='S_00.eex',replayed=len(rows),events=len(cases),rows=rows,scope='native dispatcher replay; state window 0x492F90..0x4A2F90; no resume/render/audio; changed bytes are raw offsets, not guessed field names')
        (ROOT/'analysis/native-s00-unit-setup-replay.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(f'S_00 native setup replay: {len(rows)}/{len(cases)}; errors={sum(bool(r["error"]) for r in rows)}')
        if any(r['error'] for r in rows):raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
