import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {buildNativePaletteLookup} from '../src/rules/nativePaletteLookup';
import {nativeDarkenedPixel} from '../src/rules/actedDarkening';
import {nativeActorStatusPixel,nativeActorStatusColorActive} from '../src/rules/actorStatusColor';
test('status pixel transformation and darkening order match all 1536 native outputs',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-actor-status-color.json','utf8'));
  expect(evidence.pixels).toBe(1536);
  for(const row of evidence.rows){
    const lookup=[...buildNativePaletteLookup(row.palette)];
    for(const sample of row.rows){
      const actual=Array.from({length:256},(_,index)=>nativeActorStatusPixel(sample.acted?nativeDarkenedPixel(index,4,row.palette,lookup):index,row.palette,lookup));
      expect(actual).toEqual(sample.pixels);
    }
  }
});
test('status overlay gate follows native status bit and phase modulo four',()=>{
  expect(Array.from({length:8},(_,phase)=>nativeActorStatusColorActive(16,phase))).toEqual([false,false,true,true,false,false,true,true]);
  expect(nativeActorStatusColorActive(8,3)).toBe(false);
});
