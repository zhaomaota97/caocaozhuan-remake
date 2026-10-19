import {test,expect} from '@playwright/test';
import {nativeTargetRelation} from '../src/rules/nativeTargetEligibility';

test('native relation byte separates opposing and allied slot groups',()=>{
  expect(nativeTargetRelation(0,35,0)).toBe(true);
  expect(nativeTargetRelation(0,1,0)).toBe(false);
  expect(nativeTargetRelation(0,1,1)).toBe(true);
  expect(nativeTargetRelation(0,35,1)).toBe(false);
});
