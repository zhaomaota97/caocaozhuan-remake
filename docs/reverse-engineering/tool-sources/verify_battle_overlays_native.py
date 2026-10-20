"""Compare original overlay writes with Python reconstruction on actual saved states."""
import hashlib
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    maps=dict(entries(ROOT/'Hexzmap.e5'))
    gates=dict(entries(ROOT/'Gate.e5'))
    cases=[]
    expected=[]
    for slot in (0,5,6):
        path=ROOT/f'Sv{slot:02d}s.e5s'
        save=path.read_bytes(); map_id=save[35]
        raw=maps[map_id]; width,height=raw[0]//3,raw[1]//3
        original=(ROOT/f'Hm{map_id:02d}.e5').read_bytes()
        art=bytearray(original)
        terrain=bytearray(raw[2:]); markers=bytearray([255]*1600)
        overlays=save[51:1301]
        requested=[]
        for i in range(250):
            x,y,t,unused,appearance=overlays[i*5:(i+1)*5]
            if appearance==255:
                continue
            terrain[x+y*width]=t
            if appearance<4:
                markers[x+y*width]=appearance
            else:
                entry=appearance*2-8; requested.append(entry)
                for tile in range(9):
                    tx,ty=x+tile%3-1,y+tile//3-1
                    if 0<=tx<width and 0<=ty<height:
                        offset=(tx+ty*width)*2304
                        art[offset:offset+2304]=gates[entry][tile*2304:(tile+1)*2304]
        cases.append(dict(file=path.name,width=width,height=height,
                          art=list(original),terrain=list(raw[2:]),overlays=list(overlays)))
        expected.append(dict(art=digest(art),terrain=digest(terrain),markers=digest(markers),
                             requested=requested))
    device=frida.get_local_device();lab=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases,gates) {
  const b=Process.mainModule.base,keep=[];
  let requested=[];
  function replace(rva,ret,args,abi,fn) {
    const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);
    Interceptor.replace(b.add(rva),cb);
  }
  replace(0x32b0,'pointer',['pointer'],'fastcall',p=>p);
  replace(0x32d0,'void',['pointer'],'fastcall',()=>{});
  replace(0x1fb35,'uint8',['pointer','pointer'],'thiscall',()=>1);
  replace(0x192c5,'uint',['pointer'],'fastcall',()=>1);
  replace(0x1fc89,'uint',['pointer','int','pointer'],'thiscall',(_obj,index,out)=>{
    requested.push(index);out.writeByteArray(gates[index]);return gates[index].length;
  });
  Interceptor.flush();
  const apply=new NativeFunction(b.add(0x56de6),'void',[],'mscdecl');
  function install(rva,size,bytes) {
    const buffer=Memory.alloc(size);buffer.writeByteArray(new Uint8Array(size));
    if(bytes)buffer.writeByteArray(bytes);
    const view=b.add(rva);view.add(4).writeU32(size);
    view.add(12).writePointer(buffer);view.add(16).writeU8(1);return buffer;
  }
  const hash=(buffer,length)=>Checksum.compute('sha256',buffer.readByteArray(length));
  return cases.map(c=>{
    requested=[];
    const art=install(0xae4a8,c.art.length,c.art);
    const map=install(0xaeb38,9600,null);
    const scratch=install(0xae4c8,20736,null);
    map.add(0x640).writeByteArray(c.terrain);
    map.add(8000).writeByteArray(new Uint8Array(1600).fill(255));
    b.add(0xb422c).writeU8(c.width);b.add(0xb422d).writeU8(c.height);
    b.add(0xb3d21).writeByteArray(c.overlays);
    apply();
    return {file:c.file,art:hash(art,c.art.length),
      terrain:hash(map.add(0x640),c.terrain.length),markers:hash(map.add(8000),1600),
      requested:requested.slice()};
  });
}};
''')
        script.load()
        rows=script.exports_sync.verify(cases,{str(i):list(b) for i,b in gates.items()})
        for row,want in zip(rows,expected):
            row['expected']=want
            row['match']=all(row[k]==v for k,v in want.items())
        (ROOT/'analysis/native-battle-overlay-validation.json').write_text(
            json.dumps(rows,indent=2),encoding='utf-8')
        print(f'Native overlay states: {sum(r["match"] for r in rows)}/{len(rows)}')
        if len(rows)!=3 or not all(r['match'] for r in rows):
            raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:session.detach()
            except frida.InvalidOperationError:pass


if __name__=='__main__':
    main()
