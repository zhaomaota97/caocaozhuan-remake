import {test,expect} from '@playwright/test';
import {applyNativeChapterPhase,applyOpcode58ChapterPhase} from '../src/rules/eexPortraitPhase';

test('opcode 103 stores saturated byte minus one',()=>{
  expect(applyNativeChapterPhase(4,4)).toEqual({status:1,phase:3});
  expect(applyNativeChapterPhase(0,4)).toEqual({status:1,phase:0});
  expect(applyNativeChapterPhase(0x8000,4)).toEqual({status:5,phase:0});
});
test('opcode 58 direct branch only writes when mode is one',()=>{
  expect(applyOpcode58ChapterPhase(2,1,3,40,4)).toEqual({status:1,phase:3});
  expect(applyOpcode58ChapterPhase(2,0,3,40,4)).toEqual({status:1,phase:2});
});
