import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeStrategyResourceWriteback} from '../src/rules/strategyResourceWriteback';

test('strategy resource writeback matches native cost and restoration cases',()=>{
  const rows=JSON.parse(readFileSync('docs/reverse-engineering/native-effect-cost-validation.json','utf8'));
  expect(rows).toHaveLength(12);
  for(const row of rows){
    expect(nativeStrategyResourceWriteback({success:true,effectId:row.effect??0,hp:80,maxHp:100,mp:row.current,maxMp:50,cost:row.cost,costDivisor:row.divisor,magnitude:row.magnitude??0})).toEqual({hp:row.health,mp:row.resource});
  }
});

test('unsuccessful action leaves resources unchanged',()=>{
  expect(nativeStrategyResourceWriteback({success:false,effectId:20,hp:80,maxHp:100,mp:40,maxMp:50,cost:13,magnitude:7})).toEqual({hp:80,mp:40});
});

test('writeback matches all 1728 native success and resource boundaries',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-strategy-resource-matrix.json','utf8'));
  expect(evidence.total).toBe(1728);expect(evidence.passed).toBe(1728);
  const failures=[];
  for(const row of evidence.rows){
    const actual=nativeStrategyResourceWriteback({success:row.success,effectId:row.effect,hp:80,maxHp:100,mp:row.current,maxMp:50,cost:row.cost,costDivisor:row.divisor??undefined,magnitude:row.magnitude});
    if(actual.hp!==row.health||actual.mp!==row.resource)failures.push({input:row,actual});
  }
  expect(failures).toEqual([]);
});
