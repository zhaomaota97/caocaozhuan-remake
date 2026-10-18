import {test,expect} from '@playwright/test';
import {nativeGrowthField,nativeGrowthFields} from '../src/rules/nativeGrowthFields';

test('native growth categories map to verified unit offsets',()=>{
  expect(nativeGrowthFields()).toHaveLength(5);
  expect(nativeGrowthField(0x46)).toEqual({category:0x46,unitOffset:0x15,actorIndex:0});
  expect(nativeGrowthField(0x47)).toEqual({category:0x47,unitOffset:0x17,actorIndex:2});
  expect(nativeGrowthField(0x48)).toEqual({category:0x48,unitOffset:0x16,actorIndex:1});
  expect(nativeGrowthField(0x49)).toEqual({category:0x49,unitOffset:0x18,actorIndex:3});
  expect(nativeGrowthField(0x4a)).toEqual({category:0x4a,unitOffset:0x19,actorIndex:4});
  expect(nativeGrowthField(0x3f)).toBeUndefined();
});
