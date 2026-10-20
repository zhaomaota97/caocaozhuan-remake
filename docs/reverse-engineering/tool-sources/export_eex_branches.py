"""Recover candidate-branch boundaries and compare the native indexed branch cursor."""
import json
import struct
from pathlib import Path
import frida
from eex_segments import inspect

ROOT=Path(__file__).resolve().parents[1]


def main():
    payload=[];records=[]
    for path in sorted(ROOT.glob('*.eex')):
        raw=path.read_bytes();info=inspect(path);segments=[]
        for index,segment in enumerate(info['segments']):
            pos=segment['offset'];end=pos+segment['size']
            count=struct.unpack_from('<H',raw,pos)[0];pos+=2;branches=[]
            for branch in range(count):
                if pos+2>end:raise ValueError('Missing branch length')
                size=struct.unpack_from('<H',raw,pos)[0]
                if pos+2+size>end:raise ValueError('Branch exceeds segment')
                branches.append(dict(index=branch,length_offset=pos,payload_offset=pos+2,size=size))
                pos+=2+size
            if pos!=end:raise ValueError('Candidate branches do not cover segment')
            segments.append(dict(index=index,offset=segment['offset'],branches=branches))
        payload.append(dict(bytes=list(raw),table=info['table_offset'],segments=segments))
        records.append(dict(file=path.name,segments=segments))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(files){
  const seek=new NativeFunction(Process.mainModule.base.add(0xfba9),'void',
    ['pointer','int'],'thiscall');
  const obj=Memory.alloc(0x38),rows=[];
  for(const file of files){
    const source=Memory.alloc(file.bytes.length);source.writeByteArray(file.bytes);
    obj.writeByteArray(new Uint8Array(0x38));obj.add(0x20).writePointer(source);obj.add(0x30).writeU32(file.table);
    let matched=0,total=0;
    for(const segment of file.segments){
      obj.add(4).writeU32(segment.index);
      for(const branch of segment.branches){
        seek(obj,branch.index);total++;
        const offset=obj.add(12).readPointer().sub(source).toInt32();
        if(offset===branch.length_offset && obj.add(8).readU32()===offset-segment.offset)matched++;
      }
    }
    rows.push({total,matched});
  }
  return rows;
}};
''')
        script.load();native=script.exports_sync.verify(payload)
        for record,result in zip(records,native):record['native_validation']=result
        (ROOT/'analysis/eex-branches.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
        total=sum(r['total'] for r in native);matched=sum(r['matched'] for r in native)
        print(f'Native EEX branch offsets: {matched}/{total} across {len(records)} files')
        if len(records)!=117 or total!=2320 or matched!=total:raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
