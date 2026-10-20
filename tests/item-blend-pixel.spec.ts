import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeItemBlendPixel} from '../src/rules/itemBlendPixel';
import {buildNativePaletteLookup} from '../src/rules/nativePaletteLookup';
test('item pixel blend matches 4096 original native frame outputs',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-item-blend-frames.json','utf8'));
  expect(evidence.rows).toHaveLength(16);expect(evidence.lookup).toHaveLength(4096);
  const failures=[];
  const lookup=[...buildNativePaletteLookup(evidence.palette)];
  for(const row of evidence.rows){
    const actual=evidence.source.map((source:number,index:number)=>nativeItemBlendPixel(source,evidence.background[index],row.frame,evidence.palette,lookup));
    if(JSON.stringify(actual)!==JSON.stringify(row.pixels))failures.push(row.frame);
  }
  expect(failures).toEqual([]);
});
