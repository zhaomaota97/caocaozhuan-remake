"""Differential-check native keyed blits, including independent row pitches."""
import json
from pathlib import Path
import frida

ROOT=Path(__file__).resolve().parents[1]


def main():
    cases=[]
    for width,height,source_pitch,destination_pitch in [
        (256,1,256,256),(13,3,17,19),(48,48,64,60),(64,64,68,70),(0,4,7,9)]:
        source=[(i*37)%256 for i in range(source_pitch*height)]
        destination=[(i*19+53)%256 for i in range(destination_pitch*height)]
        for mode in (0,6,7):
            cases.append(dict(width=width,height=height,source_pitch=source_pitch,
                destination_pitch=destination_pitch,source=source,destination=destination,mode=mode))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases){
  const blit=new NativeFunction(Process.mainModule.base.add(0x7f740),'void',
    ['int','int','int','int','pointer','pointer','int'],'mscdecl');
  return cases.map(c=>{
    const source=Memory.alloc(c.source.length),dest=Memory.alloc(c.destination.length+32);
    source.writeByteArray(c.source);dest.writeByteArray(new Uint8Array(c.destination.length+32).fill(165));
    dest.add(16).writeByteArray(c.destination);
    blit(c.width,c.height,c.destination_pitch,c.source_pitch,source,dest.add(16),c.mode);
    return Array.from(new Uint8Array(dest.readByteArray(c.destination.length+32)));
  });
}};
''')
        script.load();outputs=script.exports_sync.verify(cases);rows=[]
        for case,output in zip(cases,outputs):
            expected=case['destination'].copy()
            for y in range(case['height']):
                for x in range(case['width']):
                    v=case['source'][y*case['source_pitch']+x]
                    if v if case['mode']==7 else v&15:
                        expected[y*case['destination_pitch']+x]=v
            rows.append(dict(**{k:v for k,v in case.items() if k not in ('source','destination')},
                             match=output==[165]*16+expected+[165]*16))
        (ROOT/'analysis/native-transparent-blit-validation.json').write_text(
            json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native transparent blits: {sum(r["match"] for r in rows)}/{len(rows)}')
        if len(rows)!=15 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
