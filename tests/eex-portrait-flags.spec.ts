import {test,expect} from '@playwright/test';
import {applyNativePortraitFlags} from '../src/rules/eexPortraitFlags';

test('native portrait flag opcode rejects wrong tag and sentinel',()=>{
  expect(applyNativePortraitFlags(0xab,73,3)).toEqual({status:5,flags:0xab});
  expect(applyNativePortraitFlags(0xab,74,0x8000)).toEqual({status:5,flags:0xab});
});
test('native portrait flag opcode clears low five bits on FF',()=>{
  expect(applyNativePortraitFlags(0x9f,74,0xff)).toEqual({status:1,flags:0x80});
});
test('native portrait flag opcode preserves high nibble and writes byte',()=>{
  expect(applyNativePortraitFlags(0xa0,74,0x15)).toEqual({status:1,flags:0xb5});
});
