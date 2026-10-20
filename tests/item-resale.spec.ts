import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeItemResale} from '../src/rules/itemResale';

test('item resale matches all 624 native returns for original definitions',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-item-resale.json','utf8'));
  const runtime=JSON.parse(readFileSync('data/rules/native-item-prices.json','utf8'));
  expect(evidence.total).toBe(624);expect(evidence.passed).toBe(624);
  expect(runtime).toEqual(evidence.definitions);
  expect(evidence.rows.filter((row:any)=>nativeItemResale(runtime[row.id],row.level)!==row.value)).toEqual([]);
});
