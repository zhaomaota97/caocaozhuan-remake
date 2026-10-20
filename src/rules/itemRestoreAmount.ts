/** Native 0x43C42E for valid resource states (current <= maximum). */
export function nativeItemRestoreAmount(category:number,value:number,current:number,maximum:number):number{
  if(category!==63&&category!==64)return value;
  if(current>maximum)throw new RangeError('Over-maximum native resource state is not validated');
  const missing=maximum-current;
  return value===255?missing:Math.min(value,missing);
}

/** State portion of 0x41CCDF/0x41CE3D after a valid target is selected. */
export function nativeItemRestoreWriteback(category:63|64,value:number,target:{hp:number;maxHp:number;mp:number;maxMp:number}):{hp:number;mp:number}{
  if(category===63){
    const gain=nativeItemRestoreAmount(category,value,target.hp,target.maxHp);
    return {hp:Math.min(target.maxHp,target.hp+gain),mp:target.mp};
  }
  const gain=nativeItemRestoreAmount(category,value,target.mp,target.maxMp)&255;
  return {hp:target.hp,mp:Math.min(target.maxMp,target.mp+gain)};
}
