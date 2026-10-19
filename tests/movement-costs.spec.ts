import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {movementCosts,stopsExpansion} from '../src/rules/movementCosts';

test('four-direction search matches all original slot 8 cost maps',()=>{
  const save=JSON.parse(readFileSync('data/saves/slot-08.json','utf8'));
  const items=JSON.parse(readFileSync('data/rules/item-categories.json','utf8'));
  const table=JSON.parse(readFileSync('data/rules/terrain-movement.json','utf8'));
  const classes=JSON.parse(readFileSync('data/rules/class-movement.json','utf8'));
  expect(save.actors).toHaveLength(32);
  for(const actor of save.actors){
    const stops=Array.from({length:save.width*save.height},(_,index)=>stopsExpansion(save.width,save.height,save.actors,actor,index,items));
    expect(stops,`${actor.id}: native restriction predicate`).toEqual(actor.nativeStopExpansion);
    const actual=movementCosts(save.width,save.height,save.terrain,save.actors,{...actor,move:-999},items,table,classes);
    expect(actual,actor.id).toEqual(actor.nativeMovementCosts);
    const scenarioActors=save.actors.map((row:any)=>({...row,id:`s00-slot-${row.id.slice(5)}`}));
    const scenarioActor=scenarioActors.find((row:any)=>row.id===`s00-slot-${actor.id.slice(5)}`);
    const scenarioStops=Array.from({length:save.width*save.height},(_,index)=>stopsExpansion(save.width,save.height,scenarioActors,scenarioActor,index,items));
    expect(scenarioStops,`${scenarioActor.id}: native restriction predicate`).toEqual(actor.nativeStopExpansion);
    expect(movementCosts(save.width,save.height,save.terrain,scenarioActors,scenarioActor,items,table,classes),scenarioActor.id).toEqual(actor.nativeMovementCosts);
  }
});
