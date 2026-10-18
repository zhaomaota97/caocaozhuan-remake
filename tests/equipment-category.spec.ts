import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {hasEquipmentCategory} from '../src/rules/equipmentCategory';

test('equipment category lookup matches 8192 native predicates',()=>{
  const actors=JSON.parse(readFileSync('tests/fixtures/slot08-native-actor-state.json','utf8'));
  const items=JSON.parse(readFileSync('data/rules/item-categories.json','utf8'));
  expect(actors).toHaveLength(32);
  expect(items).toHaveLength(104);
  for(const actor of actors){
    expect(actor.nativeEquipmentCategories).toHaveLength(256);
    for(let category=0;category<256;category++){
      expect(hasEquipmentCategory(actor.equipmentSlots,items,category),`${actor.slot}: category ${category}`).toBe(actor.nativeEquipmentCategories[category]);
    }
  }
});
