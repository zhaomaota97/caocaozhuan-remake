import {test,expect} from '@playwright/test';
import {nativeAiOrdinaryAttackScore} from '../src/rules/aiAttackScore';

const base={currentHp:100,maxHp:100,predictedDamage:0,attackerMode:0,targetFlags:0,targetIdentity:10,leaderMatch:false,covered:false,sameSide:false,candidateRisk:false};
test('native ordinary AI score applies lethal, damage-ratio, HP-ratio and flag branches',()=>{
  expect(nativeAiOrdinaryAttackScore({...base,currentHp:40})).toBe(16);
  expect(nativeAiOrdinaryAttackScore({...base,currentHp:100,predictedDamage:10})).toBe(16);
  expect(nativeAiOrdinaryAttackScore({...base,predictedDamage:100})).toBe(80);
  expect(nativeAiOrdinaryAttackScore({...base,attackerMode:1})).toBe(10);
  expect(nativeAiOrdinaryAttackScore({...base,targetFlags:8})).toBe(10);
  expect(nativeAiOrdinaryAttackScore({...base,sameSide:true})).toBe(0);
  expect(nativeAiOrdinaryAttackScore({...base,covered:true})).toBe(0);
});

test('identity 174 uses explicit native leader-match input',()=>{
  expect(nativeAiOrdinaryAttackScore({...base,targetIdentity:174,leaderMatch:false})).toBe(6);
  expect(nativeAiOrdinaryAttackScore({...base,targetIdentity:174,leaderMatch:true})).toBe(10);
});
