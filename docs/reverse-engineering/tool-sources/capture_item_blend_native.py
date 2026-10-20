"""Capture exact native pixel outputs for ITEM animation's constant blend loop."""
import ast
import json
from pathlib import Path
import frida
from export_map_layouts import entries
ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'tools/verify_effect_blend_native.py').read_text(encoding='utf-8'))
source=next(n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='create_script')
palette=[v>>4 for v in dict(entries(ROOT/'Spalet.e5'))[31].ljust(768,b'\0')]
pixels=list(range(256));background=[(i*13+61)&255 for i in pixels]
cases=[dict(kind='constant',opacity=i,invert=1,strength=0,alternate=False) for i in range(16)]
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
    session=device.attach(pid);script=session.create_script(source);script.load()
    actual=script.exports_sync.verify(palette,palette,pixels,[0]*256,background,cases)
    rows=[]
    for case,output in zip(cases,actual['outputs']):
        if output[:16]!=[165]*16 or output[-16:]!=[165]*16:raise RuntimeError('Native buffer guard changed')
        rows.append(dict(frame=case['opacity'],pixels=output[16:-16]))
    result=dict(scope='native 0x42FD5A, map31 palette and native 0x42FCC6 lookup; item frame arguments 0..15, invert1 strength0; source0..255 and synthetic backgrounds, not full animation render',palette=palette,lookup=actual['lookup'],source=pixels,background=background,rows=rows)
    text=json.dumps(result,indent=2)+'\n';(ROOT/'analysis/native-item-blend-frames.json').write_text(text,encoding='utf-8');(ROOT.parent/'caocaozhuan-remake/docs/reverse-engineering/native-item-blend-frames.json').write_text(text,encoding='utf-8')
    print('Native item blend captured: 16 frames, 4096 pixels, guards intact')
finally:
    device.kill(pid)
    if session:session.detach()
