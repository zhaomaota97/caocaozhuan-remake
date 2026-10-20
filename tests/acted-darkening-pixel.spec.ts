import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {buildNativePaletteLookup} from '../src/rules/nativePaletteLookup';
import {nativeDarkenedPixel,nativeActorIsDarkened} from '../src/rules/actedDarkening';
test('indexed darkening matches all 3072 captured native pixel outputs',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-acted-darkening.json','utf8'));
  expect(evidence.pixels).toBe(3072);
  for(const row of evidence.rows){
    const lookup=[...buildNativePaletteLookup(row.palette)];
    for(const sample of row.rows)expect(Array.from({length:256},(_,index)=>nativeDarkenedPixel(index,sample.amount,row.palette,lookup))).toEqual(sample.pixels);
  }
});
test('actor darkening gate requires both action flags and living actor',()=>{
  expect([0,2,4,6].map(flags=>nativeActorIsDarkened(flags,1))).toEqual([false,false,false,true]);
  expect(nativeActorIsDarkened(6,0)).toBe(false);
});

test('darkening gate matches all 512 native actor renderer executions',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-acted-render-gate.json','utf8'));
  expect(evidence.total).toBe(512);expect(evidence.passed).toBe(512);
  const failures=evidence.rows.filter((row:any)=>!row.match||nativeActorIsDarkened(row.flags,row.hp)!==row.darkened);
  expect(failures).toEqual([]);
});
