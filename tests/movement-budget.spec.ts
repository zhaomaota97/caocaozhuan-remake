import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {movementBudget} from '../src/rules/movementBudget';

test('movement budget matches every actual saved-actor native value',()=>{
  const save=JSON.parse(readFileSync('data/saves/slot-08.json','utf8'));
  const items=JSON.parse(readFileSync('data/rules/item-categories.json','utf8'));
  const classes=JSON.parse(readFileSync('data/rules/class-movement.json','utf8'));
  expect(classes).toHaveLength(53);
  for(const actor of save.actors)expect(movementBudget(actor,items,classes),actor.id).toBe(actor.move);
});

test('equipment slots and byte overflow match original native probes',()=>{
  const fixture=JSON.parse(readFileSync('tests/fixtures/native-movement-budget-equipment.json','utf8'));
  const originalItems=JSON.parse(readFileSync('data/rules/item-categories.json','utf8'));
  const classes=JSON.parse(readFileSync('data/rules/class-movement.json','utf8'));
  expect(fixture.rows).toHaveLength(487);
  for(const row of fixture.rows){
    const slots=[0,1,2].map(slot=>({slot,itemId:255,byte1:0,byte2:0}));
    let items=originalItems;
    if(row.kind==='original-item')slots[row.slot].itemId=row.itemId;
    else{
      items=[{id:0,categoryByte:row.category,equipmentEffectCategory:32,
        baseValue:row.value,secondaryValue:row.value}];
      for(const slot of row.slots)slots[slot].itemId=0;
    }
    expect(movementBudget({classId:0,statusFlags:0,movementTier:3,equipmentSlots:slots},items,classes),
      JSON.stringify(row)).toBe(row.native);
  }
});
