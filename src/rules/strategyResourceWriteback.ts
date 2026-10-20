export interface NativeStrategyResources {
  success:boolean;effectId:number;hp:number;maxHp:number;mp:number;maxMp:number;
  cost:number;costDivisor?:number;magnitude:number;
}

/** Native 0x422F0D resource part; excludes rewards and presentation callbacks. */
export function nativeStrategyResourceWriteback(input:NativeStrategyResources):{hp:number;mp:number}{
  if(!input.success)return {hp:input.hp,mp:input.mp};
  const divisor=input.costDivisor??1;
  if(divisor===0)throw new RangeError('Native strategy cost divisor is zero');
  const cost=Math.floor(input.cost/divisor);
  let hp=input.hp,mp=Math.max(0,input.mp-cost);
  if(input.effectId===20)hp+=Math.min(input.magnitude,input.maxHp-hp);
  else if(input.effectId===22)mp+=Math.min(input.magnitude,input.maxMp-mp);
  return {hp:Math.min(input.maxHp,hp),mp:Math.min(input.maxMp,mp)};
}
