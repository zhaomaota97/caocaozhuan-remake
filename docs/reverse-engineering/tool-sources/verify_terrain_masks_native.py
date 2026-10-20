"""Validate original terrain masking using Mark.e5 and real animation tiles."""
import hashlib
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]
MASKS={48:{1:0x39c0,2:0x30c0,7:0x42c0,9:0x27c0,10:0x27c0},
       64:{1:0x6bc0,2:0x5bc0,7:0x7bc0,9:0x4bc0,10:0x4bc0}}


def main():
    mark=(ROOT/'Mark.e5').read_bytes()
    if len(mark)!=0x1c7e0:raise ValueError('Unexpected Mark.e5 size')
    tiles={48:dict(entries(ROOT/'Unit_mov.e5'))[0][:2304],
           64:dict(entries(ROOT/'Unit_atk.e5'))[0][:4096]}
    cases=[dict(size=size,terrain=t,source=list(tiles[size])) for size in (48,64)
           for t in range(30) if t!=13]
    cases.extend(dict(size=size,terrain=13,direction=direction,phase=phase,
                      source=list(tiles[size])) for size in (48,64)
                 for direction in range(4) for phase in range(2))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(mark,cases){
  const b=Process.mainModule.base;let calls=[],geometry=[];
  const capture=new NativeCallback((x,y,w,h,source,_mode)=>{
    calls.push(Checksum.compute('sha256',source.readByteArray(w*h)));
    geometry.push([x.toInt32(),y.toInt32(),w,h]);
  },'void',['pointer','pointer','uint','int','pointer','uint'],'mscdecl');
  Interceptor.replace(b.add(0x51913),capture);Interceptor.flush();
  function install(rva,bytes){
    const buffer=Memory.alloc(bytes.length);buffer.writeByteArray(bytes);
    const v=b.add(rva);v.add(4).writeU32(bytes.length);
    v.add(12).writePointer(buffer);v.add(16).writeU8(1);return buffer;
  }
  const marks=install(0xaeb50,mark);
  const map=install(0xaeb38,new Uint8Array(0x641));
  b.add(0xb422c).writeU8(1);b.add(0xb422d).writeU8(1);
  b.add(0xb2c50).writeByteArray(new Uint8Array(0x24));
  const draw=new NativeFunction(b.add(0x5137c),'void',
    ['pointer','pointer','uint','uint','uint','pointer'],'mscdecl');
  return cases.map(c=>{
    calls=[];geometry=[];map.add(0x640).writeU8(c.terrain);
    b.add(0xb2c50+15).writeU8(c.direction || 0);
    b.add(0xb3d08+5).writeU8(c.phase || 0);
    const sprite=Memory.alloc(c.source.length);sprite.writeByteArray(c.source);
    draw(ptr(0),ptr(0),c.size,c.size,0,sprite);
    return {size:c.size,terrain:c.terrain,direction:c.direction || 0,
      phase:c.phase || 0,calls:calls.slice(),geometry:geometry.slice()};
  });
}};
''')
        script.load();rows=script.exports_sync.verify(list(mark),cases)
        for row in rows:
            size=row['size'];terrain=row['terrain'];source=tiles[size]
            if terrain in MASKS[size]:
                mask=mark[MASKS[size][terrain]:MASKS[size][terrain]+size*size]
                source=bytes(pixel if key==0 else 0 for pixel,key in zip(source,mask))
            boat=None
            if terrain==13:
                direction,phase=row['direction'],row['phase']
                offsets=[0x109c0,0x11bc0,0xf7c0,0x11bc0] if size==48 else [0x14dc0,0x16dc0,0x12dc0,0x16dc0]
                offset=offsets[direction]+phase*size*size
                mask=mark[offset:offset+size*size]
                offset=[0xd3c0,0xe5c0,0xc1c0,0xe5c0][direction]+phase*2304
                boat=mark[offset:offset+2304]
                if direction==1:
                    mask=b''.join(mask[i:i+size][::-1] for i in range(0,len(mask),size))
                    boat=b''.join(boat[i:i+48][::-1] for i in range(0,len(boat),48))
                source=bytes(pixel if key==0 else 0 for pixel,key in zip(source,mask))
            row['expected_sha256']=hashlib.sha256(source).hexdigest()
            hashes=[row['expected_sha256']]
            geometry=[[0,0,size,size]]
            if boat is not None:
                hashes.append(hashlib.sha256(boat).hexdigest())
                geometry.append([(size-48)//2,(size-48)//2,48,48])
            row['match']=row['calls']==hashes and row['geometry']==geometry
        (ROOT/'analysis/native-terrain-mask-validation.json').write_text(
            json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native terrain masks: {sum(r["match"] for r in rows)}/{len(rows)}')
        if len(rows)!=74 or not all(r['match'] for r in rows):raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':main()
