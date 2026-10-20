#!/usr/bin/env python3
from pathlib import Path
import struct
import pefile
root=Path(__file__).resolve().parents[1]
dispatch=(root/'analysis/native-main/pseudocode/0041ac86.c').read_text(encoding='utf-8')
pe=pefile.PE(str(root/'Ekd5.exe'))
menus=next(e for e in pe.DIRECTORY_ENTRY_RESOURCE.entries if e.id==4)
resource=menus.directory.entries[0].directory.entries[0].data.struct
raw=pe.get_data(resource.OffsetToData,resource.Size)
version,offset=struct.unpack_from('<HH',raw)
if version!=0: raise ValueError('Unsupported menu format')
labels={}
def read_menu(position):
 while True:
  flags=struct.unpack_from('<H',raw,position)[0]; position+=2
  command=None
  if not flags&16:
   command=struct.unpack_from('<H',raw,position)[0];position+=2
  end=position
  while raw[end:end+2]!=b'\0\0': end+=2
  text=raw[position:end].decode('utf-16le');position=end+2
  if command: labels[command]=text
  if flags&16: position=read_menu(position)
  if flags&128: return position
read_menu(4+offset)
checks={
 'dialog_dispatcher': 'FUN_0041ac86' in dispatch,
 'load_branch': 'FUN_0041ad06' in dispatch,
 'save_branch': 'FUN_0041b16a' in dispatch,
 'save_command_101': labels.get(101)=='\u4fdd\u5b58',
 'load_command_102': labels.get(102)=='\u8bfb\u53d6',
 'settings_command_107': labels.get(107)=='\u73af\u5883\u8bbe\u5b9a',
}
for k,v in checks.items(): print(f'{k}: {"PASS" if v else "FAIL"}')
if not all(checks.values()): raise SystemExit(1)
