import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeManualItemEligible} from '../src/rules/manualItemEligibility';

test('manual item eligibility matches 13328 original native decisions',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-manual-item-eligibility.json','utf8'));
  expect(evidence.total).toBe(13328);expect(evidence.passed).toBe(13328);
  expect(evidence.rows.filter((row:any)=>nativeManualItemEligible(row.category,{statusFlags:row.status,classId:row.classId,nativeLevel:row.level},row.mode!==0)!==row.eligible)).toEqual([]);
});
