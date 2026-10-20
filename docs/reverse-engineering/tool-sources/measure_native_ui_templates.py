"""Instantiate hidden original Win32 templates to measure font-based dialog units."""
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import pefile
ROOT=Path(__file__).resolve().parents[1]
user=c.windll.user32;kernel=c.windll.kernel32;common=c.windll.comctl32
user.SetProcessDPIAware()
class Init(c.Structure):_fields_=[('size',w.DWORD),('classes',w.DWORD)]
init=Init(c.sizeof(Init),0xffff);common.InitCommonControlsEx(c.byref(init))
callbackType=c.WINFUNCTYPE(c.c_ssize_t,w.HWND,w.UINT,w.WPARAM,w.LPARAM)
@callbackType
def proc(hwnd,msg,wp,lp):return 0
user.CreateDialogIndirectParamW.argtypes=[w.HINSTANCE,c.c_void_p,w.HWND,callbackType,w.LPARAM];user.CreateDialogIndirectParamW.restype=w.HWND
user.GetDlgItem.argtypes=[w.HWND,c.c_int];user.GetDlgItem.restype=w.HWND
user.GetWindowRect.argtypes=[w.HWND,c.POINTER(w.RECT)];user.GetClientRect.argtypes=[w.HWND,c.POINTER(w.RECT)]
user.MapDialogRect.argtypes=[w.HWND,c.POINTER(w.RECT)];user.DestroyWindow.argtypes=[w.HWND]
user.ScreenToClient.argtypes=[w.HWND,c.POINTER(w.POINT)]
pe=pefile.PE(str(ROOT/'Ekd5.exe'));doc=json.loads((ROOT/'analysis/native-ui-templates.json').read_text(encoding='utf-8'))
resources={}
for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries:
 if kind.id==5:
  for name in kind.directory.entries:
   entry=name.directory.entries[0].data.struct;resources[name.id if name.id is not None else str(name.name)]=pe.get_data(entry.OffsetToData,entry.Size)
for dialog in doc['dialogs']:
 key=dialog['resourceId'] if dialog['resourceId'] is not None else dialog['resourceName']
 raw=c.create_string_buffer(resources[key]);hwnd=user.CreateDialogIndirectParamW(None,raw,None,proc,0)
 if not hwnd:
  dialog['measurementError']=kernel.GetLastError();continue
 try:
  client=w.RECT();window=w.RECT();scale=w.RECT(0,0,4,8)
  user.GetClientRect(hwnd,c.byref(client));user.GetWindowRect(hwnd,c.byref(window));user.MapDialogRect(hwnd,c.byref(scale))
  dialog['nativeClientPixels']=[client.right,client.bottom];dialog['nativeWindowPixels']=[window.right-window.left,window.bottom-window.top]
  dialog['dialogBasePixels']=[scale.right,scale.bottom]
  for control in dialog['controls']:
   if control['id'] in (65535,4294967295):continue
   child=user.GetDlgItem(hwnd,control['id'])
   if child:
    rect=w.RECT();user.GetWindowRect(child,c.byref(rect));point=w.POINT(rect.left,rect.top);user.ScreenToClient(hwnd,c.byref(point))
    control['nativeRectPixels']=[point.x,point.y,rect.right-rect.left,rect.bottom-rect.top]
 finally:user.DestroyWindow(hwnd)
for path in [ROOT/'analysis/native-ui-templates.json',ROOT.parent/'caocaozhuan-remake/data/mappings/native-ui-templates.json']:
 path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f"Measured {sum('nativeClientPixels' in d for d in doc['dialogs'])}/{len(doc['dialogs'])} hidden original dialog templates; failures retained explicitly")
for dialog in doc['dialogs']:
 if dialog['resourceId']==279:print(json.dumps(dialog,ensure_ascii=True))
