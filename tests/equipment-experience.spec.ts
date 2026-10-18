import {test,expect} from '@playwright/test';
import {nativeEquipmentExperience,updateNativeEquipmentSlots} from '../src/rules/equipmentExperience';

test('native equipment experience upgrades and caps normal weapons',()=>{
  expect(nativeEquipmentExperience({slot:0,itemId:0,categoryByte:0,level:2,experience:99,gain:1})).toEqual({level:3,experience:255,levelsGained:1,updated:true});
  expect(nativeEquipmentExperience({slot:0,itemId:21,categoryByte:1,level:8,experience:99,gain:101})).toEqual({level:9,experience:255,levelsGained:1,updated:true});
});
test('native equipment updater ignores slot two and empty equipment',()=>{
  expect(nativeEquipmentExperience({slot:2,itemId:0,categoryByte:0,level:0,experience:0,gain:200}).updated).toBe(false);
  expect(nativeEquipmentExperience({slot:0,itemId:255,categoryByte:0,level:0,experience:0,gain:200}).updated).toBe(false);
});
test('equipment array updater preserves non-target slots',()=>{
  const slots=[{slot:0,itemId:0,categoryByte:0,level:2,experience:99,name:'weapon'},{slot:1,itemId:1,categoryByte:0,level:1,experience:0,name:'armor'}];
  expect(updateNativeEquipmentSlots(slots,0,1)).toEqual([{...slots[0],level:3,experience:255},slots[1]]);
});
