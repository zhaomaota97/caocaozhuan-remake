/** Verified outer target-list predicates from native 0x420422.
 * These are intentionally separate from range geometry and effect mutation.
 */
export function sameNativeFaction(actorSlot:number,targetSlot:number,relation:number):boolean{
  const actorFriendly=actorSlot<35,targetFriendly=targetSlot<35;
  if(relation===0)return actorFriendly!==targetFriendly;
  if(relation===1)return actorFriendly===targetFriendly;
  return true;
}

export function nativeTargetRelation(actorSlot:number,targetSlot:number,relation:number):boolean{
  return sameNativeFaction(actorSlot,targetSlot,relation);
}
