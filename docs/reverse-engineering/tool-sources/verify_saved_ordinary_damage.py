"""Compare ordinary deterministic native damage for all saved attacker/defender pairs."""
import ast
import json
from pathlib import Path
import frida
from export_map_layouts import entries
from game_rng import GameRng

ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'tools/export_slot08_native_health.py').read_text(encoding='utf-8'))
sources=[node.args[0].value for node in ast.walk(tree) if isinstance(node,ast.Call)
         and isinstance(node.func,ast.Attribute) and node.func.attr=='create_script'
         and isinstance(node.args[0],ast.Constant)]
if len(sources)!=1 or sources[0].count('return out;')!=1:
    raise RuntimeError('Review native initialization')
source=sources[0].replace('return out;', '''
 const attack=new NativeFunction(b.add(0x3f4fe),'uint',['pointer'],'fastcall');
 const defense=new NativeFunction(b.add(0x3f595),'uint',['pointer'],'fastcall');
 const adaptation=new NativeFunction(b.add(0x3f84d),'uint',['pointer'],'fastcall');
 const agility=new NativeFunction(b.add(0x3f631),'uint',['pointer'],'fastcall');
 const luck=new NativeFunction(b.add(0x3f67f),'uint',['pointer'],'fastcall');
 const critical=new NativeFunction(b.add(0x5d69),'uint',['pointer'],'fastcall');
 const doubleChance=new NativeFunction(b.add(0x5ce6),'uint',['pointer'],'fastcall');
 const action=Memory.alloc(0x620);
 const metadataCallbacks=[];
 for(const rva of [0x379b,0x397d,0x3a85]){
  const cb=new NativeCallback(()=>0,'uint',['pointer','uint'],'thiscall');
  metadataCallbacks.push(cb);Interceptor.replace(b.add(rva),cb);
 }
 Interceptor.flush();
 const generateResult=new NativeFunction(b.add(0x5e03),'void',['pointer'],'fastcall');
 const repeat=new NativeFunction(b.add(0x6181),'uint',['pointer'],'fastcall');
 const presentation=new NativeCallback(()=>{},'void',['uint8','uint8','int','int','uint','uint','uint','int'],'mscdecl');
 const reward=new NativeCallback(()=>{},'void',['pointer','uint8','int'],'thiscall');
 const autoItem=new NativeCallback(()=>0,'int',['pointer','uint8','uint8','int','int'],'thiscall');
 Interceptor.replace(b.add(0x50984),presentation);Interceptor.replace(b.add(0x82d6),reward);
 Interceptor.replace(b.add(0x1dc43),autoItem);Interceptor.flush();
 const writeResult=new NativeFunction(b.add(0x5889),'void',['pointer'],'fastcall');
 const accuracy=new NativeFunction(b.add(0x3b50d),'uint',['pointer','int','pointer'],'thiscall');
 const damage=new NativeFunction(b.add(0x3bc4b),'uint',['pointer','pointer','int','int'],'thiscall');
 const actorStats=out.map(row=>{
  const a=b.add(0xb2c50+row.slot*36);
  return {...row,attack:attack(a),defense:defense(a),adaptation:adaptation(a)&255,
    agility:agility(a),luck:luck(a),statusFlags:a.add(30).readU8(),actorFlags:a.add(13).readU8()};
 });
 const rows=[];
 for(const attacker of actorStats)for(const defender of actorStats){
  if(attacker.slot===defender.slot)continue;
  const a=b.add(0xb2c50+attacker.slot*36),d=b.add(0xb2c50+defender.slot*36);
  action.add(12).writePointer(a);action.add(8).writePointer(b.add(0xa1b68+a.readU32()*72));action.add(1).writeU8(defender.slot);
  for(const counter of [0,1]){
   const live=[];
   for(const seed of [0,1,7,0xffffffff]){
    b.add(0x8ecd4).writeU32(seed);
    const value=damage(a,b.add(0xa1b68+d.readU32()*72),1,counter);
    const entry={seed,native:value,state:b.add(0x8ecd4).readU32(),results:[]};
    for(const round of [0,1]){
     action.writeByteArray(new Uint8Array(0x620));
     action.add(12).writePointer(a);action.add(8).writePointer(b.add(0xa1b68+a.readU32()*72));
     action.add(1).writeU8(defender.slot);action.add(16).writeByteArray(new Uint8Array(116).fill(255));
     action.add(16).writeU8(defender.slot);action.add(0x608).writeU8(round);
     b.add(0x92e04).writeU8(counter);b.add(0x8ecd4).writeU32(seed);
     generateResult(action);
     const generated={round,hpDamage:action.add(0x84).readU32(),mpDamage:action.add(0x254).readU32(),
       critical:action.add(0x604).readU32()!==0,state:b.add(0x8ecd4).readU32()};
     const snapshot=new Uint8Array(d.readByteArray(36));action.writeU8(attacker.slot);
     writeResult(action);
     generated.writeback={hp:d.add(16).readU32(),mp:d.add(20).readU32(),status:d.add(30).readU8(),
       flags:d.add(13).readU8(),state:b.add(0x8ecd4).readU32()};
     d.writeByteArray(snapshot);b.add(0x8ecd4).writeU32(generated.state);
     generated.repeat=repeat(action)!==0;generated.repeatState=b.add(0x8ecd4).readU32();
     generated.criticalReset=action.add(0x604).readU32()===0;
     entry.results.push(generated);
    }
    live.push(entry);
   }
   rows.push({attacker:attacker.slot,defender:defender.slot,counter,live,
    native:damage(a,b.add(0xa1b68+d.readU32()*72),0,counter),nativeAccuracy:accuracy(a,0,d),
    nativeCritical:critical(action)&255,nativeDouble:doubleChance(action)&255});
  }
 }
 const first=b.add(0xb2c50+actorStats[0].slot*36),equippedUnit=b.add(0xa1b68+first.readU32()*72);
 const previous=equippedUnit.add(0x34).readU8(),yuxiChecks=[];equippedUnit.add(0x34).writeU8(82);
 action.add(12).writePointer(first);action.add(8).writePointer(equippedUnit);
 for(const target of actorStats){
  if(target.slot===actorStats[0].slot)continue;
  action.add(1).writeU8(target.slot);yuxiChecks.push({target:target.slot,chance:critical(action)&255});
 }
 equippedUnit.add(0x34).writeU8(previous);
 return {actors:actorStats,rows,yuxiChecks};
''')
data=dict(entries(ROOT/'Data.e5'))
def category_values(actor,category):
    values=[]
    for slot in actor['equipmentSlots']:
        if slot['itemId']==255:
            continue
        record=data[1][slot['itemId']*25:(slot['itemId']+1)*25]
        if slot['slot']<2 and record[17]<18 and record[17]&1 and record[18]==category:
            values.append(record[22])
        elif slot['slot']==2 and record[17]==category:
            values.append(record[21])
    return values

