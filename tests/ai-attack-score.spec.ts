import {test,expect} from '@playwright/test';
import {nativeAiOrdinaryAttackScore,nativeAiClassFiltered} from '../src/rules/aiAttackScore';
import {readFileSync} from 'node:fs';

const base={currentHp:100,maxHp:100,predictedDamage:0,attackerMode:0,targetFlags:0,targetIdentity:10,leaderMatch:false,covered:false,sameSide:false,candidateRisk:false};
test('native class filter follows class tiers and special-class mapping',()=>{
  for(let id=0;id<53;id++)expect(nativeAiClassFiltered(id)).toBe((id>=24&&id<=35)||(id>=44&&id<=46));
  expect(nativeAiClassFiltered(53)).toBe(false);
});
test('native ordinary AI score applies lethal, damage-ratio, HP-ratio and flag branches',()=>{
  expect(nativeAiOrdinaryAttackScore({...base,currentHp:40})).toBe(20);
  expect(nativeAiOrdinaryAttackScore({...base,currentHp:100,predictedDamage:10})).toBe(20);
  expect(nativeAiOrdinaryAttackScore({...base,predictedDamage:100})).toBe(84);
  expect(nativeAiOrdinaryAttackScore({...base,attackerMode:1})).toBe(14);
  expect(nativeAiOrdinaryAttackScore({...base,targetFlags:8})).toBe(14);
  expect(nativeAiOrdinaryAttackScore({...base,sameSide:true})).toBe(0);
  expect(nativeAiOrdinaryAttackScore({...base,covered:true})).toBe(0);
});

test('identity 174 uses explicit native leader-match input',()=>{
  expect(nativeAiOrdinaryAttackScore({...base,targetIdentity:174,leaderMatch:false})).toBe(2);
  expect(nativeAiOrdinaryAttackScore({...base,targetIdentity:174,leaderMatch:true})).toBe(2);
});

test('ordinary score matches all 2880 captured native returns',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-ai-attack-score-validation.json','utf8'));
  expect(evidence.rows).toHaveLength(2880);
  const failures=[];
  for(const row of evidence.rows){
    const x=row.input;
    const actual=nativeAiOrdinaryAttackScore({currentHp:x.hp,maxHp:100,predictedDamage:x.damage,attackerMode:x.mode,targetFlags:x.flag,targetIdentity:x.identity,targetSlot:x.slot,leaderMatch:x.identity===10,covered:Boolean(x.filtered),sameSide:x.same_side,candidateRisk:Boolean(x.risk)});
    if(actual!==row.actual)failures.push({input:x,actual,expected:row.actual});
  }
  expect(failures).toEqual([]);
});
