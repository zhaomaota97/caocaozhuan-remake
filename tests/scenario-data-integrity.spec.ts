import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('all migrated scenarios have native units and terrain indexes',()=>{
  const readJson=(path:string)=>JSON.parse(readFileSync(path,'utf8').replace(/^\uFEFF/,''));
  const terrain=readJson('data/scenarios/native-terrain-index.json') as Record<string,{width:number;height:number;terrain:unknown}>;
  for(let id=0;id<58;id++){
    const key=String(id).padStart(2,'0');
    const data=readJson(`data/scenarios/S_${key}-units-native.json`) as {units?:Array<Record<string,unknown>>};
    expect(data.units?.length,`S_${key} units`).toBeGreaterThan(0);
    expect(data.units?.every(unit=>{
      const native=(unit.controlledNativeExpansion??unit.nativePlacement??unit) as Record<string,unknown>;
      const position=unit.position??unit.coordinateBytes??native.position;
      return Array.isArray(position)&&position.length===2&&typeof native.classId==='number'&&typeof native.art==='number';
    })).toBe(true);
    const map=terrain[String(id)];
    expect(map,`map ${id} terrain`).toBeTruthy();
    expect(map.width*map.height).toBeGreaterThan(0);
    expect(Array.isArray(map.terrain)?map.terrain.length:(map.terrain as any).value.length).toBe(map.width*map.height);
  }
});