device=frida.get_local_device()
pid=device.spawn([str(ROOT/'analysis/runtime-game/Ekd5.exe')],cwd=str(ROOT/'analysis/runtime-game'))
session=None
try:
    session=device.attach(pid);script=session.create_script(source);script.load()
    result=script.exports_sync.read(list(data[0]),list(data[1]),list(data[3]),list(data[4]),
        list((ROOT/'Sv08d.e5s').read_bytes()[0x14dc:]),
        list((ROOT/'Sv08s.e5s').read_bytes()[1301:4291]),
        list((ROOT/'analysis/saved-battlefields/Sv08s-terrain.bin').read_bytes()))
    actors={row['slot']:row for row in result['actors']}
    for row in result['rows']:
        a,d=actors[row['attacker']],actors[row['defender']]
        av=a['attack']*a['adaptation']//10;dv=d['defense']*d['adaptation']//10
        value=max(1,a['nativeLevel']+25-(dv-av)//2) if av<dv else a['nativeLevel']+25+(av-dv)//2
        kind=lambda actor:actor['classId']//3 if actor['classId']<39 else actor['classId']-26
        ak,dk=kind(a),kind(d)
        if ak==1:
            if dk==3:value=max(1,value*3//5)
            elif dk in (2,5):value=value*3//2
        elif ak in (2,4,5):
            if dk in (3,17,16):value=value*3//2
            modifiers=category_values(d,61)
            if modifiers:value-=modifiers[-1]*value//100
        modifiers=category_values(a,45)
        if dk==3 and modifiers:value+=modifiers[-1]*value//100
        if row['counter']:value=max(1,value*3//4)
        row['expected']=min(value,d['hp']);row['match']=row['native']==row['expected']
        aa,da=a['agility'],d['agility']
        if ak in (2,4,5) and category_values(d,56):
            chance=0
        elif d['statusFlags']&8:
            chance=100
        else:
            if aa>=da*2:chance=100
            elif aa>=da:chance=90+(aa-da)*10//da
            elif aa>=da//2:chance=60+max(0,aa-da//2)*30//(da//2)
            else:chance=30+max(0,aa-da//3)*30//(da//3)
            chance=min(100,chance+(category_values(a,39) or [0])[-1])
            chance=max(0,chance-(category_values(d,53) or [0])[-1])
            chance=max(0,chance-(category_values(d,55) or [0])[-1])
        row['expectedAccuracy']=chance
        row['accuracyMatch']=row['nativeAccuracy']==chance
        def followup(a_value,d_value):
            if a_value>=3*d_value:return 100
            if a_value>=2*d_value:return 20+(a_value-2*d_value)*80//d_value
            if a_value>=d_value:return 2+(a_value-d_value)*18//d_value
            return 1
        row['criticalMatch']=row['nativeCritical']==(100 if category_values(a,41) else followup(a['luck'],d['luck']))
        row['doubleMatch']=row['nativeDouble']==followup(a['agility'],d['agility'])
        for live in row['live']:
            rng=GameRng(live['seed'])
            if rng.chance(chance):
                draw=rng.bounded(7)
                expected=max(1,value-draw) if draw<3 else value-2+draw
                expected=min(expected,d['hp'])
            else:expected=0
            live['expected']=expected
            live['match']=expected==live['native'] and rng.state==live['state']
            for generated in live['results']:
                follow_rng=GameRng(live['state'])
                is_critical=follow_rng.chance(row['nativeCritical'])
                result_damage=live['native']
                if is_critical:
                    result_damage=0 if category_values(d,57) else result_damage*3//2
                if generated['round'] and category_values(d,58):result_damage=0
                mp_damage=min(result_damage,d['mp']) if category_values(d,60) and d['mp'] else 0
                hp_damage=0 if category_values(d,60) and d['mp'] else min(result_damage,d['hp'])
                generated['match']=(generated['hpDamage']==hp_damage and generated['mpDamage']==mp_damage
                    and generated['critical']==is_critical and generated['state']==follow_rng.state)
                status_rng=GameRng(generated['state']);status=d['statusFlags']
                if hp_damage or mp_damage:
                    for category,mask,special_class in [(35,8,50),(36,16,49),(37,2,42),(38,4,None)]:
                        if category_values(a,category):status|=mask
                        if a['classId']==special_class and status_rng.chance(60):status|=mask
                expected_writeback={'hp':d['hp']-hp_damage,'mp':d['mp']-mp_damage,'status':status,
                    'flags':d['actorFlags']&~32,'state':status_rng.state}
                generated['writebackMatch']=generated['writeback']==expected_writeback
                repeated=follow_rng.chance(row['nativeDouble']) if not row['counter'] and generated['round']==0 else False
                generated['repeatMatch']=(generated['repeat']==repeated and generated['repeatState']==follow_rng.state
                                          and generated['criticalReset'])
    result.update(function='0x43BC4B',mode=0,total=len(result['rows']),
                  matched=sum(row['match'] for row in result['rows']))
    (ROOT/'analysis/native-saved-ordinary-damage.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f"Native saved ordinary damage: {result['matched']}/{result['total']}")
    if result['matched']!=result['total']:
        raise SystemExit('Ordinary damage mismatch')
    print(f"Native saved ordinary accuracy: {sum(row['accuracyMatch'] for row in result['rows'])}/{result['total']}")
    if not all(row['accuracyMatch'] for row in result['rows']):
        raise SystemExit('Ordinary accuracy mismatch')
    live_cases=[case for row in result['rows'] for case in row['live']]
    print(f"Native live ordinary strikes and RNG states: {sum(case['match'] for case in live_cases)}/{len(live_cases)}")
    if not all(case['match'] for case in live_cases):
        raise SystemExit('Live damage/RNG mismatch')
    if not all(row['criticalMatch'] and row['doubleMatch'] for row in result['rows']):
        raise SystemExit('Critical/double chance mismatch')
    if not all(row['chance']==100 for row in result['yuxiChecks']):
        raise SystemExit('Yuxi must give 100 percent critical chance')
    print(f"Native critical/double chances: {result['total']}/{result['total']}; Yuxi {len(result['yuxiChecks'])}/{len(result['yuxiChecks'])}")
    generated_cases=[generated for row in result['rows'] for live in row['live'] for generated in live['results']]
    print(f"Native attack results: {sum(row['match'] for row in generated_cases)}/{len(generated_cases)}")
    if not all(row['match'] for row in generated_cases):raise SystemExit('Attack result mismatch')
    print(f"Native repeat decisions and RNG states: {sum(row['repeatMatch'] for row in generated_cases)}/{len(generated_cases)}")
    if not all(row['repeatMatch'] for row in generated_cases):raise SystemExit('Repeat decision mismatch')
    print(f"Native HP/MP/status writebacks: {sum(row['writebackMatch'] for row in generated_cases)}/{len(generated_cases)}")
    if not all(row['writebackMatch'] for row in generated_cases):raise SystemExit('Writeback mismatch')
    fixture={'actors':[{key:row[key] for key in ('slot','classId','equipmentSlots','attack','defense','adaptation','nativeLevel','hp','mp','agility','luck','statusFlags','actorFlags')}
                       for row in result['actors']],'rows':result['rows']}
    (ROOT.parent/'caocaozhuan-remake/tests/fixtures/native-ordinary-damage.json').write_text(
        json.dumps(fixture,indent=2)+'\n',encoding='utf-8')
finally:
    device.kill(pid)
    if session:session.detach()
