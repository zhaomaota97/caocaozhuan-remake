export interface ItemCategory { id:number; categoryByte:number; equipmentEffectCategory:number; }
export interface EquipmentSlot { itemId:number; }

/** Original 0x407A09; first two slots require an odd weapon/armor category below 0x12. */
export function hasEquipmentCategory(slots:EquipmentSlot[],items:ItemCategory[],category:number):boolean{
  for(let slot=0;slot<Math.min(3,slots.length);slot++){
    const id=slots[slot].itemId;
    if(id===255)continue;
    const item=items.find(candidate=>candidate.id===id);
    if(!item)continue;
    if(slot===2){if(item.categoryByte===category)return true;}
    else if(item.categoryByte<0x12 && (item.categoryByte&1)!==0 && item.equipmentEffectCategory===category)return true;
  }
  return false;
}
