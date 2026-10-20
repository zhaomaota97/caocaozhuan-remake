"""Verify original palette uploader with display writes intercepted."""
import json
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]


def main():
    cases = [dict(file=name, index=i, data=list(raw))
             for name in ('Pmpalet.e5', 'Spalet.e5')
             for i, raw in entries(ROOT / name)]
    device = frida.get_local_device()
    runtime = ROOT / 'analysis/runtime-game'
    pid = device.spawn([str(runtime / 'Ekd5.exe')], cwd=str(runtime))
    session = None
    try:
        session = device.attach(pid)
        script = session.create_script('''
rpc.exports = { verify(cases) {
 const b=Process.mainModule.base, keep=[], rows=[]; let uploads=[];
 const setTable=new NativeCallback((dc,start,count,table)=>{
  uploads.push({dc:dc.toUInt32(),start,count}); return count;
 },'uint',['pointer','uint','uint','pointer'],'mscdecl');
 const redraw=new NativeCallback(()=>{},'void',['int','int','int','int','int'],'mscdecl');
 keep.push(setTable,redraw);
 Interceptor.replace(b.add(0x7F402),setTable);
 Interceptor.replace(b.add(0x7C966),redraw); Interceptor.flush();
 const upload=new NativeFunction(b.add(0x7E867),'void',['uint','uint','pointer'],'mscdecl');
 b.add(0xB7DB0).writeU32(1); b.add(0xBC028).writeU32(2);
 b.add(0xB9948).writeU32(101); b.add(0xB994C).writeU32(202);
 const input=Memory.alloc(768);
 for(const c of cases) for(const context of [0,1]) {
  b.add(0xBD044).writeU32(context);
  b.add(0xB88B8+context*4).writeU32(7);
  b.add(0xBA228+context*4).writeU32(4);
  b.add(0xB9548).writeByteArray(new Uint8Array(1024).fill(165));
  b.add(0xB9E10).writeByteArray(new Uint8Array(1024).fill(165));
  const data=new Uint8Array(768); data.set(c.data.map(x=>x>>4));
  input.writeByteArray(data); uploads=[]; upload(10,236,input.add(30));
  const dib=new Uint8Array(b.add(0xB9548).readByteArray(1024));
  const pal=new Uint8Array(b.add(0xB9E10).readByteArray(1024));
  let mismatch=0;
  for(let i=0;i<256;i++) {
   const active=i>=10&&i<246, p=i*3;
   const d=active?[data[p]<<4,data[p+2]<<4,data[p+1]<<4,165]:[165,165,165,165];
   const l=active?[data[p+1]<<4,data[p+2]<<4,data[p]<<4,165]:[165,165,165,165];
   for(let j=0;j<4;j++) { if(dib[i*4+j]!==d[j])mismatch++; if(pal[i*4+j]!==l[j])mismatch++; }
  }
  rows.push({file:c.file,index:c.index,context,mismatch,uploads});
 }
 return rows;
}};
''')
        script.load()
        rows = script.exports_sync.verify(cases)
        for row in rows:
            row['match'] = row['mismatch'] == 0 and row['uploads'] == [
                dict(dc=101, start=0, count=256), dict(dc=202, start=0, count=256)]
        report = dict(function='0x47E867', passed=sum(r['match'] for r in rows),
                      total=len(rows), rows=rows,
                      scope='mode7, shift4, indices10..245, 173 real resource palettes, contexts0/1, two DIB targets; display/table output intercepted; no actual window rendering')
        (ROOT / 'analysis/native-palette-upload-validation.json').write_text(
            json.dumps(report, indent=2), encoding='utf-8')
        print(f'Native palette table/channel/shared-context upload: {report["passed"]}/{len(rows)}')
        if report['passed'] != len(rows):
            print(next(r for r in rows if not r['match']))
            raise SystemExit(1)
    finally:
        if session:
            session.detach()
        device.kill(pid)


if __name__ == '__main__':
    main()
