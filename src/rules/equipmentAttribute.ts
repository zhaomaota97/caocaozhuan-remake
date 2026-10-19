export interface NativeItemAttribute {categoryByte:number;baseValue:number;growthValue:number;}

/** Native 0x40C674: per-item contribution before the slot accumulator. */
export function nativeEquipmentAttribute(item:NativeItemAttribute,storedLevel:number):number{
  const level=storedLevel&255;
  if(item.categoryByte>=18)return item.baseValue;
  return Math.min(255,item.baseValue+Math.max(0,level-1)*item.growthValue);
}
