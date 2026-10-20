"""Export saved battle actors and validate original actor/state serialization."""
import csv
import json
from pathlib import Path
import frida

ROOT = Path(__file__).resolve().parents[1]


def main():
    payload = []
    with (ROOT / 'analysis/characters.csv').open(encoding='utf-8-sig') as f:
        names = {int(row['id']):row['name_gbk'] for row in csv.DictReader(f)}
    with (ROOT / 'analysis/battle-save-actors.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f)
        w.writerow(['save','slot','unit_id','name','x','y','health_like','resource_like',
                    'state','side_candidate','raw_hex'])
        for path in sorted(ROOT.glob('Sv??s.e5s')):
            raw=path.read_bytes()
            if len(raw) != 5891 or raw[0] != 5:
                raise ValueError(f'{path.name}: unsupported format')
            state=raw[35:1301]
            actors=raw[1301:4291]
            payload.append(dict(file=path.name,state=list(state),actors=list(actors)))
            for slot in range(115):
                row=actors[slot*26:(slot+1)*26]
                uid=int.from_bytes(row[:2],'little')
                w.writerow([path.name,slot,uid,names.get(uid,''),row[8],row[9],
                            int.from_bytes(row[2:4],'little'),int.from_bytes(row[4:6],'little'),
                            row[14],row[7],row.hex()])
    if len(payload) != 10:
        raise ValueError('Expected ten shipped save slots')
    device=frida.get_local_device()
    lab=ROOT / 'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab))
    session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports = {verify(payload) {
  const b=Process.mainModule.base;
  const loadActor=new NativeFunction(b.add(0x42e26),'pointer',['pointer','pointer'],'thiscall');
  const saveActor=new NativeFunction(b.add(0x42bf6),'pointer',['pointer','pointer'],'thiscall');
  const loadState=new NativeFunction(b.add(0x4f384),'pointer',['pointer','pointer'],'thiscall');
  const saveState=new NativeFunction(b.add(0x4f153),'pointer',['pointer','pointer'],'thiscall');
  const obj=Memory.alloc(0x508), output=Memory.alloc(1266);
  const results=[];
  for(const file of payload) {
    for(const [kind,bytes,width,load,save] of [
      ['state',file.state,1266,loadState,saveState],
      ['actor',file.actors,26,loadActor,saveActor]]) {
      const input=Memory.alloc(bytes.length);input.writeByteArray(bytes);
      let matched=0;
      for(let i=0;i<bytes.length/width;i++) {
        obj.writeByteArray(new Uint8Array(0x508));
        const src=input.add(i*width);
        const consumed=load(obj,src).sub(src).toInt32();
        const written=save(obj,output).sub(output).toInt32();
        const actual=new Uint8Array(output.readByteArray(width));
        if(consumed===width && written===width &&
          actual.every((v,j)=>v===bytes[i*width+j])) matched++;
      }
      results.push({file:file.file,kind,records:bytes.length/width,matched});
    }
  }
  return results;
}};
''')
        script.load()
        results=script.exports_sync.verify(payload)
        (ROOT/'analysis/native-battle-save-validation.json').write_text(
            json.dumps(results,indent=2),encoding='utf-8')
        total=sum(r['records'] for r in results); matched=sum(r['matched'] for r in results)
        print(f'Native battle save round trips: {matched}/{total}')
        if matched != total or len(results) != 20:
            raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:
                session.detach()
            except frida.InvalidOperationError:
                pass


if __name__=='__main__':
    main()
