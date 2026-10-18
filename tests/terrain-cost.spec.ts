import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {terrainCost,movementType} from '../src/rules/terrainCost';

test('terrain rule matches 960 actual saved-actor native costs',()=>{
  const save=JSON.parse(readFileSync('data/saves/slot-08.json','utf8'));
  const items=JSON.parse(readFileSync('data/rules/item-categories.json','utf8'));
  const table=JSON.parse(readFileSync('data/rules/terrain-movement.json','utf8'));
  expect(table).toHaveLength(27);
  for(const actor of save.actors){
    for(let terrain=0;terrain<30;terrain++)expect(terrainCost(actor.classId,actor.equipmentSlots,terrain,items,table),`${actor.id},${terrain}`).toBe(actor.terrainCosts[terrain]);
  }
  expect(movementType(53)).toBe(27);
});
