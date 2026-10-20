import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeConsumableCount,decrementNativeConsumable,grantNativeConsumable} from '../src/rules/consumableInventory';
import {nativeItemResale} from '../src/rules/itemResale';

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

test('consumable grants match all 918 native stock and money boundaries',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-consumable-grant.json','utf8'));
  expect(evidence.total).toBe(918);expect(evidence.passed).toBe(918);
  const failures=[];
  for(const row of evidence.rows){
    const stock=Array(17).fill(0);stock[row.id-87]=row.count;
    const result=grantNativeConsumable(stock,row.id,row.initialMoney,row.price);
    if(result.stock[row.id-87]!==row.stock||result.money!==row.money||result.returned!==row.returned)failures.push({row,result});
  }
  expect(failures).toEqual([]);
});

test('original-item grant and real resale composition match 306 unpatched native cases',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-real-consumable-grant.json','utf8'));
  const prices=JSON.parse(readFileSync('data/rules/native-item-prices.json','utf8'));
  expect(evidence.total).toBe(306);expect(evidence.passed).toBe(306);
  const failures=[];
  for(const row of evidence.rows){
    const stock=Array(17).fill(0);stock[row.id-87]=row.count;
    const price=nativeItemResale(prices.find((item:any)=>item.id===row.id),0);
    const result=grantNativeConsumable(stock,row.id,row.initialMoney,price);
    if(result.stock[row.id-87]!==row.stock||result.money!==row.money||result.returned!==row.returned)failures.push({row,result});
  }
  expect(failures).toEqual([]);
});
