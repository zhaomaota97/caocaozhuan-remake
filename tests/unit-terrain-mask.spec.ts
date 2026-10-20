import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeUnitTerrainMask} from '../src/rules/unitTerrainMask';
test('unit terrain clipping matches all 32000 captured native pixels',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-unit-terrain-mask.json','utf8'));
  const masks=JSON.parse(readFileSync('data/mappings/unit-terrain-masks.json','utf8')).rows;
  const resources=JSON.parse(readFileSync('docs/SOURCE-MIGRATION-MANIFEST.json','utf8'));
  const raw=readFileSync(resources.entries.find((entry:any)=>entry.name.toLowerCase()==='mark.e5').destination);
  expect(evidence.total).toBe(10);expect(evidence.passed).toBe(10);
  for(const row of evidence.rows){
    expect([...raw.subarray(row.offset,row.offset+row.size*row.size)]).toEqual(row.mask);
    const source=Uint8Array.from({length:row.size*row.size},(_,i)=>i&255);
    expect([...nativeUnitTerrainMask(source,row.size,row.terrain,masks)]).toEqual(row.pixels);
    expect(source[1]).toBe(1);
  }
});

test('terrain mask selection matches all 14 original unit draw wrapper executions',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-unit-terrain-draw.json','utf8'));
  const masks=JSON.parse(readFileSync('data/mappings/unit-terrain-masks.json','utf8')).rows;
  expect(evidence.total).toBe(14);expect(evidence.passed).toBe(14);
  for(const row of evidence.rows){
    const source=Uint8Array.from({length:row.size*row.size},(_,i)=>i&255);
    const mask=masks.find((entry:any)=>entry.size===row.size&&entry.terrain===row.terrain);
    expect(row.offsets).toEqual(mask?[mask.offset]:[]);
    expect([...nativeUnitTerrainMask(source,row.size,row.terrain,masks)]).toEqual(row.pixels);
  }
});
