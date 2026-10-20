import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {buildNativePaletteLookup,nativePaletteColorIndex} from '../src/rules/nativePaletteLookup';

test('regenerated quantization table matches all 4096 original native entries',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-item-blend-frames.json','utf8'));
  expect([...buildNativePaletteLookup(evidence.palette)]).toEqual(evidence.lookup);
});
test('native color search excludes reserved indexes and keeps last exact tie',()=>{
  const palette=Array(768).fill(0);
  expect(nativePaletteColorIndex([0,0,0],palette)).toBe(245);
  palette[246*3]=15;
  expect(nativePaletteColorIndex([15,0,0],palette)).toBe(245);
  expect(nativePaletteColorIndex([0,15,0],palette)).toBe(0);
});
