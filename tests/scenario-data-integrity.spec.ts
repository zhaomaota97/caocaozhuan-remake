import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('all migrated scenarios have native units and terrain indexes',()=>{
  const terrain=JSON.parse(readFileSync('data/scenarios/native-terrain-index.json','utf8')) as Record<string,{width:number;height:number;terrain:unknown}>;
  for(let id=0;id<58;id++){
    const key=String(id).padStart(2,'0');
    const data=JSON.parse(readFileSync(`data/scenarios/S_${key}-units-native.json`,'utf8')) as {units?:Array<Record<string,unknown>>};
    expect(data.units?.length,`S_${key} units`).toBeGreaterThan(0);
    expect(data.units?.every(unit=>Array.isArray(unit.position)&&unit.position.length===2&&typeof unit.classId==='number'&&typeof unit.art==='number')).toBe(true);
    const map=terrain[String(id)];
    expect(map,`map ${id} terrain`).toBeTruthy();
    expect(map.width*map.height).toBeGreaterThan(0);
    expect(Array.isArray(map.terrain)?map.terrain.length:(map.terrain as any).value.length).toBe(map.width*map.height);
  }
});
