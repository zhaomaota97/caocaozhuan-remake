import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

test('all slot 8 actor attributes agree with captured original functions',()=>{
  const save=JSON.parse(readFileSync('data/saves/slot-08.json','utf8'));
  const native=JSON.parse(readFileSync('tests/fixtures/slot08-native-actor-state.json','utf8'));
  expect(save.actors).toHaveLength(32);
  expect(native).toHaveLength(32);
  for(const original of native){
    const actor=save.actors.find((candidate:{id:string})=>candidate.id===`unit-${original.slot}`);
    expect(actor).toBeDefined();
    for(const field of ['hp','maxHp','mp','maxMp','nativeLevel','classId','move','injuredPose','terrainCosts','nativeMovementCosts']){
      expect(actor[field],`${actor.id}.${field}`).toEqual(original[field]);
    }
    expect(actor.equipmentSlots.map(({slot,itemId,byte1,byte2}:{slot:number;itemId:number;byte1:number;byte2:number})=>({slot,itemId,byte1,byte2}))).toEqual(original.equipmentSlots);
  }
});
