import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {ordinaryDamage,ordinaryAccuracy,ordinaryStrike,criticalChance,doubleAttackChance,ordinaryResult,repeatsAttack,ordinaryWriteback} from '../src/rules/ordinaryDamage';
import {GameRng} from '../src/rules/gameRng';

test('deterministic ordinary damage matches 1984 actual native saved-unit cases',()=>{
  const fixture=JSON.parse(readFileSync('tests/fixtures/native-ordinary-damage.json','utf8'));
  const items=JSON.parse(readFileSync('data/rules/item-categories.json','utf8'));
  expect(fixture.rows).toHaveLength(1984);
  for(const row of fixture.rows){
    const actor=(slot:number)=>fixture.actors.find((actor:{slot:number})=>actor.slot===slot);
    expect(ordinaryDamage(actor(row.attacker),actor(row.defender),items,Boolean(row.counter)),JSON.stringify(row)).toBe(row.native);
    expect(ordinaryAccuracy(actor(row.attacker),actor(row.defender),items),JSON.stringify(row)).toBe(row.nativeAccuracy);
    expect(criticalChance(actor(row.attacker),actor(row.defender),items)).toBe(row.nativeCritical);
    expect(doubleAttackChance(actor(row.attacker),actor(row.defender))).toBe(row.nativeDouble);
    for(const live of row.live){
      const rng=new GameRng(live.seed);
      expect(ordinaryStrike(actor(row.attacker),actor(row.defender),items,rng,Boolean(row.counter))).toBe(live.native);
      expect(rng.state).toBe(live.state);
    }
  }
});

test('primary attack result and random state match 15872 original outputs',()=>{
  const fixture=JSON.parse(readFileSync('tests/fixtures/native-ordinary-damage.json','utf8'));
  const items=JSON.parse(readFileSync('data/rules/item-categories.json','utf8'));
  const actors=new Map<number,any>(fixture.actors.map((actor:any)=>[actor.slot,actor]));
  const actual=[],expected=[];
  for(const row of fixture.rows)for(const live of row.live)for(const result of live.results){
    const rng=new GameRng(live.seed);
    const strike=ordinaryResult(actors.get(row.attacker),actors.get(row.defender),items,rng,Boolean(row.counter),result.round);
    const state=rng.state;
    const writeback=ordinaryWriteback(actors.get(row.attacker),actors.get(row.defender),strike,items,rng);
    const written={hp:writeback.hp,mp:writeback.mp,status:writeback.statusFlags,flags:writeback.actorFlags,state:rng.state};
    rng.state=state;
    const repeat=repeatsAttack(actors.get(row.attacker),actors.get(row.defender),rng,row.counter,result.round);
    actual.push({...strike,state,repeat,repeatState:rng.state,writeback:written});
    expected.push({hpDamage:result.hpDamage,mpDamage:result.mpDamage,critical:result.critical,state:result.state,
      repeat:result.repeat,repeatState:result.repeatState,writeback:result.writeback});
  }
  expect(actual).toHaveLength(15872);
  expect(actual).toEqual(expected);
});
