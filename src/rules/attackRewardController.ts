import {nativeUnitGrowth,type NativeGrowthInput} from './unitGrowth';
import {updateNativeEquipmentSlots,type NativeEquipmentSlot} from './equipmentExperience';

/** Native 0x405C6C state writeback; presentation callbacks are separate. */
export function applyNativeAttackerRewards(unit:NativeGrowthInput,equipment:NativeEquipmentSlot[],awards:{unit:number;weapon:number}){
  return {
    growth:nativeUnitGrowth(unit,unit.experience+awards.unit),
    equipment:updateNativeEquipmentSlots(equipment,0,awards.weapon),
  };
}
