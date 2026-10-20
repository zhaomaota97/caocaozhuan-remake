"""Execute all58 level-entry prefixes with an explicit default party fixture."""
import csv
import json
import struct
from pathlib import Path
import frida
from export_eex_bodies import encode_block

ROOT=Path(__file__).resolve().parents[1]


def main():
    cases=[]
    for path in sorted((ROOT/'analysis/eex-bodies').glob('S_*.json')):
        branch=json.loads(path.read_text(encoding='utf-8'))[0]
        scene=next(n for n in branch['nodes'] if n['opcode']==39)
        nodes=[n for n in branch['nodes'] if n['offset']<=scene['offset']]
        body=encode_block(dict(nodes=nodes+[dict(opcode=0)]))
        start=nodes[0]['offset'];end=scene['end']
        if body[:-2]!=(ROOT/f'{path.stem}.eex').read_bytes()[start:end]:raise ValueError(f'{path.stem} prefix not original')
        predicate=struct.pack('<HH',2,5)+b'\0'+b'\0\0'
        payload=predicate+struct.pack('<H',len(body))+body
        file=b'EEX\0\1\2\0\0\0\0'+struct.pack('<I',14)+struct.pack('<HH',1,len(payload))+payload
        cases.append(dict(script=path.stem+'.eex',source_start=start,source_end=end,
                          mapId=scene['arguments'][4]['value'],bytes=list(file)))
    device=frida.get_local_device();runtime=ROOT/'analysis/runtime-game'
    pid=device.spawn([str(runtime/'Ekd5.exe')],cwd=str(runtime));session=None
    try:
        session=device.attach(pid)
        script=session.create_script('''
rpc.exports={verify(cases,party){
  party=party||[0];
 const b=Process.mainModule.base;
 const select=new NativeFunction(b.add(0x100A1),'uint',['pointer'],'fastcall');
 const execute=new NativeFunction(b.add(0x1084E),'int',['pointer','int','int'],'thiscall');
 const rows=[];
 for(const c of cases){
  b.add(0x92F90).writeByteArray(new Uint8Array(0x4000));
  b.add(0xA1B68).writeByteArray(new Uint8Array(512*72));
  b.add(0xB0770).writeByteArray(new Uint8Array(0x300));
  for(let i=0;i<16;i++)b.add(0x8B350+i*4).writeU32(i<party.length?party[i]:65535);
  b.add(0xB09EC).writeU8(party.length);
  b.add(0xAC63C).writeU8(0);b.add(0xABF9C).writeU32(0);
  const input=Memory.alloc(c.bytes.length),obj=Memory.alloc(0x2040);
  input.writeByteArray(c.bytes);obj.writeByteArray(new Uint8Array(0x2040));
  obj.writePointer(b.add(0x86610));obj.add(16).writeU16(65535);obj.add(20).writeS32(-1);
  obj.add(32).writePointer(input);obj.add(40).writeU32(1);obj.add(48).writeU32(10);
  const selected=select(obj);let result=null,error=null;
  try{result=selected?execute(obj,1,0):null;}catch(e){error=String(e);}
  const records=[];
  for(let i=0;i<115;i++){
   const r=b.add(0x92F90+0x2044+i*64);if(r.readU32()===65535)continue;
   records.push({sourceSlot:i,unitId:r.readU32(),coordinates:[r.add(4).readU8(),r.add(5).readU8()],
    flags:r.add(8).readU32(),levelSetting:r.add(17).readU8(),
    recordHex:Array.from(new Uint8Array(r.readByteArray(64))).map(x=>x.toString(16).padStart(2,'0')).join('')});
  }
  rows.push({script:c.script,selected,result,error,mapId:b.add(0xB3D08).readU8(),mode:b.add(0xAC63C).readU8(),records,
   stateHex:Array.from(new Uint8Array(b.add(0x92F90).readByteArray(0x4000))).map(x=>x.toString(16).padStart(2,'0')).join('')});
  if(error)break;
 }
 return rows;
}};
''');script.load();rows=script.exports_sync.verify(cases)
        names={int(r['id']):r['name_gbk'] for r in csv.DictReader((ROOT/'analysis/characters.csv').open(encoding='utf-8-sig'))}
        output=ROOT/'analysis/level-prefixes-native';output.mkdir(exist_ok=True)
        dest=ROOT.parent/'caocaozhuan-remake/data/scenarios/native-prefixes';dest.mkdir(exist_ok=True)
        index=[]
        for case,row in zip(cases,rows):
            row['source_offsets']=[case['source_start'],case['source_end']]
            row['passed']=row['selected']==1 and row['result']==2 and not row['error'] and row['mapId']==case['mapId'] and row['mode']==3
            groups={0:0,2:15,1:35}
            for unit in row['records']:
                unit['name']=names.get(unit['unitId'])
                key=unit['flags']&3;key=key if key in (0,2) else 1
                unit['battleSlot']=groups[key];groups[key]+=1
                unit['initiallyHidden']=bool(unit['flags']&4)
            row['scope']='original entire pre-map prefix, real native interpreter/handlers; default party=[Cao0], zeroed character/campaign tables; preset records only, no real player progression or post-map initialization'
            text=json.dumps(row,ensure_ascii=False,indent=2)
            filename=Path(row['script']).stem+'.json'
            (output/filename).write_text(text,encoding='utf-8');(dest/filename).write_text(text,encoding='utf-8')
            index.append(dict(script=row['script'],mapId=row['mapId'],records=len(row['records']),
                              hidden=sum(u['initiallyHidden'] for u in row['records']),passed=row['passed']))
        report=dict(scripts=len(rows),passed=sum(r['passed'] for r in index),rows=index,
                    fixture='party=[0], character table and campaign state zeroed; campaign-independent presets cannot stand in for actual player army')
        (ROOT/'analysis/all-level-prefixes-native.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        (dest/'index.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        lines=['# 全58关原生初始化前缀索引','',
               '原文件地图切换前的全部节点逐字节重编码，原版选择器/解释器实际执行；58/58通过，下面的记录数是默认队伍fixture下的预设，不是实际战役出战人数。',
               '', '固定输入：party=[曹操0]，角色表和战役状态清零；地图切换后的属性展开、出场剧情、玩家成长、AI、胜败与Web均未在本批次执行。',
               '', '| 脚本 | 地图 | 预设记录 | 初始隐藏位记录 | 前缀验证 |', '|---|---:|---:|---:|---|']
        for r in index:
            lines.append(f'| [{r["script"]}](level-prefixes-native/{Path(r["script"]).stem}.json) | {r["mapId"]} | {r["records"]} | {r["hidden"]} | {"通过" if r["passed"] else "未通过"} |')
        lines.extend(['',f'共{sum(r["records"] for r in index)}条预设；完整一致可玩关卡验收仍为0/58。',
                      '', '复现：`python tools/export_all_level_prefixes_native.py`。',
                      '', 'JSON另迁入remake `data/scenarios/native-prefixes/`。不可把固定路径观测、固定曹操队伍或清零角色表当作完整战役初始化。'])
        (ROOT/'analysis/all-level-prefixes-native.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        print(f'All native level prefixes: {report["passed"]}/{len(cases)}; exported records={sum(r["records"] for r in index)}')
        if len(rows)!=58 or report['passed']!=58:
            print([r for r in rows if r.get('error')]);raise SystemExit(1)
    finally:
        if session:session.detach()
        device.kill(pid)


if __name__=='__main__':main()
