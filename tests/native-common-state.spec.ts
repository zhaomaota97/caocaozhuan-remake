import {test,expect} from '@playwright/test';
import {applyEexOpcode32,applyEexOpcode103,applyEexOpcode58} from '../src/rules/nativeCommonState';

test('common state applies portrait flags without changing phase',()=>{
  const before={portraitFlags:0x20,portraitPhase:2};
  expect(applyEexOpcode32(before,74,3)).toEqual({status:1,state:{portraitFlags:0x23,portraitPhase:2}});
});
test('common state applies opcode 103 phase write',()=>{
  expect(applyEexOpcode103({portraitFlags:0,portraitPhase:0},4,4)).toEqual({status:1,state:{portraitFlags:0,portraitPhase:3}});
});
test('common state preserves state for rejected writes',()=>{
  const before={portraitFlags:2,portraitPhase:5};
  expect(applyEexOpcode32(before,73,1)).toEqual({status:5,state:before});
  expect(applyEexOpcode58(before,40,0,4,8)).toEqual({status:1,state:before});
});
