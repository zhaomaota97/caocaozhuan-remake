import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {ordinaryExchange} from '../src/rules/ordinaryExchange';
import {GameRng} from '../src/rules/gameRng';

test('exchange primary strike matches the original executable result fixtures',()=>{
  const fixture=JSON.parse(readFileSync('tests/fixtures/native-ordinary-damage.json','utf8'));
  const rules={items:JSON.parse(readFileSync('data/rules/item-categories.json','utf8')),classes:JSON.parse(readFileSync('data/rules/class-attack-ranges.json','utf8')),shapes:JSON.parse(readFileSync('data/rules/target-shapes.json','utf8')).shapes};
  const a={...fixture.actors.find((actor:any)=>actor.slot===0),id:'unit-0',x:10,y:10};
  const d={...fixture.actors.find((actor:any)=>actor.slot===41),id:'unit-41',x:10,y:11};
  const row=fixture.rows.find((row:any)=>row.attacker===0&&row.defender===41&&row.counter===0);
  for(const live of row.live){
    const expected=live.results.find((result:any)=>result.round===0);
    const exchange=ordinaryExchange(a,d,new GameRng(live.seed),rules);
    expect(exchange.supported).toBe(true);
    expect(exchange.strikes[0]).toMatchObject({hpDamage:expected.hpDamage,mpDamage:expected.mpDamage,critical:expected.critical});
    expect(exchange.strikes[0].after.hp).toBe(d.hp-expected.hpDamage);
    expect(a.hp).toBe(fixture.actors.find((actor:any)=>actor.slot===0).hp);
  }
});
