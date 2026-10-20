"""Select among all18 S_00 event predicates using captured native actor records."""
import argparse
import json
import struct
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--death-chain',action='store_true',help='execute death bodies11/10, stop before victory body9; item reward leaf captured')
    parser.add_argument('--ally-death',type=int,choices=(32,3,33),help='execute real ally death branch and flag write; HP0 supplied')
    parser.add_argument('--victory-chain',action='store_true',help='execute enemy deaths and full victory body in one interpreter; move/item leaves captured')
    parser.add_argument('--grant-drop',action='store_true',help='victory chain with real item76 inventory insertion; discovery file write intercepted')
    args=parser.parse_args()
    if args.grant_drop:args.victory_chain=True
    if args.victory_chain:args.death_chain=True
    raw=(ROOT/'S_00.eex').read_bytes()
    predicates=[p for p in json.loads((ROOT/'analysis/eex-predicates/S_00.json').read_text(encoding='utf-8')) if p['segment']==1]
    segment=bytearray(struct.pack('<H',len(predicates)));cursors=[]
    for p in predicates:
        condition=raw[p['instructions'][0]['offset']:p['body_offset']-2]
        enabled=p['branch'] in ((9,10,11) if args.victory_chain else (10,11)) if args.death_chain else p['branch']=={32:12,3:13,33:14}.get(args.ally_death)
        body=raw[p['body_offset']:p['body_offset']+p['body_size']] if enabled else struct.pack('<H',0)
        payload=condition+struct.pack('<H',len(body))+body
        cursors.append(14+len(segment)+2+len(condition));segment+=struct.pack('<H',len(payload))+payload
    file=b'EEX\0\1\2\0\0\0\0'+struct.pack('<I',14)+segment
    unit_source='native-s00-liu-movement-validation.json' if args.ally_death is not None or args.victory_chain else 'native-s00-placed-units.json'
    units=json.loads((ROOT/'analysis'/unit_source).read_text())['units']
    snapshot=next(r['state_after'] for r in reversed(json.loads((ROOT/'analysis/native-s00-unit-setup-replay.json').read_text())['rows']) if r.get('state_after'))
    cases=[dict(name='first-turn-enemy-phase',turn=0,phase=2,flags=[],dead=[]),
           dict(name='first-turn-other-phase',turn=0,phase=0,flags=[],dead=[]),
           dict(name='second-turn-reinforcements',turn=1,phase=0,flags=[],dead=[]),
           dict(name='reinforcements-already-handled',turn=1,phase=0,flags=[12],dead=[]),
           dict(name='zhang-bao-zero-hp',turn=0,phase=2,flags=[],dead=[146]),
           dict(name='both-zhangs-zero-hp',turn=0,phase=2,flags=[],dead=[146,147]),
           dict(name='both-dead-zhang-liang-handled',turn=0,phase=2,flags=[51],dead=[146,147]),
           dict(name='both-dead-zhang-bao-handled',turn=0,phase=2,flags=[50],dead=[146,147]),
           dict(name='both-death-flags-set',turn=2,phase=0,flags=[50,51],dead=[]),
           dict(name='victory-event-handled',turn=2,phase=0,flags=[50,51,100],dead=[])]
    if args.death_chain:cases=[dict(name='death-chain',turn=2,phase=0,flags=[],dead=[146,147])]
    if args.ally_death is not None:cases=[dict(name='ally-death',turn=2,phase=0,flags=[],dead=[args.ally_death])]
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(bytes,units,snapshot,cases,cursors,deathChain,allyDeath,victoryChain,data,grantDrop){
 const b=Process.mainModule.base,file=Memory.alloc(bytes.length);file.writeByteArray(bytes);
 const initialize=new NativeFunction(b.add(0x42613),'void',['pointer','uint8'],'thiscall');
 const select=new NativeFunction(b.add(0x100A1),'uint',['pointer'],'fastcall');
 const execute=new NativeFunction(b.add(0x1084E),'int',['pointer','int','int'],'thiscall');
 const keep=[],effects=[];
 if(deathChain){
  function replace(rva,ret,args,abi,fn){const cb=new NativeCallback(fn,ret,args,abi);keep.push(cb);Interceptor.replace(b.add(rva),cb);}
  replace(0x5965D,'void',['pointer','uint'],'mscdecl',(_text,speaker)=>effects.push({kind:'dialogue',speaker}));
  replace(0x419B6,'void',['pointer','int8'],'thiscall',()=>{});
  replace(0x4197B,'void',['uint'],'mscdecl',()=>{});
  replace(0x54F10,'void',['pointer','uint','int'],'thiscall',()=>{});
  replace(0x5503F,'void',['pointer','uint8','uint8'],'thiscall',()=>{});
  replace(0x7467A,'void',['pointer','uint','int'],'thiscall',()=>{});
  replace(0x3FCC9,'void',['int'],'fastcall',()=>{});
  replace(0x4A88A,'void',['int'],'fastcall',()=>{});
  replace(0x79A01,'void',['uint'],'mscdecl',()=>{});
  if(!grantDrop)replace(0x5991B,'uint',['pointer','uint','uint8','uint','uint','int'],'thiscall',(_o,item,level,mode,actor,enabled)=>{effects.push({kind:'item-request',item,level,mode,actor,enabled});return 1;});
  else{
   replace(0x81100,'int',['pointer'],'mscdecl',()=>0);
   replace(0x2F699,'uint',['uint'],'mscdecl',()=>0);
   replace(0x1A1B0,'void',['uint','uint8'],'mscdecl',(index,value)=>effects.push({kind:'discovery',index,value}));
  }
  if(victoryChain){
   replace(0x53B13,'void',['pointer'],'thiscall',()=>{});
   replace(0x3FD34,'void',['pointer','int'],'thiscall',(slot,mirror)=>{const flag=slot.add(13).readU8();slot.add(13).writeU8(mirror?flag|8:flag&247);});
   replace(0x57428,'uint',['uint','uint','uint8','uint','uint','uint'],'mscdecl',()=>1);
   replace(0x59487,'uint',['int','uint8','uint8','uint'],'mscdecl',(actor,x,y,direction)=>{effects.push({kind:'move-request',actor,x,y,direction});return 1;});
   replace(0x4B5A8,'void',['int','pointer','uint'],'mscdecl',(money,items,mode)=>effects.push({kind:'reward',money,items:Array.from(new Uint8Array(items.readByteArray(3))),mode}));
  }
  Interceptor.flush();
 }
 function unhex(hex){return hex.match(/../g).map(x=>parseInt(x,16));}
 if(victoryChain){
  function buffer(bytes){const p=Memory.alloc(bytes.length);p.writeByteArray(bytes);return p;}
  const loadItem=new NativeFunction(b.add(0x0C537),'pointer',['pointer','pointer'],'thiscall');
  const loadClass=new NativeFunction(b.add(0x093EF),'pointer',['pointer','pointer'],'thiscall');
  const items=buffer(data.items);for(let i=0;i<104;i++)loadItem(b.add(0xA1140+i*25),items.add(i*25));
  let classes=buffer(data.classes);for(let i=0;i<53;i++)classes=loadClass(b.add(0xABFA0+i*27),classes);
 }
 const rows=[];
 for(const c of cases){
  b.add(0x92F90).writeByteArray(snapshot);
  for(let i=0;i<116;i++)initialize(b.add(0xB2C50+i*36),i);
  const map=Memory.alloc(0x3000);map.writeByteArray(new Uint8Array(0x3000).fill(255));
  const view=b.add(0xAEB38);view.add(4).writeU32(0x3000);view.add(12).writePointer(map);view.add(16).writeU8(1);
  b.add(0xB422C).writeU8(20);b.add(0xB422D).writeU8(20);b.add(0xB2C48).writeU32(1);
  for(const u of units){
   const actor=b.add(0xB2C50+u.slot*36);actor.writeByteArray(unhex(u.actorHex));
   b.add(0xA1B68+u.unitId*72).writeByteArray(unhex(u.unitHex));
   if(c.dead.includes(u.unitId))actor.add(16).writeU32(0);
   if(u.type===2)map.add(0xC80+u.position[0]+u.position[1]*20).writeU8(u.slot);
  }
  b.add(0xAC63C).writeU8(3);b.add(0xB3D0A).writeU8(c.turn);b.add(0xB3D18).writeU8(c.phase);
  b.add(0xB5DF0).writeU32(65535);
  b.add(0xB5DF4).writeU32(65535);
  if(victoryChain)b.add(0xB0770+12).writeU32(0);
  if(grantDrop)b.add(0xB0770+0x13).writeByteArray(new Uint8Array(600).fill(255));
  const obj=Memory.alloc(0x2040),refs=Memory.alloc(32),values=Memory.alloc(32);
  values.writeByteArray(new Uint8Array(32));for(let i=0;i<8;i++)refs.add(i*4).writePointer(values.add(i*4));
  obj.writeByteArray(new Uint8Array(0x2040));obj.writePointer(b.add(0x86610));
  obj.add(16).writeU16(65535);obj.add(20).writeS32(-1);obj.add(28).writePointer(refs);
  b.add(0x92F90+28).writePointer(refs);
  obj.add(32).writePointer(file);obj.add(40).writeU32(1);obj.add(48).writeU32(10);
  for(const flag of c.flags)obj.add(0x38+flag*4).writeU32(1);
  if(deathChain){
   const transitions=[];
   for(let i=0;i<(allyDeath!==null?2:victoryChain?4:3);i++){
    obj.add(4).writeU32(0);obj.add(8).writeU32(0);obj.add(16).writeU16(65535);obj.add(20).writeS32(-1);obj.add(40).writeU32(1);
    const selected=select(obj),offset=obj.add(12).readPointer().sub(file).toInt32(),branch=selected?cursors.indexOf(offset):null;
    const ret=(allyDeath!==null?branch===({32:12,3:13,33:14}[allyDeath]):branch===10||branch===11||(victoryChain&&branch===9))?execute(obj,1,0):null;
    const ally=allyDeath!==null?units.find(u=>u.unitId===allyDeath):null;
    transitions.push({branch,ret,flag50:obj.add(0x38+50*4).readU32(),flag51:obj.add(0x38+51*4).readU32(),
      types:[b.add(0xB2C50+35*36+12).readU8(),b.add(0xB2C50+36*36+12).readU8()],
      occupancy:[map.add(0xC80+9+11*20).readU8(),map.add(0xC80+10+11*20).readU8()],
      allyFlag:ally?obj.add(0x38+({32:52,3:53,33:54}[allyDeath])*4).readU32():null,
      allyType:ally?b.add(0xB2C50+ally.slot*36+12).readU8():null,
      allyOccupancy:ally?map.add(0xC80+ally.position[0]+ally.position[1]*20).readU8():null,
      completionFlags:[0,100,600].map(f=>obj.add(0x38+f*4).readU32()),
      money:b.add(0xB0770+12).readU32(),battleState:b.add(0xB3D08+1).readU8()});
    if(grantDrop){
     const inventory=new Uint8Array(b.add(0xB0770+0x13).readByteArray(600));
     transitions[transitions.length-1].dropEntries=Array.from({length:200},(_,s)=>Array.from(inventory.slice(s*3,s*3+3))).filter(entry=>entry[0]!==255);
    }
   }
   rows.push({name:c.name,transitions,effects});
  }else{
   const selected=select(obj),offset=obj.add(12).readPointer().sub(file).toInt32();
   rows.push({name:c.name,selected,branch:selected?cursors.indexOf(offset):null,register5:values.add(20).readU32(),register6:values.add(24).readU32()});
  }
 }
 return rows;
}};
''');script.load()
        tables=dict(entries(ROOT/'Data.e5')) if args.victory_chain else {}
        data=dict(items=list(tables[1]),classes=list(tables[3])) if args.victory_chain else {}
        rows=script.exports_sync.verify(list(file),units,snapshot,cases,cursors,args.death_chain or args.ally_death is not None,args.ally_death,args.victory_chain,data,args.grant_drop)
        if args.victory_chain:
            t=rows[0]['transitions'];effects=rows[0]['effects']
            passed=([r['branch'] for r in t]==[11,10,9,None] and t[0]['flag51']==1 and t[1]['flag50']==1
                    and t[2]['money']==800 and t[2]['battleState']==2 and t[2]['completionFlags']==[1,1,1]
                    and t[1]['occupancy']==[255,255] and t[1]['types']==[3,3]
                    and len([e for e in effects if e['kind']=='move-request'])==6)
            if args.grant_drop:
                passed=passed and t[0]['dropEntries']==[] and all(r['dropEntries']==[[76,255,255]] for r in t[1:])
                passed=passed and [e for e in effects if e['kind']=='discovery']==[dict(kind='discovery',index=79,value=1)]
            report=dict(passed=passed,rows=rows,predicate_count=18,
                        scope='same native interpreter and all18 predicates; original death11/10/full victory9 bodies; zeroHP and captured post-Liu actors supplied; flags50/51 produced by native scripts, treasury800 real; moves/orient/item76 leaves captured, no battle damage or rendering/campaign transition')
            filename='native-s00-death-to-victory-chain.json'
            if args.grant_drop:
                filename='native-s00-death-victory-inventory-chain.json'
                report['scope']='same interpreter/all18 predicates, original death11/10/victory9, real DATA item tables and inventory insertion76 once, discovery callback79 intercepted; zeroHP/post-Liu actors/empty200-slot bag supplied; no item receiver animation, move/orient/display suppressed; not full battle'
            (ROOT/'analysis'/filename).write_text(json.dumps(report,indent=2),encoding='utf-8')
            print(report)
            if not passed:raise SystemExit(1)
            return
        if args.ally_death is not None:
            row=rows[0];t=row['transitions']
            passed=([r['branch'] for r in t]==[{32:12,3:13,33:14}[args.ally_death],None]
                    and t[0]['allyFlag']==1 and t[0]['allyType']==3 and t[0]['allyOccupancy']==255
                    and any(e['kind']=='dialogue' and e['speaker']==args.ally_death for e in row['effects']))
            report=dict(passed=passed,actor=args.ally_death,rows=rows,predicate_count=18,
                        scope='all18 native predicates, original ally death body and removal/flag write; zeroHP supplied after captured Liu event movement; rendering/audio/auto death text suppressed; no attack simulation')
            (ROOT/f'analysis/native-s00-ally-death-{args.ally_death}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
            print(report)
            if not passed:raise SystemExit(1)
            return
        if args.death_chain:
            row=rows[0];t=row['transitions']
            passed=([r['branch'] for r in t]==[11,10,9] and t[0]['flag51']==1 and t[1]['flag50']==1
                    and t[0]['types']==[2,3] and t[1]['types']==[3,3]
                    and t[0]['occupancy']==[35,255] and t[1]['occupancy']==[255,255]
                    and [e['speaker'] for e in row['effects'] if e['kind']=='dialogue']==[147,146]
                    and any(e['kind']=='item-request' and e['item']==76 for e in row['effects']))
            report=dict(passed=passed,rows=rows,predicate_count=18,
                        scope='all18 real predicates; original death bodies11/10 executed with native removal and flags; renderer/audio suppressed; item76 reward leaf captured, not granted; stops at victory candidate9, no victory body or real battle damage')
            (ROOT/'analysis/native-s00-death-chain-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
            print(report)
            if not passed:raise SystemExit(1)
            return
        expected=[1,0,2,None,10,11,10,11,9,None]
        for row,wanted in zip(rows,expected):row['expected']=wanted;row['match']=row['branch']==wanted
        report=dict(rows=rows,passed=all(r['match'] for r in rows),predicate_count=len(predicates),
                    scope='all18 original event predicate byte sequences; actual native selection and condition functions; actors/characters restored from controlled native map0 snapshot; registers5/6 initialized0; bodies replaced by terminators; sampled states only, not full playthrough')
        (ROOT/'analysis/native-s00-full-event-selection.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(report)
        if not report['passed']:raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
