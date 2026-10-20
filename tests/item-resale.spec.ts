import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeItemResale} from '../src/rules/itemResale';

test('item resale matches all 624 native returns for original definitions',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-item-resale.json','utf8'));
  const runtime=JSON.parse(readFileSync('data/rules/native-item-prices.json','utf8'));
  expect(evidence.total).toBe(624);expect(evidence.passed).toBe(624);
  expect(runtime).toEqual(evidence.definitions);
  const itemBytes=readFileSync('public/assets/native-extracted/Data/resource_0001.bin');
  expect(itemBytes.length).toBeGreaterThanOrEqual(104*25);
  for(const item of runtime){
    expect(item.categoryByte).toBe(itemBytes[item.id*25+0x11]);
    expect(item.priceByte).toBe(itemBytes[item.id*25+0x13]);
  }
  expect(evidence.rows.filter((row:any)=>nativeItemResale(runtime[row.id],row.level)!==row.value)).toEqual([]);
});
