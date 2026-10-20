import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeItemRestoreAmount} from '../src/rules/itemRestoreAmount';

test('consumable restoration amount matches all 180 native helper returns',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-item-restore-amount.json','utf8'));
  expect(evidence.total).toBe(180);expect(evidence.passed).toBe(180);
  expect(evidence.rows.filter((row:any)=>nativeItemRestoreAmount(row.category,row.value,row.current,row.maximum)!==row.amount)).toEqual([]);
});
