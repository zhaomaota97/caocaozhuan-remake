"""Decode original Win32 dialog/menu resources into readable structured templates."""
import json
import struct
from pathlib import Path
import pefile
ROOT=Path(__file__).resolve().parents[1]
class Reader:
 def __init__(self,raw):self.raw=raw;self.pos=0
 def take(self,n):
  value=self.raw[self.pos:self.pos+n]
  if len(value)!=n:raise ValueError(f'Truncated template at {self.pos}')
  self.pos+=n;return value
 def unpack(self,fmt):return struct.unpack('<'+fmt,self.take(struct.calcsize('<'+fmt)))
 def align(self,n):self.pos=(self.pos+n-1)&~(n-1)
 def field(self):
  first=self.unpack('H')[0]
  if first==0:return ''
  if first==65535:return {'ordinal':self.unpack('H')[0]}
  values=[first]
  while True:
   value=self.unpack('H')[0]
   if value==0:break
   values.append(value)
  return struct.pack('<'+'H'*len(values),*values).decode('utf-16le')
def dialog(raw):
 r=Reader(raw);extended=raw[:4]==b'\x01\x00\xff\xff'
 if extended:
  version,signature,help_id,exstyle,style,count,x,y,w,h=r.unpack('HHIIIHhhhh')
 else:
  style,exstyle,count,x,y,w,h=r.unpack('IIHhhhh');help_id=0
 result=dict(extended=extended,helpId=help_id,style=style,exStyle=exstyle,rectDlu=[x,y,w,h],menu=r.field(),windowClass=r.field(),title=r.field())
 if style&0x40:
  font={'pointSize':r.unpack('H')[0]}
  if extended:
   weight,italic,charset=r.unpack('HBB');font.update(weight=weight,italic=italic,charset=charset)
  font['face']=r.field();result['font']=font
 controls=[]
 for _ in range(count):
  r.align(4)
  if extended:help_id,exstyle,style,x,y,w,h,control_id=r.unpack('IIIhhhhI')
  else:style,exstyle,x,y,w,h,control_id=r.unpack('IIhhhhH');help_id=0
  cls,text=r.field(),r.field();extra=r.unpack('H')[0]
  data=r.take(extra).hex() if extra else ''
  controls.append(dict(id=control_id,helpId=help_id,style=style,exStyle=exstyle,rectDlu=[x,y,w,h],windowClass=cls,text=text,creationData=data))
 result.update(controls=controls,resourceBytes=len(raw),parsedBytes=r.pos,trailingHex=raw[r.pos:].hex())
 return result
def menu(raw):
 r=Reader(raw);version,offset=r.unpack('HH');r.take(offset)
 if version!=0:raise ValueError(f'Unsupported menu version {version}')
 def items():
  out=[]
  while True:
   flags=r.unpack('H')[0];item={'flags':flags}
   if not flags&0x10:item['id']=r.unpack('H')[0]
   item['text']=r.field()
   if flags&0x10:item['children']=items()
   out.append(item)
   if flags&0x80:return out
 return {'version':version,'items':items(),'resourceBytes':len(raw),'parsedBytes':r.pos}
pe=pefile.PE(str(ROOT/'Ekd5.exe'));out={'source':'Ekd5.exe','rectUnits':'Windows dialog units, not pixels','dialogs':[],'menus':[]}
for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries:
 if kind.id not in (4,5):continue
 for name in kind.directory.entries:
  for language in name.directory.entries:
   entry=language.data.struct;raw=pe.get_data(entry.OffsetToData,entry.Size)
   value=dialog(raw) if kind.id==5 else menu(raw)
   value.update(resourceId=name.id,resourceName=str(name.name) if name.name else None,language=language.id)
   out['dialogs' if kind.id==5 else 'menus'].append(value)
dest=ROOT.parent/'caocaozhuan-remake/data/mappings/native-ui-templates.json'
for path in [ROOT/'analysis/native-ui-templates.json',dest]:path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f"Decoded {len(out['dialogs'])} original dialogs and {len(out['menus'])} menu resources")
for d in out['dialogs']:print(f"{d['resourceId'] or d['resourceName']}: {d['title']} {d['rectDlu']} controls={len(d['controls'])}")
