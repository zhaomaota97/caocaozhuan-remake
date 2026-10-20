"""Exhaust native status bit updates and six attribute-stage transitions."""
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]
SET_BITS={31:8,32:8,33:16,34:16,35:2,36:2,37:4}
CLEAR_CODES={46,47,67}


def main():
    codes=[*SET_BITS,*CLEAR_CODES,0]
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(codes){
  const b=Process.mainModule.base,actor=b.add(0xb2c50);
  const refresh=new NativeCallback(()=>{},'void',['uint'],'mscdecl');
  Interceptor.replace(b.add(0x79a01),refresh);Interceptor.flush();
  const status=new NativeFunction(b.add(0x20e25),'void',['uint8','uint'],'mscdecl');
  const stage=new NativeFunction(b.add(0x3f98e),'void',['pointer','uint8','int'],'thiscall');
  const rows=[];
  for(const code of codes)for(let current=0;current<256;current++){
    actor.writeByteArray(new Uint8Array(36).fill(165));actor.writeU32(0);
    actor.add(30).writeU8(current);status(code,0);
    rows.push({kind:'status',code,current,bytes:Array.from(new Uint8Array(actor.readByteArray(36)))});
  }
  for(let channel=0;channel<6;channel++)for(let current=0;current<256;current++)for(const up of [0,1]){
    actor.writeByteArray(new Uint8Array(36).fill(165));actor.add(24+channel).writeU8(current);
    stage(actor,channel,up);
    rows.push({kind:'stage',channel,current,up,bytes:Array.from(new Uint8Array(actor.readByteArray(36)))});
  }
  return rows;
}};
''')
        script.load();rows=script.exports_sync.verify(codes)
        for row in rows:
            wanted=[165]*36
            if row['kind']=='status':
                wanted[:4]=[0]*4
                value=row['current']
                if row['code'] in SET_BITS:value|=SET_BITS[row['code']]
                elif row['code'] in CLEAR_CODES:value&=~0x1e
                offset=30
            else:
                offset=24+row['channel'];current=row['current']
                value=(6 if row['up'] else 3) if current>=4 else (
                    (6 if row['up'] else 0) if current==3 else (3 if row['up'] else 0))
            wanted[offset]=value
            row['actual']=row['bytes'][offset]
            row['expected']=value
            row['match']=row.pop('bytes')==wanted
        result=dict(cases=len(rows),matched=sum(r['match'] for r in rows),
                    status_cases=sum(r['kind']=='status' for r in rows),
                    stage_cases=sum(r['kind']=='stage' for r in rows),
                    failures=[r for r in rows if not r['match']])
        (ROOT/'analysis/native-status-effect-validation.json').write_text(
            json.dumps(result,indent=2),encoding='utf-8')
        print(f'Native status updates: {result["matched"]}/{len(rows)}')
        if len(rows)!=5888 or result['failures']:raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
