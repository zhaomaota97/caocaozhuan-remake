import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeItemRestoreAmount,nativeItemRestoreWriteback} from '../src/rules/itemRestoreAmount';

test('consumable restoration amount matches all 180 native helper returns',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-item-restore-amount.json','utf8'));
  expect(evidence.total).toBe(180);expect(evidence.passed).toBe(180);
  expect(evidence.rows.filter((row:any)=>nativeItemRestoreAmount(row.category,row.value,row.current,row.maximum)!==row.amount)).toEqual([]);
});

test('HP and MP controller state writes match all 120 native cases',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-item-restore-controller.json','utf8'));
  expect(evidence.total).toBe(120);expect(evidence.passed).toBe(120);
  const failures=[];
  for(const row of evidence.rows){
    const actual=nativeItemRestoreWriteback(row.category,row.value,{hp:row.current,maxHp:row.maximum,mp:row.current,maxMp:row.maximum});
    if(actual.hp!==row.hp||actual.mp!==row.mp)failures.push({input:row,actual});
  }
  expect(failures).toEqual([]);
});
