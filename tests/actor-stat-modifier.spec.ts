import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeActorStatModifier,nativeBattleStat} from '../src/rules/actorStatModifier';

test('actor stat modifier matches every captured native result',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-actor-stat-modifier.json','utf8'));
  expect(evidence.passed).toBe(true);
  expect(evidence.rows).toHaveLength(5120);
  const failures=evidence.rows.filter((row:{base:number;status:number;result:number})=>nativeActorStatModifier(row.base,row.status)!==row.result);
  expect(failures).toEqual([]);
});

test('outer battle attribute getters cap the modified value at 400',()=>{
  expect(nativeBattleStat(399,4)).toBe(400);
  expect(nativeBattleStat(333,4)).toBe(399);
  expect(nativeBattleStat(400,2)).toBe(280);
  expect(nativeBattleStat(400,3)).toBe(400);
});
