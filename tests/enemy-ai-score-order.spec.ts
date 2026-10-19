import {test,expect} from '@playwright/test';
import {nativeAiOrdinaryAttackScore} from '../src/rules/aiAttackScore';

test('verified score prioritizes a lethal target over distance',()=>{
  const input={maxHp:100,predictedDamage:0,attackerMode:0,targetFlags:0,targetIdentity:0,leaderMatch:false,covered:false,sameSide:false,candidateRisk:false};
  const lethal=nativeAiOrdinaryAttackScore({...input,currentHp:10,predictedDamage:10});
  const healthy=nativeAiOrdinaryAttackScore({...input,currentHp:100,predictedDamage:0});
  expect(lethal).toBeGreaterThan(healthy);
});
