/** Native 0x40D9C4; callers pass item IDs as bytes. */
export function nativeConsumableIndex(itemId:number):number|undefined{
  const id=itemId&255;
  return id<87?undefined:id-87;
}
export function nativeConsumableCount(stock:readonly number[],itemId:number):number{
  const index=nativeConsumableIndex(itemId);
  if(index===undefined)return 255;
  if(index>=stock.length)throw new RangeError(`Missing native stock index ${index}`);
  return stock[index]&255;
}
/** Native decrement leaf; action-success/free-use gating belongs to 0x41DC43. */
export function decrementNativeConsumable(stock:readonly number[],itemId:number):number[]{
  const result=stock.slice(),index=nativeConsumableIndex(itemId);
  if(index!==undefined)result[index]=Math.max(0,nativeConsumableCount(stock,itemId)-1);
  return result;
}
