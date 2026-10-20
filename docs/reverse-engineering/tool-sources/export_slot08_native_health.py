"""Export actual saved actor health and native maximum-health/pose predicates."""
import json
import csv
from pathlib import Path
import frida
from export_map_layouts import entries

ROOT = Path(__file__).resolve().parents[1]
data = dict(entries(ROOT / 'Data.e5'))
roster = (ROOT / 'Sv08d.e5s').read_bytes()[0x14dc:]
actors = (ROOT / 'Sv08s.e5s').read_bytes()[1301:4291]
device = frida.get_local_device()
pid = device.spawn([str(ROOT / 'analysis/runtime-game/Ekd5.exe')], cwd=str(ROOT / 'analysis/runtime-game'))
session = None
try:
    session = device.attach(pid)
    script = session.create_script('''
rpc.exports={music(config){
 const b=Process.mainModule.base, obj=Memory.alloc(0x400), input=Memory.alloc(config.length);
 obj.writeByteArray(new Uint8Array(0x400));input.writeByteArray(config);
 new NativeFunction(b.add(0xcc65),'pointer',['pointer','pointer'],'thiscall')(obj,input);
 return new NativeFunction(b.add(0x1c2b0),'uint8',['pointer'],'fastcall')(obj);
},read(source,items,classTable,terrainTable,roster,actors,terrain){
 const b=Process.mainModule.base;
 // Suspended-process harness has no initialized CRT atexit list; omit registration only.
 const exitRegistration=new NativeCallback(()=>0,'int',['pointer'],'mscdecl');
 Interceptor.replace(b.add(0x81100),exitRegistration);Interceptor.flush();
 function buf(bytes){const p=Memory.alloc(bytes.length);p.writeByteArray(bytes);return p;}
 const expand=new NativeFunction(b.add(0x8be3),'pointer',['pointer','uint16','pointer','int'],'thiscall');
 const item=new NativeFunction(b.add(0xc537),'pointer',['pointer','pointer'],'thiscall');
 const unit=new NativeFunction(b.add(0x9188),'pointer',['pointer','pointer'],'thiscall');
 const actor=new NativeFunction(b.add(0x42e26),'pointer',['pointer','pointer'],'thiscall');
 const loadClass=new NativeFunction(b.add(0x93ef),'pointer',['pointer','pointer'],'thiscall');
 let classInput=buf(classTable);
 for(let i=0;i<53;i++)classInput=loadClass(b.add(0xabfa0+i*27),classInput);
 const maxHp=new NativeFunction(b.add(0x721b),'uint',['pointer','uint'],'fastcall');
 const maxMp=new NativeFunction(b.add(0x724a),'uint',['pointer','uint'],'fastcall');
 const level=new NativeFunction(b.add(0x65d0),'uint8',['pointer'],'fastcall');
 const injured=new NativeFunction(b.add(0x4015a),'uint',['pointer','uint'],'fastcall');
 const moveBudget=new NativeFunction(b.add(0x3f74f),'uint8',['pointer'],'fastcall');
 const moveCost=new NativeFunction(b.add(0x3f7cf),'uint',['pointer','uint'],'thiscall');
 const equipmentCategory=new NativeFunction(b.add(0x7a09),'uint',['pointer','uint','int'],'fastcall');
 b.add(0xae4e0).writeByteArray(terrainTable);
 const src=buf(source),it=buf(items),rs=buf(roster),ac=buf(actors),out=[];
 for(let i=0;i<512;i++){expand(b.add(0xa1b68+i*72),i,src.add(i*32),0);unit(b.add(0xa1b68+i*72),rs.add(i*32));}
 for(let i=0;i<104;i++)item(b.add(0xa1140+i*25),it.add(i*25));
 for(let i=0;i<115;i++){
  const a=b.add(0xb2c50+i*36);actor(a,ac.add(i*26));
  if(a.add(12).readU8()!==2)continue;
  const u=b.add(0xa1b68+a.readU32()*72);
  out.push({slot:i,hp:a.add(16).readU32(),maxHp:maxHp(u,0),injuredPose:injured(a,0)!==0,
    mp:a.add(20).readU32(),maxMp:maxMp(u,0),nativeLevel:level(u),classId:u.add(0x2b).readU8(),
    ignoresEnemyAdjacency:equipmentCategory(u,0,33)!==0,
    movementTier:a.add(0x1d).readU8(),
    nativeEquipmentCategories:Array.from({length:256},(_,category)=>equipmentCategory(u,0,category)!==0),
    equipmentSlots:Array.from({length:3},(_,slot)=>({slot,itemId:u.add(0x2e+slot*3).readU8(),byte1:u.add(0x2f+slot*3).readU8(),byte2:u.add(0x30+slot*3).readU8()})),
    move:moveBudget(a),terrainCosts:Array.from({length:30},(_,terrain)=>moveCost(a,terrain)&255)});
 }
 function view(rva){
  const pixels=Memory.alloc(0x3000);pixels.writeByteArray(new Uint8Array(0x3000).fill(255));
  const v=b.add(rva);v.add(4).writeU32(0x3000);v.add(12).writePointer(pixels);v.add(16).writeU8(1);
  return pixels;
 }
 const battlefield=view(0xaeb38);view(0xaab68);
 battlefield.add(0x640).writeByteArray(terrain);
 b.add(0xb422c).writeU8(20);b.add(0xb422d).writeU8(32);
 for(const row of out){
  const a=b.add(0xb2c50+row.slot*36);
  battlefield.add(0xc80+a.add(7).readU8()*20+a.add(6).readU8()).writeU8(row.slot);
 }
 const search=new NativeFunction(b.add(0x38308),'uint8',['pointer','pointer','uint','uint','uint','uint','int'],'thiscall');
 const restriction=new NativeFunction(b.add(0x37d59),'uint',['pointer','pointer'],'thiscall');
 const coordinate=Memory.alloc(2);
 for(const row of out){
  const a=b.add(0xb2c50+row.slot*36);
  row.nativeStopExpansion=Array.from({length:640},(_,index)=>{
    coordinate.writeU8(index%20);coordinate.add(1).writeU8(Math.floor(index/20));
    return restriction(a,coordinate)!==0;
  });
  row.searchResult=search(a,a.add(6),row.move,0,255,255,1);
  row.nativeMovementCosts=Array.from(new Uint8Array(battlefield.add(0x12c0).readByteArray(640)));
 }
 return out;
}};
''')
    script.load()
    terrain=(ROOT/'analysis/saved-battlefields/Sv08s-terrain.bin').read_bytes()
    rows = script.exports_sync.read(list(data[0]), list(data[1]), list(data[3]), list(data[4]), list(roster), list(actors), list(terrain))
    path = ROOT / 'analysis/slot08-native-health.json'
    path.write_text(json.dumps(rows, indent=2), encoding='utf-8')
    save_path = ROOT.parent / 'caocaozhuan-remake/data/saves/slot-08.json'
    save = json.loads(save_path.read_text(encoding='utf-8-sig'))
    config = (ROOT / 'Sv08d.e5s').read_bytes()[0x32:0x2da]
    track = script.exports_sync.music(list(config))
    mapping = json.loads((ROOT / 'analysis/native-music-mapping-validation.json').read_text())
    music = next(row for row in mapping['rows'] if row['track'] == track and row['match'])
    save['bgmTrack'] = track
    save['bgm'] = music['selected'].replace('\\', '/').split('/')[-1]
    save['bgmStatus'] = 'verified-save-native-mapping'
    save['bgmEvidence'] = {'saveOffset': '0x3B', 'deserialize': '0x40CC65', 'readTrack': '0x41C2B0', 'battleStartup': '0x44D092'}
    by_slot = {r['slot']: r for r in rows}
    with (ROOT/'analysis/items.csv').open(encoding='utf-8-sig') as file:
        item_names={int(item['id']):item['name'] for item in csv.DictReader(file)}
    item_definitions=[]
    for item_id in range(104):
        record=data[1][item_id*25:(item_id+1)*25]
        item_definitions.append({'id':item_id,'name':item_names[item_id],
                                 'categoryByte':record[17],'equipmentEffectCategory':record[18],
                                 'baseValue':record[21],'secondaryValue':record[22]})
    item_path=ROOT.parent/'caocaozhuan-remake/data/rules/item-categories.json'
    item_path.write_text(json.dumps(item_definitions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    terrain_definitions=[{'movementType':kind,'adaptation':list(data[4][kind*60:kind*60+30]),
                          'costs':list(data[4][kind*60+30:(kind+1)*60])} for kind in range(27)]
    terrain_path=ROOT.parent/'caocaozhuan-remake/data/rules/terrain-movement.json'
    terrain_path.write_text(json.dumps(terrain_definitions,indent=2)+'\n',encoding='utf-8')
    classes=[{'id':index,'baseMove':data[3][index*27]} for index in range(53)]
    (ROOT.parent/'caocaozhuan-remake/data/rules/class-movement.json').write_text(json.dumps(classes,indent=2)+'\n',encoding='utf-8')
    for u in save['actors']:
        r = by_slot[int(u['id'].split('-')[1])]
        u.update(hp=r['hp'], maxHp=r['maxHp'], injuredPose=r['injuredPose'], move=r['move'], terrainCosts=r['terrainCosts'])
        u.update(mp=r['mp'],maxMp=r['maxMp'],nativeLevel=r['nativeLevel'],classId=r['classId'])
        u['equipmentSlots']=[dict(item,name=item_names.get(item['itemId'])) for item in r['equipmentSlots']]
        u['nativeMovementCosts']=r['nativeMovementCosts']
        u['nativeStopExpansion']=r['nativeStopExpansion']
        u['ignoresEnemyAdjacency']=r['ignoresEnemyAdjacency']
        u['movementTier']=r['movementTier']
    save_path.write_text(json.dumps(save, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Exported native health/pose for {len(rows)} actors; injured={sum(r['injuredPose'] for r in rows)}")
finally:
    device.kill(pid)
    if session:
        session.detach()
