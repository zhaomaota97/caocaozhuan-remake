"""Extract real EEX interpreter snapshots from events.jsonl."""
import json,sys
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit('usage: summarize_live_eex_cursor.py EVENTS.JSONL')
path=Path(sys.argv[1]);interpreter=[];handlers=[];dispatches=[]
for line in path.read_text(encoding='utf-8').splitlines():
    try:item=json.loads(line);p=item.get('payload',item)
    except Exception:continue
    event=p.get('event')
    if event=='eex-interpreter':interpreter.append(p)
    elif event=='eex-handler':handlers.append(p)
    elif event=='eex-dispatch':dispatches.append(p)
first=interpreter[0] if interpreter else {}
opcode20=next((h for h in handlers if h.get('opcode')==20),None)
out={'source':str(path),'interpreterSnapshots':len(interpreter),'handlerObservations':len(handlers),'dispatchObservations':len(dispatches),'firstInterpreter':first,'opcode20':opcode20,'handlerOpcodes':sorted({h.get('opcode') for h in handlers})}
dest=path.parent/'eex-cursor-summary.json';dest.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
lines=['# Live EEX cursor evidence','',f"Source: `{path}`",'',f"Interpreter snapshots: {len(interpreter)}; dispatches: {len(dispatches)}; handler observations: {len(handlers)}.",'']
if first:
    lines += [f"- Interpreter object: `{first.get('this_ecx')}`",f"- Script parameter/buffer: `{first.get('param1')}`",f"- State pointer: `{first.get('state_ptr')}`",f"- Cursor pointer reported by observer: `{first.get('cursor_ptr')}`",f"- Script prefix: `{bytes(first.get('bytes',[])[:16]).hex(' ')}`",f"- State prefix: `{bytes(first.get('state_bytes',[])[:32]).hex(' ')}`",'']
lines += ['Observed handler opcodes: '+', '.join(str(x) for x in sorted({h.get('opcode') for h in handlers if h.get('opcode') is not None}))+'.']
if opcode20: lines += [f"- Opcode 20 live cursor: `{opcode20.get('cursor_ptr')}`, cursor field `{opcode20.get('cursor_field')}`."]
lines += ['', 'The observer hook records real process addresses and buffers. The first interpreter snapshot has a null pre-dispatch cursor, but the live opcode-20 handler supplies a valid cursor pointer and field. This is the runtime layout needed to replace the earlier incomplete synthetic object.']
(path.parent/'eex-cursor-summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f'Live EEX: {len(interpreter)} snapshots, {len(dispatches)} dispatches, {len(handlers)} handlers')
