import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeConsumableCount} from '../src/rules/consumableInventory';

test('ten native saved inventory exports preserve all 170 stock bytes',()=>{
  const evidence=JSON.parse(readFileSync('data/saves/consumable-stock.json','utf8'));
  const manifest=JSON.parse(readFileSync('docs/SOURCE-MIGRATION-MANIFEST.json','utf8'));
  expect(evidence.rows).toHaveLength(10);
  for(const row of evidence.rows){
    const entry=manifest.entries.find((item:any)=>item.name.toLowerCase()===row.file.toLowerCase());
    const raw=readFileSync(entry.destination);
    expect(row.nativeConsumed).toBe(654);expect(row.stock).toHaveLength(17);
    expect(row.stock).toEqual([...raw.subarray(evidence.stockFileOffset,evidence.stockFileOffset+17)]);
    for(let id=87;id<=103;id++)expect(nativeConsumableCount(row.stock,id)).toBe(raw[evidence.stockFileOffset+id-87]);
  }
});
