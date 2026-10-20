import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('ITEM source index audit covers every migrated item without map31 tail references',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/item-palette-coverage.json','utf8'));
  const assets=JSON.parse(readFileSync('data/mappings/battle-item-art.json','utf8'));
  expect(evidence.items).toBe(104);expect(evidence.pixels).toBe(104*1024);
  expect(evidence.rows.map((row:any)=>row.itemId)).toEqual(assets.rows.map((row:any)=>row.itemId));
  for(const row of evidence.rows){
    expect(row.pixels).toBe(1024);expect(row.maximumIndex).toBeLessThanOrEqual(173);expect(row.tailPixels).toBe(0);
  }
  expect(evidence.palettes.find((row:any)=>row.paletteEntry===31)).toMatchObject({bytes:738,missingUsedIndexes:[],affectedPixels:0});
});
