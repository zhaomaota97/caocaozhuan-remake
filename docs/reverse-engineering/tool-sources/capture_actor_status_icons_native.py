"""Trace original actor renderer's status icon resource offsets and positions."""
import ast
import json
from pathlib import Path
import frida
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'tools/verify_acted_render_gate_native.py').read_text(encoding='utf-8'))
source=next(n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='create_script')
source=source.replace('let output=[];','let output=[],icons=[];')
needle='b.add(0x97770).writeByteArray(palette);'
source=source.replace(needle,"""
 const buffer=Memory.alloc(0x20000);
 const resource=new NativeCallback((_obj,offset)=>buffer.add(offset),'pointer',['pointer','uint','uint','uint'],'thiscall');keep.push(resource);Interceptor.replace(b.add(0x7fa40),resource);
 replace(0x51913,'void',['pointer','pointer','uint','uint','pointer','uint'],(x,y,w,h,p,mode)=>icons.push({x:x.toInt32(),y:y.toInt32(),width:w,height:h,offset:p.sub(buffer).toInt32(),mode}));Interceptor.flush();
 """+needle)
start=source.index(' for(let flags=0;');end=source.index(' return {rows,darkened};',start)
source=source[:start]+'''
 for(const flags of [0,6])for(let status=0;status<32;status++)for(let phase=0;phase<8;phase++){
  actor.writeByteArray(new Uint8Array(36));actor.add(13).writeU8(flags);actor.add(16).writeU32(1);actor.add(30).writeU8(status);b.add(0xb3d08+5).writeU8(phase);
  output=[];icons=[];draw(ptr(0),ptr(0),0);
  rows.push({flags,status,phase,icons,pixels:output.slice(0,256)});
 }
''' +source[end:]
palette=[v>>4 for v in dict(entries(ROOT/'Spalet.e5'))[31].ljust(768,b'\0')]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid);script=session.create_script(source);script.load();result=script.exports_sync.capture(palette)
    result.update(total=len(result['rows']),palette=palette,scope='original actor renderer with source tile, final actor draw, status icon draw and resource-buffer query controlled; actual flag/status/phase branches and color transforms run; map31 explicit zero-tail palette')
    text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/native-actor-status-icons.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-actor-status-icons.json').write_text(text,encoding='utf-8')
    print(f'Native status renderer: {result["total"]} cases, icon offsets/coordinates and pixel outputs captured')
    for mask in [2,4,6,8,10,12,14]:print(mask,[next(r['icons'] for r in result['rows'] if r['flags']==0 and r['status']==mask and r['phase']==p) for p in [0,1]])
finally:
    device.kill(pid)
    if session:session.detach()
