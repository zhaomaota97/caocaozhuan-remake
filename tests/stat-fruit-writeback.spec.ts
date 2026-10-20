import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeStatFruitWriteback} from '../src/rules/statFruitWriteback';
test('stat fruit controller matches all 1125 native state transitions',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-stat-fruit-controller.json','utf8'));
  expect(evidence.total).toBe(1125);expect(evidence.passed).toBe(1125);
  const failures=[];
  for(const row of evidence.rows){
    const actual=nativeStatFruitWriteback(row.category,row.value,Array(5).fill(row.stat),Array(5).fill(row.rank),Array(5).fill(row.state));
    if(JSON.stringify(actual)!==JSON.stringify({stats:row.stats,ranks:row.ranks,states:row.states}))failures.push({row,actual});
  }
  expect(failures).toEqual([]);
});
