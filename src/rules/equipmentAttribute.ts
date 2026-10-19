export interface NativeItemAttribute {categoryByte:number;baseValue:number;growthValue:number;}

/** Native 0x40C674: per-item contribution before the slot accumulator. */
export function nativeEquipmentAttribute(item:NativeItemAttribute,storedLevel:number):number{
  const level=storedLevel&255;
  if(item.categoryByte>=18)return item.baseValue;
  return Math.min(255,item.baseValue+Math.max(0,level-1)*item.growthValue);
}

export interface NativeAttributeItem extends NativeItemAttribute {id:number;equipmentEffectCategory:number;secondaryValue:number;}
export interface NativeAttributeSlot {slot:number;itemId:number;byte1:number;}
function primaryAttribute(category:number):number{
  if(category<10||category===24)return 0;
  if(category<14||category===25)return 2;
  if(category<18||category===26)return 1;
  return ({27:3,28:4,29:5,30:6,31:8,32:7} as Record<number,number>)[category]??255;
}

/** Native 0x407C0E returns an eight-bit accumulated contribution. */
export function nativeEquipmentAttributeTotal(slots:NativeAttributeSlot[],items:NativeAttributeItem[],attribute:number):number{
  let total=0;
  for(const slot of slots){
    if(slot.slot<0||slot.slot>2||slot.itemId===255)continue;
    const item=items.find(row=>row.id===slot.itemId);
    if(!item)throw new Error(`Missing native item ${slot.itemId}`);
    if(primaryAttribute(item.categoryByte)===attribute)total+=slot.slot===2?item.baseValue:nativeEquipmentAttribute(item,slot.byte1);
    const secondary=({24:0,25:2,26:1,27:3,28:4,29:5,30:6,31:8,32:7} as Record<number,number>)[item.equipmentEffectCategory]??255;
    if(slot.slot<2&&item.categoryByte<18&&(item.categoryByte&1)!==0&&secondary===attribute)total+=item.secondaryValue;
  }
  return total&255;
}
