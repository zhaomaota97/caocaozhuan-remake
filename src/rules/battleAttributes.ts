import {nativeBattleStat} from './actorStatModifier';
import {nativeEquipmentAttributeTotal,type NativeAttributeItem,type NativeAttributeSlot} from './equipmentAttribute';

/** Native unit getter clamps, followed by the actor-specific state modifier. */
export function nativeBattleAttributes(baseStats:number[],states:number[],slots:NativeAttributeSlot[],items:NativeAttributeItem[]){
  const values=baseStats.map((base,index)=>nativeBattleStat(Math.min(index<3?400:300,base+nativeEquipmentAttributeTotal(slots,items,index)),states[index]));
  return {attack:values[0],defense:values[1],agility:values[3],luck:values[4]};
}
