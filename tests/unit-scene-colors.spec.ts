import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
test('all 453 unit animation resources have scene-independent source colors',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/unit-scene-colors.json','utf8'));
  expect(evidence.families.map((row:any)=>row.family)).toEqual(['atk','mov','spc']);
  expect(evidence.families.map((row:any)=>row.pixels)).toEqual([151*64*64*12,151*48*48*11,151*48*48*5]);
  for(const family of evidence.families){
    expect(family.resources).toBe(151);expect(family.colorProfiles).toBe(1);
    expect(family.rows.map((row:any)=>row.paletteEntry)).toEqual(Array.from({length:58},(_,i)=>i));
    expect(new Set(family.rows.map((row:any)=>row.visibleColorSha256)).size).toBe(1);
    for(const row of family.rows){expect(row.missingUsedIndexes).toEqual([]);expect(row.changedIndexesFrom31).toEqual([]);expect(row.affectedResources).toEqual([]);}
  }
});
