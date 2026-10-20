"""Read missing roster fields using the existing native save initializer."""
import ast
import json
from pathlib import Path
import struct
import frida
import pefile
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'tools/export_slot08_native_health.py').read_text(encoding='utf-8'))
source=next(n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='create_script')
source=source.split(' function view(rva)')[0]+'''
 const spirit=new NativeFunction(b.add(0x3f5e3),'uint',['pointer'],'fastcall');
 return out.map(row=>{const a=b.add(0xb2c50+row.slot*36),u=b.add(0xa1b68+a.readU32()*72);return {slot:row.slot,experience:u.add(0x2d).readU8(),spirit:spirit(a),classId:row.classId};});
}};
'''
data=dict(entries(ROOT/'Data.e5'));device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid);script=session.create_script(source);script.load()
    rows=script.exports_sync.read(list(data[0]),list(data[1]),list(data[3]),list(data[4]),list((ROOT/'Sv08d.e5s').read_bytes()[0x14dc:]),list((ROOT/'Sv08s.e5s').read_bytes()[1301:4291]),[])
    pe=pefile.PE(str(ROOT/'Ekd5.exe'))
    for row in rows:
        address=struct.unpack('<I',pe.get_data(0x8bea8+row['classId']*4,4))[0]
        row['className']=pe.get_data(address-0x400000,100).split(b'\0')[0].decode('cp936')
    dest=ROOT.parent/'caocaozhuan-remake/data/mappings/slot08-roster-fields.json'
    dest.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Exported XP, spirit and original class names for {len(rows)} actors')
finally:
    device.kill(pid)
    if session:
        try:session.detach()
        except frida.InvalidOperationError:pass
