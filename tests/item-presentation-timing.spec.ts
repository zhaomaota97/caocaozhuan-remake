import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeItemWaitRemaining,nativeItemPresentationStages} from '../src/rules/itemPresentationTiming';
test('item deadline arithmetic matches all 20 original native timer cases',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-item-wait-chain.json','utf8'));
  expect(evidence.total).toBe(20);expect(evidence.passed).toBe(20);
  for(const row of evidence.rows)expect(nativeItemWaitRemaining(1000,row.amount,1000+row.elapsed)).toBe(row.pumps);
});
test('item static presentation stages retain direct tick waits and all blend frames',()=>{
  const stages=nativeItemPresentationStages();
  expect(stages.map(row=>row.waitTicks)).toEqual([5,10,...Array(16).fill(1)]);
  expect(stages.filter(row=>row.kind==='blend').map(row=>'frame' in row?row.frame:undefined)).toEqual(Array.from({length:16},(_,i)=>i));
});
