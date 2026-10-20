/** Native 0x43C42E for valid resource states (current <= maximum). */
export function nativeItemRestoreAmount(category:number,value:number,current:number,maximum:number):number{
  if(category!==63&&category!==64)return value;
  if(current>maximum)throw new RangeError('Over-maximum native resource state is not validated');
  const missing=maximum-current;
  return value===255?missing:Math.min(value,missing);
}
