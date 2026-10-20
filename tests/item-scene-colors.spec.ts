import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
test('all original scene palettes share the migrated ITEM source color profile',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/item-scene-colors.json','utf8'));
  const coverage=JSON.parse(readFileSync('docs/reverse-engineering/item-palette-coverage.json','utf8'));
  expect(evidence.items).toBe(104);expect(evidence.palettes).toBe(58);expect(evidence.colorProfiles).toBe(1);
  expect(evidence.usedIndexes).toEqual(coverage.usedIndexes.filter((index:number)=>index!==0));
  expect(evidence.rows.map((row:any)=>row.paletteEntry)).toEqual(Array.from({length:58},(_,i)=>i));
  expect(new Set(evidence.rows.map((row:any)=>row.visibleColorSha256)).size).toBe(1);
  for(const row of evidence.rows){expect(row.changedIndexesFrom31).toEqual([]);expect(row.affectedItems).toEqual([]);}
});
