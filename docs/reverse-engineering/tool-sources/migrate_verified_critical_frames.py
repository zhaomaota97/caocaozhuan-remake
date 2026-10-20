"""Verify native critical palette transforms, then export normal + six critical atlas rows."""
import json
from pathlib import Path
import frida
from PIL import Image
from export_map_layouts import entries
from game_palette import color_lookup
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT.parent/'caocaozhuan-remake'
palette=next(raw for i,raw in entries(ROOT/'Spalet.e5') if i==31).ljust(768,b'\0')
current=bytes(v>>4 for v in palette);lookup=color_lookup(current)
def transform(indices,strength):
 return bytes(lookup[(min(15,current[i*3]+strength)<<8)|(min(15,current[i*3+1]+strength)<<4)|min(15,current[i*3+2]+strength)] if i else 0 for i in indices)
stages=[];indices=bytes(range(256))
for strength in [1,1,2,2,3,3]:
 indices=transform(indices,strength);stages.append(indices)
device=frida.get_local_device();pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'));session=None
try:
 session=device.attach(pid);script=session.create_script(r'''rpc.exports={verify(palette){
 const b=Process.mainModule.base;b.add(0x97770).writeByteArray(palette);
 new NativeFunction(b.add(0x2fcc6),'void',['pointer'],'mscdecl')(b.add(0x97770));
 const brighten=new NativeFunction(b.add(0x303c0),'void',['pointer','int','int','uint8'],'mscdecl'),pixels=Memory.alloc(256),rows=[];
 pixels.writeByteArray(Array.from({length:256},(_,i)=>i));
 for(const strength of [1,1,2,2,3,3]){brighten(pixels,256,1,strength);rows.push(Array.from(new Uint8Array(pixels.readByteArray(256))));}
 return rows;
}};''');script.load();actual=script.exports_sync.verify(list(current))
 assert len(actual)==6 and all(bytes(a)==e for a,e in zip(actual,stages)), 'Native critical transform mismatch'
finally:
 device.kill(pid)
 if session:session.detach()
rgb=bytes(v&0xf0 for i in range(0,768,3) for v in (palette[i+1],palette[i+2],palette[i]))
output=DEST/'public/assets/animations/atk-map31';count=0
for index,raw in entries(ROOT/'Unit_atk.e5'):
 assert len(raw)==12*4096
 sheet=Image.new('RGBA',(12*64,7*64))
 for row,lut in enumerate([bytes(range(256)),*stages]):
  translated=raw.translate(lut)
  for frame in range(12):
   pixels=translated[frame*4096:(frame+1)*4096];tile=Image.frombytes('P',(64,64),pixels);tile.putpalette(rgb);rgba=tile.convert('RGBA');rgba.putalpha(Image.frombytes('L',(64,64),bytes(255 if p else 0 for p in raw[frame*4096:(frame+1)*4096])));sheet.paste(rgba,(frame*64,row*64))
 sheet.save(output/f'atk-{index:03d}.png');count+=1
evidence={'scope':'Native 0x4303C0 with map31 palette; all 256 indices across six cumulative stages','nativeStagesMatched':6,'strengths':[1,1,2,2,3,3],'atlasRows':7,'framesPerRow':12,'exportedAtlases':count,'stageIndexMaps':[list(s) for s in stages]}
(DEST/'data/mappings/critical-palette-stages.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
(ROOT/'analysis/native-critical-palette-stages.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
print(f'Native critical palette: 6/6 stages, 1536 index outputs; exported {count} atlases')
