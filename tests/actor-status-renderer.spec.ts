import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeActorStatusIcon} from '../src/rules/actorStatusIcon';
import {nativeActorStatusPixel,nativeActorStatusColorActive} from '../src/rules/actorStatusColor';
import {nativeDarkenedPixel,nativeActorIsDarkened} from '../src/rules/actedDarkening';
import {buildNativePaletteLookup} from '../src/rules/nativePaletteLookup';
test('status icons and composed actor pixels match all 512 native renderer traces',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-actor-status-icons.json','utf8'));
  expect(evidence.total).toBe(512);const lookup=[...buildNativePaletteLookup(evidence.palette)];
  const failures=[];
  for(const row of evidence.rows){
    const icon=nativeActorStatusIcon(row.status,row.phase);
    const pixels=Array.from({length:256},(_,index)=>{
      if(nativeActorIsDarkened(row.flags,1))index=nativeDarkenedPixel(index,4,evidence.palette,lookup);
      return nativeActorStatusColorActive(row.status,row.phase)?nativeActorStatusPixel(index,evidence.palette,lookup):index;
    });
    if(JSON.stringify(icon?[icon]:[])!==JSON.stringify(row.icons)||JSON.stringify(pixels)!==JSON.stringify(row.pixels))failures.push({flags:row.flags,status:row.status,phase:row.phase});
  }
  expect(failures).toEqual([]);
});
