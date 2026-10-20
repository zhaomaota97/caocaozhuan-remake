"""Observe a bounded actual GUI startup in the existing isolated game copy."""
import ctypes
import argparse
import csv
from ctypes import wintypes
import json
import threading
import time
from pathlib import Path
from PIL import ImageGrab
import frida

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--open-load',action='store_true')
    parser.add_argument('--start-new',action='store_true')
    parser.add_argument('--advance-story',action='store_true',help='periodically press Enter/Space after starting a new game')
    parser.add_argument('--load-slot',type=int,choices=range(10))
    parser.add_argument('--save-slot',type=int,choices=range(10),help='activate this slot after the native save dialog opens')
    parser.add_argument('--seconds',type=int,default=35)
    parser.add_argument('--confirm-load',action='store_true')
    parser.add_argument('--confirm-save',action='store_true',help='confirm the native save overwrite prompt')
    parser.add_argument('--move-test',action='store_true')
    parser.add_argument('--save-test',action='store_true',help='send Ctrl+S once after battle load')
    parser.add_argument('--probe-toolbar',action='store_true',help='click each battle toolbar button once')
    parser.add_argument('--save-command',action='store_true',help='post native save WM_COMMAND 101 once')
    parser.add_argument('--direct-commands',default='',help='comma-separated WM_COMMAND ids sent to the battle root without probing toolbar')
    parser.add_argument('--skip-intro',action='store_true')
    parser.add_argument('--background',action='store_true',help='keep Ekd5 windows hidden and avoid foreground activation')
    parser.add_argument('--force-load-dispatch',action='store_true',help='after slot selection, probe native load completion dispatcher')
    args=parser.parse_args();load_opened=False;slot_selected=False;save_slot_selected=False;load_confirmed=False;save_confirmed=False;native_slot=None;move_tested=False;direct_sent=False
    battle_ready=False;native_battle_ready=False;save_init_ready=False;snapshot_taken=False
    output=ROOT/'analysis'/('live-startup-'+time.strftime('%Y%m%d-%H%M%S'))
    output.mkdir()
    lab=ROOT/'analysis/runtime-game';device=frida.get_local_device()
    pid=device.spawn([str(lab/'Ekd5.exe')],cwd=str(lab));session=None;detached=threading.Event()
    user=ctypes.windll.user32
    user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
    user.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
    user.GetDlgCtrlID.argtypes=[wintypes.HWND]
    callback_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    with (output/'events.jsonl').open('w',encoding='utf-8') as log:
        def record(item,data=None):
            nonlocal native_slot,battle_ready,native_battle_ready,save_init_ready
            payload=item.get('payload',{})
            if payload.get('event')=='native-entry' and payload.get('rva')==0x1ad06:
                native_slot=int(payload['arg0'],16)
            if payload.get('event')=='native-return' and payload.get('rva')==0x4d092:
                battle_ready=True;native_battle_ready=True
            if payload.get('event')=='save-buffer-init-followup' and payload.get('save_buffer') not in (None,'0x0','0x00000000'):
                save_init_ready=True
            if data is not None and payload.get('event')=='runtime-snapshot':
                kind=payload['kind']
                if kind not in {'roster','actors','terrain','state','artwork'}:raise ValueError('Unknown snapshot kind')
                prefix=payload.get('prefix','')
                name=f'{prefix}snapshot-{kind}.bin';(output/name).write_bytes(data);payload['dump']=name
            log.write(json.dumps(item,ensure_ascii=False)+'\n');log.flush()
        def ended(reason,crash):
            record(dict(event='detached',reason=reason,crash=str(crash)));detached.set()
        try:
            session=device.attach(pid);session.on('detached',ended)
            handler_map={}
            with (ROOT/'analysis/eex/opcode-index.csv').open(encoding='utf-8-sig') as index_file:
                for row in csv.DictReader(index_file):
                    if row.get('handler'):
                        handler_map[int(row['handler'],16)-0x400000]=int(row['opcode'])
            script_source='''
const b=Process.mainModule.base;
let lastDialogObject=ptr(0);
const globalExport=name => {
  for(const module of Process.enumerateModules()){
    try{return module.getExportByName(name);}catch(_){ }
  }
  throw new Error('export not found: '+name);
};
const skipIntro=SKIP_INTRO;
const introSkip=new NativeCallback(()=>{send({event:'intro-skipped'});},'void',
  ['uint16','int','int','int','int'],'mscdecl');
if(skipIntro){Interceptor.replace(b.add(0x1f862),introSkip);Interceptor.flush();}
if(typeof Process.setExceptionHandler==='function')Process.setExceptionHandler(details=>{
  const module=Process.findModuleByAddress(details.address);
  send({event:'exception',type:details.type,address:details.address.toString(),
    module:module?module.name:null,memory:details.memory,
    backtrace:Thread.backtrace(details.context,Backtracer.ACCURATE).map(p=>p.toString())});return false;
});
for(const name of ['ExitProcess','TerminateProcess']){
  Interceptor.attach(globalExport(name),{onEnter(args){
    send({event:name,arg0:args[0].toString(),arg1:args[1].toString(),
      backtrace:Thread.backtrace(this.context,Backtracer.ACCURATE).map(p=>p.toString())});
  }});
}
let snd=null;try{snd=globalExport('sndPlaySoundA');}catch(_){snd=null;}
if(snd && BACKGROUND_MODE){
  Interceptor.replace(snd,new NativeCallback(function(path,flags){
    let p='';try{p=path.isNull()?'':path.readCString();}catch(_){ }
    send({event:'sndPlaySoundA-muted',path:p,flags:flags.toUInt32()});return 1;
  },'uint',['pointer','uint']));
} else if(snd)Interceptor.attach(snd,{onEnter(args){
  let path='';try{path=args[0].isNull()?'':args[0].readCString();}catch(_){path='';}
  send({event:'sndPlaySoundA',path,flags:args[1].toUInt32(),backtrace:Thread.backtrace(this.context,Backtracer.ACCURATE).map(p=>p.toString())});
}});
if(BACKGROUND_MODE){
  for(const name of ['PlaySoundA','PlaySoundW']){try{const p=globalExport(name);Interceptor.replace(p,new NativeCallback(function(sound,mod,flags){send({event:name+'-muted'});return 1;},'int',['pointer','pointer','uint']));}catch(_){}}
  try{const p=globalExport('mciSendStringA');Interceptor.replace(p,new NativeCallback(function(command,returnText,returnLen,callback){let c='';try{c=command.isNull()?'':command.readCString();}catch(_){ }send({event:'mciSendStringA-muted',command:c});return 0;},'uint',['pointer','pointer','uint','pointer']));}catch(_){ }
  try{const p=globalExport('waveOutOpen');Interceptor.replace(p,new NativeCallback(function(){send({event:'waveOutOpen-muted'});return 1;},'uint',['pointer','uint','pointer','uint','uint','uint']));}catch(_){ }
}
// Save serializer boundary: FUN_0041B16A(this, slot) and its output buffer.
try{Interceptor.attach(b.add(0x1b16a),{onEnter(args){
  try{const q=b.add(0x96f60).readPointer();send({event:'save-serializer-enter',slot:args[0].toUInt32(),this_ptr:this.context.ecx.toString(),
    save_buffer:q.toString(),save_buffer_bytes:q.isNull()?[]:Array.from(new Uint8Array(q.readByteArray(16)))});}catch(e){send({event:'save-serializer-enter-error',error:String(e)});}
},onLeave(retval){send({event:'save-serializer-return',ret:retval.toString()});}});}catch(e){send({event:'save-hook-error',error:String(e)});}
try{Interceptor.attach(b.add(0x1bf67),{onEnter(){send({event:'save-state-init-enter'});},onLeave(retval){
  try{const q=b.add(0x96f60).readPointer();send({event:'save-state-init-return',ret:retval.toString(),save_buffer:q.toString()});}
  catch(e){send({event:'save-state-init-return-error',ret:retval.toString(),error:String(e)});}
}});}catch(e){send({event:'save-init-hook-error',error:String(e)});}
try{Interceptor.attach(b.add(0x7fa40),{onEnter(args){send({event:'save-buffer-alloc-enter',size:args[3].toUInt32()});},onLeave(retval){send({event:'save-buffer-alloc-return',ret:retval.toString()});}});}catch(e){send({event:'save-alloc-hook-error',error:String(e)});}
try{Interceptor.attach(b.add(0x7fd13),{onEnter(){try{send({event:'save-buffer-init-followup',save_buffer:b.add(0x96f60).readPointer().toString()});}catch(e){send({event:'save-buffer-init-followup-error',error:String(e)});}}});}catch(e){send({event:'save-followup-hook-error',error:String(e)});}
try{Interceptor.attach(b.add(0x64a97),{onEnter(args){
  // This wrapper is also called for transient/non-window messages.  Do not
  // dereference ECX or LPARAM here: raw pointers are sufficient for tracing
  // and keep the observer from perturbing the native load path.
  try{send({event:'save-dialog-wrapper-enter-raw',ecx:this.context.ecx.toString(),arg0:args[0].toString(),arg1:args[1].toString(),arg2:args[2].toString(),arg3:args[3].toString()});}catch(e){}
}});}catch(e){send({event:'save-dialog-wrapper-hook-error',error:String(e)});}
try{Interceptor.attach(b.add(0x0e240),{onEnter(args){send({event:'save-slot-callback-enter',ecx:this.context.ecx.toString(),arg0:args[0].toString(),arg1:args[1].toString()});},onLeave(ret){send({event:'save-slot-callback-return',ret:ret.toString()});}});}catch(e){send({event:'save-slot-callback-hook-error',error:String(e)});}
try{Interceptor.attach(b.add(0x64e1f),{onEnter(args){try{const obj=this.context.ecx;lastDialogObject=obj;const row=args[0].toInt32(),table=obj.add(0x18).readPointer();send({event:'save-selection-callback-enter',object:obj.toString(),row,current:obj.add(0x1c).readS32(),table:table.toString(),value:table.add(row*4).readU32()});}catch(e){send({event:'save-selection-callback-error',error:String(e)});}}});}catch(e){send({event:'save-selection-hook-error',error:String(e)});}
try{Interceptor.attach(b.add(0x1ac86),{onEnter(args){send({event:'dialog-completion-dispatch-enter',object:this.context.ecx.toString(),param:args[0].toUInt32()});}});}catch(e){send({event:'dialog-completion-hook-error',error:String(e)});}
rpc.exports={completeLoad(slot){if(lastDialogObject.isNull())throw new Error('dialog object unavailable');const f=new NativeFunction(b.add(0x1ac86),'void',['pointer','uint'],'thiscall');f(lastDialogObject,slot);return lastDialogObject.toString();},snapshot(prefix){
  const roster=Memory.alloc(512*32),actors=Memory.alloc(115*26),state=Memory.alloc(1266);
  const getMapField=new NativeFunction(b.add(0x7fa40),'pointer',['pointer','uint','uint','uint'],'thiscall');
  const saveUnit=new NativeFunction(b.add(0x8f2e),'pointer',['pointer','pointer'],'thiscall');
  const saveActor=new NativeFunction(b.add(0x42bf6),'pointer',['pointer','pointer'],'thiscall');
  const saveState=new NativeFunction(b.add(0x4f153),'pointer',['pointer','pointer'],'thiscall');
  for(let i=0;i<512;i++)saveUnit(b.add(0xa1b68+i*72),roster.add(i*32));
  for(let i=0;i<115;i++)saveActor(b.add(0xb2c50+i*36),actors.add(i*26));
  saveState(b.add(0xb3d08),state);
  const width=b.add(0xb422c).readU8(),height=b.add(0xb422d).readU8();
  let resourceWidth=0,resourceHeight=0;try{resourceWidth=getMapField(b.add(0xae4c8),0,0,4).readU8()/3;resourceHeight=getMapField(b.add(0xae4c8),1,0,4).readU8()/3;}catch(e){}
  if(width<1||width>40||height<1||height>40)throw new Error('Battle map dimensions invalid: globals='+width+'x'+height+',resource='+resourceWidth+'x'+resourceHeight+',map='+b.add(0xb3d08).readU8());
  for(const [kind,pointer,size] of [['roster',roster,512*32],['actors',actors,115*26],
      ['state',state,1266],['terrain',b.add(0xaeb38+12).readPointer().add(0x640),width*height],
      ['artwork',b.add(0xae4a8+12).readPointer(),width*height*2304]]){
    send({event:'runtime-snapshot',prefix:prefix||'',kind,width,height,map:b.add(0xb3d08).readU8()},pointer.readByteArray(size));
  }
  return {width,height,resourceWidth,resourceHeight,map:b.add(0xb3d08).readU8()};
},activateRow(handle,row){
  const backgroundMode=BACKGROUND_MODE;
  const hwnd=ptr(handle),rect=Memory.alloc(16);rect.writeByteArray(new Uint8Array(16));rect.writeS32(2);
  const send=new NativeFunction(globalExport('SendMessageW'),'int',
    ['pointer','uint','uint','pointer'],'stdcall');
  const post=new NativeFunction(globalExport('PostMessageW'),'bool',
    ['pointer','uint','uint','int'],'stdcall');
  if(!send(hwnd,0x100e,row,rect))throw new Error('Cannot retrieve save row bounds');
  const bounds=[0,4,8,12].map(off=>rect.add(off).readS32());
  const x=Math.floor((bounds[0]+bounds[2])/2),y=Math.floor((bounds[1]+bounds[3])/2);
  const point=(y<<16)|(x&65535);
  const getRoot=new NativeFunction(globalExport('GetAncestor'),'pointer',['pointer','uint'],'stdcall');
  const root=getRoot(hwnd,2);
  const thread=new NativeFunction(globalExport('GetWindowThreadProcessId'),'uint',['pointer','pointer'],'stdcall');
  const current=new NativeFunction(globalExport('GetCurrentThreadId'),'uint',[],'stdcall');
  const attach=new NativeFunction(globalExport('AttachThreadInput'),'int',['uint','uint','int'],'stdcall');
  const foreground=new NativeFunction(globalExport('SetForegroundWindow'),'bool',['pointer'],'stdcall');
  const active=new NativeFunction(globalExport('SetActiveWindow'),'pointer',['pointer'],'stdcall');
  const focus=new NativeFunction(globalExport('SetFocus'),'pointer',['pointer'],'stdcall');
  const getActive=new NativeFunction(globalExport('GetActiveWindow'),'pointer',[],'stdcall');
  const getForeground=new NativeFunction(globalExport('GetForegroundWindow'),'pointer',[],'stdcall');
  const from=current(),to=thread(hwnd,ptr(0)),attached=attach(from,to,1);
  const foregroundBefore=getForeground(),foregroundThread=thread(foregroundBefore,ptr(0));
  const foregroundAttached=foregroundThread!==from&&foregroundThread!==to?attach(from,foregroundThread,1):0;
  const foregroundResult=foreground(root);active(root);focus(hwnd);
  const item=Memory.alloc(60);item.writeByteArray(new Uint8Array(60));
  // LVITEM: iItem at +4, state/stateMask at +12/+16. Select and focus one row.
  // The native wrapper queries LVIS_FOCUSED (mask=1), then invokes the save
  // callback only when that bit is set. Keep selected and focused together.
  item.add(4).writeU32(row);item.add(12).writeU32(3);item.add(16).writeU32(3);
  const selection=send(hwnd,0x102b,row,item);
  // The list-view state message selects the row reliably. Keyboard activation
  // avoids the legacy coordinate fallback, which can report hitRow=-1 and
  // propagate 0xFFFFFFFF into the native save-slot formatter.
  const keydown=backgroundMode?0:post(hwnd,0x100,0x0d,0),keyup=backgroundMode?0:post(hwnd,0x101,0x0d,0);
  const doubleClick=backgroundMode?0:post(hwnd,0x203,1,point);
  const notify=Memory.alloc(80);notify.writeByteArray(new Uint8Array(80));
  notify.writePointer(hwnd);notify.add(Process.pointerSize).writeU32(1487);
  notify.add(Process.pointerSize+4).writeS32(-0x6c); // LVN_COLUMNCLICK path invokes callback +0x3c
  notify.add(Process.pointerSize+8).writeS32(row);
  const notifyResult=send(root,0x4e,1487,notify);
  const commandResult=send(root,0x111,(2<<16)|1487,hwnd);
  const notifySecond=send(root,0x4e,1487,notify);
  const activeHandle=getActive().toString();
  const screen=Memory.alloc(8);screen.writeS32(x);screen.add(4).writeS32(y);
  const toScreen=new NativeFunction(globalExport('ClientToScreen'),'bool',
    ['pointer','pointer'],'stdcall');toScreen(hwnd,screen);
  const setCursor=new NativeFunction(globalExport('SetCursorPos'),'bool',['int','int'],'stdcall');
  setCursor(screen.readS32(),screen.add(4).readS32());
  const cursor=Memory.alloc(8),getCursor=new NativeFunction(globalExport('GetCursorPos'),
    'bool',['pointer'],'stdcall');getCursor(cursor);
  const atCursor=new NativeFunction(globalExport('WindowFromPoint'),'pointer',['int','int'],'stdcall');
  const toClient=new NativeFunction(globalExport('ScreenToClient'),'int',
    ['pointer','pointer'],'stdcall');
  const hit=Memory.alloc(24);let hitRow=-1,cursorWindow='0x0',client=[];
  for(let attempt=0;attempt<5;attempt++){
    getCursor(cursor);cursorWindow=atCursor(cursor.readS32(),cursor.add(4).readS32()).toString();
    hit.writeByteArray(new Uint8Array(24));hit.writeS32(cursor.readS32());hit.add(4).writeS32(cursor.add(4).readS32());
    toClient(hwnd,hit);client=[hit.readS32(),hit.add(4).readS32()];hitRow=send(hwnd,0x1012,0,hit);
    if(hitRow===row && cursorWindow===hwnd.toString())break;
    setCursor(cursor.readS32()+x-client[0],cursor.add(4).readS32()+y-client[1]);
  }
  if(backgroundMode){
    if(foregroundAttached)attach(from,foregroundThread,0);if(attached)attach(from,to,0);
    return {bounds,queued:[keydown,keyup,doubleClick],selection,backgroundStateOnly:true,notifyResult,notifySecond,commandResult};
  }
  if(hitRow!==row || cursorWindow!==hwnd.toString()){
    // The state-selection message above is sufficient for this custom list in
    // some legacy builds; fall back to posting the click without treating the
    // optional hit-test as fatal.
    // Some common-controls builds reject the synthetic hit-test even though
    // the row is selected.  Send the actual client-coordinate click as a
    // final fallback so the dialog's native LVN/command path can run.
    const clickDown=post(hwnd,0x201,1,point),clickUp=post(hwnd,0x202,0,point);
    const fallback=[keydown,keyup,doubleClick,clickDown,clickUp];
    if(foregroundAttached)attach(from,foregroundThread,0);if(attached)attach(from,to,0);
    return {bounds,queued:fallback,selection,hitTestFallback:true,hitRow,
      cursorWindow,client,screen:[screen.readS32(),screen.add(4).readS32()],
      cursor:[cursor.readS32(),cursor.add(4).readS32()],keyboardActivation:true,notifyResult,notifySecond,commandResult};
  }
  const queued=[post(hwnd,0x201,1,point),post(hwnd,0x202,0,point)];
  if(foregroundAttached)attach(from,foregroundThread,0);
  if(attached)attach(from,to,0);
  return {bounds,queued,selection,attached,foregroundAttached,foregroundResult,activeHandle,
    foregroundBefore:foregroundBefore.toString(),root:root.toString(),cursorWindow,hitRow,client,
    screen:[screen.readS32(),screen.add(4).readS32()],cursor:[cursor.readS32(),cursor.add(4).readS32()]};
}};
for(const name of ['CreateFileA','LoadLibraryA']){
  Interceptor.attach(globalExport(name),{onEnter(args){
    try{send({event:name,path:args[0].readCString()});}catch(e){}
  }});
}
const fileHandles=new Map();let fileReads=0;
Interceptor.attach(globalExport('CreateFileA'),{onEnter(args){this.filePath='';this.rawPath=[];try{this.filePath=args[0].readCString();this.rawPath=Array.from(new Uint8Array(args[0].readByteArray(this.filePath.length+1)));}catch(e){}},onLeave(ret){
  let key=ret.toString();if(this.filePath && key!=='0xffffffff')fileHandles.set(key,this.filePath);
  send({event:'file-open',path:this.filePath,rawPathBytes:this.rawPath,handle:key,success:key!=='0xffffffff'});
}});
Interceptor.attach(globalExport('ReadFile'),{onEnter(args){
  this.handle=args[0].toString();this.request=args[2].toUInt32();this.path=fileHandles.get(this.handle)||null;this.buffer=args[1];this.count=args[3];
},onLeave(ret){
  if(fileReads++<400){let got=0;try{got=this.count.readU32();}catch(e){}send({event:'file-read',path:this.path,handle:this.handle,request:this.request,received:got,success:ret.toInt32()});}
}});
Interceptor.attach(globalExport('SetFilePointer'),{onEnter(args){
  if(fileReads<400)send({event:'file-pointer',path:fileHandles.get(args[0].toString())||null,handle:args[0].toString(),distance:args[1].toInt32(),method:args[3].toUInt32()});
}});
for(const rva of [0x1ad06,0x1b16a,0x17ed2,0x4d092,0x4c188,0x4c1cb,0x38308,
  0x3ad1c,0x3aaFb,0x438a20,0x44c658,0x44c74d,0x44c8e6]){
  Interceptor.attach(b.add(rva),{onEnter(args){
    const item={event:'native-entry',rva,object:this.context.ecx.toString(),arg0:args[0].toString()};
    if(rva===0x38308){
      try{item.coord=[args[1].readU8(),args[1].add(1).readU8()];item.budget=args[2].toUInt32();
        item.flags=args[3].toUInt32();item.start=[args[4].toUInt32(),args[5].toUInt32()];item.mode=args[6].toInt32();}catch(e){item.error=String(e);}
    }
    send(item);this.move=item;
  },onLeave(value){const item={event:'native-return',rva,value:value.toString()};
    if(rva===0x38308){item.coord=this.move&&this.move.coord;item.budget=this.move&&this.move.budget;}
    send(item);}});
}
let eexDispatches=0;
Interceptor.attach(b.add(0x109ef),{onEnter(args){
  if(eexDispatches++<300){
    try{const item={event:'eex-dispatch',ecx:this.context.ecx.toString(),
      arg0:args[0].toString(),arg1:args[1].toString(),arg2:args[2].toString(),
      return_address:this.returnAddress.toString(),stack:Thread.backtrace(this.context,Backtracer.ACCURATE).slice(0,8).map(DebugSymbol.fromAddress)};
      for(const k of ['arg0','arg1','arg2']){try{const q=args[Number(k.slice(3))];item[k+'_bytes']=Array.from(new Uint8Array(q.readByteArray(32)));}catch(e){item[k+'_bytes_error']=String(e);}}
      send(item);}
    catch(e){send({event:'eex-dispatch-error',error:String(e)});}
  }
},onLeave(ret){
  if(eexDispatches<=301){try{send({event:'eex-dispatch-return',ret:ret.toString(),ecx:this.context.ecx.toString()});}catch(e){}}
}});
let eexInterpreters=0;
Interceptor.attach(b.add(0x10273),{onEnter(args){
  if(eexInterpreters++<100){
    try{const p=args[0];const obj=this.context.ecx;const c=obj.add(0x0c).readPointer();const s=obj.add(0x1c).readPointer();send({event:'eex-interpreter',this_ecx:this.context.ecx.toString(),
      param1:p.toString(),this_bytes:Array.from(new Uint8Array(this.context.ecx.readByteArray(128))),
      bytes:Array.from(new Uint8Array(p.readByteArray(128))),cursor_ptr:c.toString(),cursor_delta:c.sub(p).toInt32(),cursor_bytes:Array.from(new Uint8Array(c.readByteArray(32))),state_ptr:s.toString(),state_bytes:Array.from(new Uint8Array(s.readByteArray(32))),state_slots:Array.from({length:8},(_,i)=>{const q=s.add(i*4).readPointer();return {ptr:q.toString(),bytes:Array.from(new Uint8Array(q.readByteArray(16)))};})});}catch(e){send({event:'eex-interpreter-error',error:String(e)});}
  }
  this.eexObj=this.context.ecx;
},onLeave(ret){
    try{const c=this.eexObj.add(0x0c).readPointer();const s=this.eexObj.add(0x1c).readPointer();const p=this.eexObj.add(0x20).readPointer();send({event:'eex-interpreter-return',ret:ret.toString(),this_ecx:this.eexObj.toString(),this_bytes:Array.from(new Uint8Array(this.eexObj.readByteArray(128))),param1:p.toString(),cursor_ptr:c.toString(),cursor_delta:c.sub(p).toInt32(),cursor_bytes:Array.from(new Uint8Array(c.readByteArray(32))),param_bytes:Array.from(new Uint8Array(p.readByteArray(128))),state_ptr:s.toString(),state_bytes:Array.from(new Uint8Array(s.readByteArray(32)))});}catch(e){}
}});
const eexHandlers=EEX_HANDLERS;
for(const rva in eexHandlers){Interceptor.attach(b.add(parseInt(rva)),{onEnter(args){try{const o=this.context.ecx;const item={event:'eex-handler',opcode:eexHandlers[rva],handler_rva:parseInt(rva),ecx:o.toString(),args:[args[0].toString(),args[1].toString(),args[2].toString()]};try{item.cursor_ptr=o.add(0x0c).readPointer().toString();item.cursor_field=o.add(8).readU32();if(eexHandlers[rva]===20){const c=o.add(0x0c).readPointer();item.cursor_before=Array.from(new Uint8Array(c.sub(16).readByteArray(32)));item.cursor_after=Array.from(new Uint8Array(c.readByteArray(32)));item.param_ptr=o.add(0x20).readPointer().toString();}}catch(e){} send(item);}catch(e){send({event:'eex-handler-error',handler_rva:parseInt(rva),error:String(e)});}}});}
const containers=new Map();let resourceCount=0;
Interceptor.attach(b.add(0x1fb35),{onEnter(args){try{containers.set(this.context.ecx.toString(),args[0].readCString());}catch(e){}}});
Interceptor.attach(b.add(0x1fc89),{onEnter(args){
  if(resourceCount++<2000)send({event:'resource-entry',container:containers.get(this.context.ecx.toString())||null,index:args[0].toUInt32()});
}});
let inputEvents=0;
Interceptor.attach(b.add(0x652b9),{onEnter(args){
  if(inputEvents++<20)send({event:'list-input',message:args[0].toUInt32(),
    object:this.context.ecx.toString(),lock:this.context.ecx.add(0x20).readU32()});
}});
let mainMessages=0;
Interceptor.attach(globalExport('DispatchMessageW'),{onEnter(args){
  if(mainMessages++<200){
    try{const m=args[0];send({event:'dispatch-message',hwnd:m.readPointer().toString(),
      message:m.add(Process.pointerSize).readU32(),wparam:m.add(Process.pointerSize+4).readU32(),
      lparam:m.add(Process.pointerSize+8).readS32()});}catch(e){}
  }
}});
for(const api of ['SendMessageA','SendMessageW','PostMessageA','PostMessageW']){
  try{Interceptor.attach(globalExport(api),{onEnter(args){
    if(mainMessages++<500){
      try{const cls=Memory.allocUtf16String('');const title=Memory.allocUtf16String('');
        const getClass=globalExport('GetClassNameW');
        const getTitle=globalExport('GetWindowTextW');
        const gc=new NativeFunction(getClass,'int',['pointer','pointer','int'],'stdcall');
        const gt=new NativeFunction(getTitle,'int',['pointer','pointer','int'],'stdcall');
        const cb=Memory.alloc(256);const tb=Memory.alloc(512);gc(args[0],cb,128);gt(args[0],tb,256);
        send({event:'window-message-api',api,hwnd:args[0].toString(),class_name:cb.readUtf16String(),
          title:tb.readUtf16String(),message:args[1].toUInt32(),wparam:args[2].toUInt32(),
          lparam:args[3].toString()});}catch(e){}
    }
  }});}catch(e){}
}
'''.replace('SKIP_INTRO',json.dumps(args.skip_intro)).replace('BACKGROUND_MODE',json.dumps(args.background)).replace('EEX_HANDLERS',json.dumps({hex(rva): opcode for rva,opcode in handler_map.items()}))
            script=session.create_script(script_source)
            script.on('message',record);script.load();device.resume(pid)
            for step in range(args.seconds):
                if detached.wait(1):break
                if native_battle_ready and not snapshot_taken:
                    record(dict(event='snapshot-request',result=script.exports_sync.snapshot()));snapshot_taken=True
                if args.save_test and battle_ready and not locals().get('save_tested',False):
                    # Record child controls once so the real save command can be
                    # identified from its command ID before attempting UI writes.
                    controls_snapshot=[]
                    for window in windows if 'windows' in locals() else []:
                        def save_child(hwnd,_):
                            text=ctypes.create_unicode_buffer(256);cls=ctypes.create_unicode_buffer(128)
                            user.GetWindowTextW(hwnd,text,256);user.GetClassNameW(hwnd,cls,128)
                            rec={'hwnd':int(hwnd),'id':user.GetDlgCtrlID(hwnd),'text':text.value,'kind':cls.value}
                            if cls.value=='ToolbarWindow32':
                                try:
                                    user.SendMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
                                    n=int(user.SendMessageW(hwnd,0x418,0,0)); rec['button_count']=n; rec['commands']=[]
                                    for bi in range(n):
                                        buf=ctypes.create_string_buffer(32)
                                        if user.SendMessageW(hwnd,0x417,bi,ctypes.addressof(buf)):
                                            rec['commands'].append(int.from_bytes(buf.raw[4:8],'little'))
                                except Exception as ex: rec['toolbar_error']=str(ex)
                            controls_snapshot.append(rec)
                            return True
                        user.EnumChildWindows(window['hwnd'],callback_type(save_child),0)
                    user.keybd_event(0x11,0,0,0);user.keybd_event(0x53,0,0,0);user.keybd_event(0x53,0,2,0);user.keybd_event(0x11,0,2,0)
                    record(dict(event='action',name='save-test',keys=['CTRL','S'],controls=controls_snapshot));save_tested=True
                if args.save_command and battle_ready and not locals().get('save_command_sent',False):
                    target=next((w for w in windows if w['rect'][2]-w['rect'][0]>=800),None) if 'windows' in locals() else None
                    if target:
                        queued=user.PostMessageW(target['hwnd'],0x111,101,0)
                        record(dict(event='action',name='save-command',command=101,queued=bool(queued),target=target))
                    else:
                        record(dict(event='action',name='save-command',command=101,target=None))
                    save_command_sent=bool(target and queued)
                if args.direct_commands and battle_ready and not direct_sent and (save_init_ready or args.skip_intro):
                    target=next((w for w in windows if w['rect'][2]-w['rect'][0]>=800),None) if 'windows' in locals() else None
                    commands=[]
                    if target:
                        for raw in args.direct_commands.split(','):
                            try:
                                command=int(raw.strip(),0)
                                queued=user.PostMessageW(target['hwnd'],0x111,command,0)
                                commands.append({'command':command,'queued':bool(queued),'target':target['hwnd']})
                            except ValueError:
                                commands.append({'raw':raw,'error':'invalid command'})
                    record(dict(event='action',name='direct-commands',commands=commands,target=target))
                    direct_sent=bool(commands)
                if args.probe_toolbar and battle_ready and not locals().get('toolbar_probed',False):
                    probes=[]
                    for c in controls_snapshot if 'controls_snapshot' in locals() else []:
                        if c.get('kind')!='ToolbarWindow32': continue
                        th=wintypes.HWND(c['hwnd']); n=c.get('button_count',0)
                        for bi in range(n):
                            rb=ctypes.create_string_buffer(32)
                            if not user.SendMessageW(th,0x41D,bi,ctypes.addressof(rb)): continue
                            left=int.from_bytes(rb.raw[0:4],'little',signed=True); top=int.from_bytes(rb.raw[4:8],'little',signed=True)
                            right=int.from_bytes(rb.raw[8:12],'little',signed=True); bottom=int.from_bytes(rb.raw[12:16],'little',signed=True)
                            pt=wintypes.POINT((left+right)//2,(top+bottom)//2);user.ClientToScreen(th,ctypes.byref(pt))
                            user.SetCursorPos(pt.x,pt.y);user.mouse_event(2,0,0,0,0);user.mouse_event(4,0,0,0,0);time.sleep(.4)
                            probes.append({'button':bi,'screen':[pt.x,pt.y],'rect':[left,top,right,bottom]})
                    record(dict(event='action',name='probe-toolbar',probes=probes));toolbar_probed=True
                if args.advance_story and step>8 and step%3==0:
                    target=next((w for w in windows if w['rect'][2]-w['rect'][0]>=800),None) if 'windows' in locals() else None
                    if target is None:
                        fg=int(user.GetForegroundWindow()); target={'hwnd':fg,'title':'foreground','rect':[]}
                    if target:
                        if not args.background:
                            user.ShowWindow(target['hwnd'],5);user.SetForegroundWindow(target['hwnd'])
                        else:
                            user.ShowWindow(target['hwnd'],0)
                        time.sleep(.1)
                    for vk in (0x0D,0x20):
                        user.keybd_event(vk,0,0,0);user.keybd_event(vk,0,2,0)
                    record(dict(event='action',name='advance-story',keys=['ENTER','SPACE'],target=target))
                if step%5!=4:continue
                windows=[]
                def collect(hwnd,_):
                    owner=wintypes.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
                    if owner.value==pid and user.IsWindowVisible(hwnd):
                        title=ctypes.create_unicode_buffer(256);user.GetWindowTextW(hwnd,title,256)
                        cls=ctypes.create_unicode_buffer(128);user.GetClassNameW(hwnd,cls,128)
                        rect=wintypes.RECT();user.GetWindowRect(hwnd,ctypes.byref(rect))
                        if args.background:
                            user.ShowWindow(hwnd,0)
                        windows.append(dict(hwnd=int(hwnd),title=title.value,class_name=cls.value,
                            rect=[rect.left,rect.top,rect.right,rect.bottom]))
                    return True
                user.EnumWindows(callback_type(collect),0)
                if args.background:
                    # Load/confirm dialogs are created after the main window;
                    # hide every visible game-owned top-level window as soon
                    # as it is enumerated, while retaining handles for native
                    # message-driven automation.
                    for hidden in windows:
                        user.ShowWindow(hidden['hwnd'],0)
                record(dict(event='windows',seconds=step+1,windows=windows))
                if args.direct_commands and battle_ready and not direct_sent and (save_init_ready or args.skip_intro):
                    target=next((w for w in windows if w['rect'][2]-w['rect'][0]>=500 and not w['title'].upper().endswith('.AVI')),None)
                    commands=[]
                    if target:
                        for raw in args.direct_commands.split(','):
                            try:
                                command=int(raw.strip(),0)
                                queued=user.PostMessageW(target['hwnd'],0x111,command,0)
                                commands.append({'command':command,'queued':bool(queued),'target':target['hwnd']})
                            except ValueError:
                                commands.append({'raw':raw,'error':'invalid command'})
                    record(dict(event='action',name='direct-commands',commands=commands,target=target))
                    direct_sent=bool(commands)
                if args.move_test and not move_tested and battle_ready:
                    for window in windows:
                        if window['rect'][2]-window['rect'][0] < 800: continue
                        left,top=window['rect'][:2]
                        if not args.background:
                            user.ShowWindow(window['hwnd'],5);user.SetForegroundWindow(window['hwnd'])
                        else:
                            user.ShowWindow(window['hwnd'],0)
                        time.sleep(.2)
                        # Approximate two adjacent 48px battlefield cells in the
                        # captured slot-0 layout; record exact coordinates used.
                        clicks=[(left+458,top+340),(left+506,top+340)]
                        for x,y in clicks:
                            if not args.background:
                                user.SetCursorPos(x,y);user.mouse_event(2,0,0,0,0);user.mouse_event(4,0,0,0,0)
                            else:
                                user.PostMessageW(window['hwnd'],0x201,1,((y-window['rect'][1])<<16)|(x-window['rect'][0]))
                                user.PostMessageW(window['hwnd'],0x202,0,((y-window['rect'][1])<<16)|(x-window['rect'][0]))
                            time.sleep(.5)
                        record(dict(event='action',name='move-test',window=window,clicks=clicks));
                        time.sleep(1)
                        if native_battle_ready:
                            record(dict(event='postmove-snapshot-request',result=script.exports_sync.snapshot('postmove-')))
                        move_tested=True;break
                for index,window in enumerate(windows):
                    left,top,right,bottom=window['rect']
                    if (right-left<80 or bottom-top<40 or
                        (not args.background and (right-left<150 or bottom-top<100))):continue
                    if window['title'].upper().endswith('.AVI'):
                        continue
                    controls=[]
                    def child_control(hwnd,_):
                        text=ctypes.create_unicode_buffer(256);cls=ctypes.create_unicode_buffer(128)
                        user.GetWindowTextW(hwnd,text,256);user.GetClassNameW(hwnd,cls,128)
                        controls.append(dict(hwnd=int(hwnd),id=user.GetDlgCtrlID(hwnd),text=text.value,kind=cls.value))
                        return True
                    user.EnumChildWindows(window['hwnd'],callback_type(child_control),0)
                    record(dict(event='controls',parent=window['hwnd'],seconds=step+1,controls=controls))
                    # The native battle-ready RVA is not reached in every
                    # startup path. A visible HexMapName plus toolbar is a
                    # stronger UI-level battle surface signal for toolbar
                    # probing, without enabling memory snapshots.
                    if ((args.probe_toolbar or args.move_test or args.save_test or args.save_command or args.direct_commands) and not battle_ready and
                        any(c['kind']=='ToolbarWindow32' for c in controls) and
                        any(c['kind']=='HexMapName' for c in controls)):
                        battle_ready=True
                        controls_snapshot=[]
                        for c in controls:
                            if c['kind']!='ToolbarWindow32': continue
                            rec=dict(c,button_count=None,commands=[])
                            # TB_BUTTONCOUNT/TB_GETBUTTON can cross into the
                            # legacy COMCTL32 subclass and corrupt its state.
                            # Only request them for workflows that explicitly
                            # need toolbar geometry or control enumeration.
                            if args.probe_toolbar or args.save_test:
                                try:
                                    user.SendMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
                                    n=int(user.SendMessageW(c['hwnd'],0x418,0,0));rec['button_count']=n
                                    for bi in range(n):
                                        buf=ctypes.create_string_buffer(32)
                                        if user.SendMessageW(c['hwnd'],0x417,bi,ctypes.addressof(buf)):
                                            rec['commands'].append(int.from_bytes(buf.raw[4:8],'little'))
                                except Exception as ex:
                                    rec['toolbar_error']=str(ex)
                            controls_snapshot.append(rec)
                        record(dict(event='battle-surface-detected',window=window,toolbar=controls_snapshot))
                        if args.move_test and not move_tested:
                            # The load path can expose the battle surface after
                            # the regular action phase.  Execute the probe here,
                            # while the battle window and HexMapName are known.
                            left, top = window['rect'][:2]
                            clicks=[(left+458,top+340),(left+506,top+340)]
                            if not args.background:
                                user.ShowWindow(window['hwnd'],5);user.SetForegroundWindow(window['hwnd'])
                            else:
                                user.ShowWindow(window['hwnd'],0)
                            time.sleep(.2)
                            for x,y in clicks:
                                if not args.background:
                                    user.SetCursorPos(x,y);user.mouse_event(2,0,0,0,0);user.mouse_event(4,0,0,0,0)
                                else:
                                    user.PostMessageW(window['hwnd'],0x201,1,((y-window['rect'][1])<<16)|(x-window['rect'][0]))
                                    user.PostMessageW(window['hwnd'],0x202,0,((y-window['rect'][1])<<16)|(x-window['rect'][0]))
                                time.sleep(.5)
                            record(dict(event='action',name='move-test-after-battle-surface',window=window,clicks=clicks))
                            try:
                                record(dict(event='postmove-snapshot-request',result=script.exports_sync.snapshot('postmove-')))
                            except Exception as exc:
                                record(dict(event='postmove-snapshot-error',error=repr(exc),native_ready=native_battle_ready))
                            move_tested=True
                        # The battle flag is established late in this scan.
                        # Dispatch direct commands immediately so a short-lived
                        # startup/skip-intro path cannot exit before the next
                        # loop iteration reaches the command block above.
                        if args.direct_commands and not direct_sent and (save_init_ready or args.skip_intro):
                            commands=[]
                            for raw in args.direct_commands.split(','):
                                try:
                                    command=int(raw.strip(),0)
                                    queued=user.PostMessageW(window['hwnd'],0x111,command,0)
                                    commands.append({'command':command,'queued':bool(queued),'target':window['hwnd']})
                                except ValueError:
                                    commands.append({'raw':raw,'error':'invalid command'})
                            record(dict(event='action',name='direct-commands',commands=commands,target=window))
                            direct_sent=bool(commands)
                    if args.confirm_load and not load_confirmed and native_slot in (None,args.load_slot):
                        ids={control['id'] for control in controls}
                        if {6,7,1332}.issubset(ids):
                            yes=next(c for c in controls if c['id']==6)
                            user.SendMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
                            user.SendMessageW.restype=ctypes.c_ssize_t
                            result=user.SendMessageW(yes['hwnd'],0xF5,0,0)
                            record(dict(event='action',name='confirm-load',slot=native_slot,control=yes,result=int(result)))
                            load_confirmed=True
                    if args.start_new and (save_init_ready or args.skip_intro):
                        for control in controls:
                            if control['id']==1027 and control['kind']=='Button':
                                user.PostMessageW(control['hwnd'],0xF5,0,0)
                                record(dict(event='action',name='start-new',control=control))
                                args.start_new=False
                                break
                    if (args.open_load or args.load_slot is not None) and not load_opened:
                        for control in controls:
                            if control['id']==1028 and control['kind']=='Button':
                                user.PostMessageW(control['hwnd'],0xF5,0,0)
                                record(dict(event='action',name='open-load',control=control));load_opened=True
                                break
                    if args.load_slot is not None and not slot_selected:
                        for control in controls:
                            if control['id']==1487 and control['kind']=='SysListView32':
                                try:
                                    activated=script.exports_sync.activate_row(str(control['hwnd']),args.load_slot)
                                    record(dict(event='action',name='activate-save',slot=args.load_slot,
                                                control=control,result=activated));slot_selected=True
                                    if args.force_load_dispatch:
                                        # Let the native dialog window thread
                                        # execute 0x41AC86 via its normal
                                        # WM_COMMAND path; a synchronous Frida
                                        # call would block the observer thread.
                                        root_hwnd=window['hwnd']
                                        queued=user.PostMessageW(root_hwnd,0x111,args.load_slot,0)
                                        record(dict(event='action',name='force-load-dispatch-post',slot=args.load_slot,queued=bool(queued),target=root_hwnd))
                                except Exception as exc:
                                    record(dict(event='action-error',name='activate-save',slot=args.load_slot,
                                                control=control,error=repr(exc)))
                                break
                    if args.save_slot is not None and not save_slot_selected and '保存进度' in window['title']:
                        for control in controls:
                            if control['id']==1487 and control['kind']=='SysListView32':
                                try:
                                    activated=script.exports_sync.activate_row(str(control['hwnd']),args.save_slot)
                                    record(dict(event='action',name='activate-save-slot',slot=args.save_slot,
                                                control=control,result=activated))
                                    save_slot_selected=True
                                except Exception as exc:
                                    record(dict(event='action-error',name='activate-save-slot',slot=args.save_slot,
                                                control=control,error=repr(exc)))
                                break
                    if args.confirm_save and not save_confirmed and '保存' in window['title'] and '保存进度' not in window['title']:
                        ids={control['id'] for control in controls}
                        if {6,7,1332}.issubset(ids):
                            yes=next(control for control in controls if control['id']==6)
                            user.SendMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
                            user.SendMessageW.restype=ctypes.c_ssize_t
                            result=user.SendMessageW(yes['hwnd'],0xF5,0,0)
                            record(dict(event='action',name='confirm-save',control=yes,result=int(result)))
                            save_confirmed=True
                    try:
                        image=ImageGrab.grab(window=window['hwnd'])
                        image.save(output/f'window-{step+1:02d}-{index}.png')
                        record(dict(event='capture',seconds=step+1,size=list(image.size),
                                    extrema=image.convert('L').getextrema()))
                    except OSError as exc:record(dict(event='capture-error',error=str(exc)))
                print(f'{step+1}s: {[(w["title"],w["rect"]) for w in windows]}',flush=True)
        finally:
            try:device.kill(pid)
            except frida.ProcessNotFoundError:pass
            if session is not None:
                try:session.detach()
                except frida.InvalidOperationError:pass
    print(f'Live evidence: {output}',flush=True)


if __name__=='__main__':main()
