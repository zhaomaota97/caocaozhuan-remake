import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeConsumableCount,decrementNativeConsumable} from '../src/rules/consumableInventory';

test('inventory query and decrement match all 1280 original native rows',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-consumable-inventory.json','utf8'));
  expect(evidence.total).toBe(1280);expect(evidence.passed).toBe(1280);
  const failures=[];
  for(const row of evidence.rows){
    const stock=Array(169).fill(0);if(row.id>=87)stock[row.id-87]=row.count;
    const before=nativeConsumableCount(stock,row.id),afterStock=decrementNativeConsumable(stock,row.id);
    const after=nativeConsumableCount(afterStock,row.id);
    if(before!==row.before||after!==row.after)failures.push({row,before,after});
  }
  expect(failures).toEqual([]);
});
