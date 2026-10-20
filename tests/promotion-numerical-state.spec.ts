import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativePromotionNumericalState} from '../src/rules/promotionNumericalState';
test('promotion numerical helper sequence matches 477 native cases',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-promotion-state-sequence.json','utf8'));
  expect(evidence.total).toBe(477);expect(evidence.passed).toBe(477);
  const failures=[];
  for(const row of evidence.rows){
    const actual=nativePromotionNumericalState({classId:row.classId,maxHpBase:row.hp,maxMpBase:row.mp},evidence.classes[row.classId]);
    if(actual.classId!==row.finalClass||actual.maxHpBase!==row.finalHp||actual.maxMpBase!==row.finalMp)failures.push({row,actual});
  }
  expect(failures).toEqual([]);
});
