/** Native 0x43F54C: actor attribute state byte, distinct from status flags. */
export function nativeActorStatModifier(base:number,stateByte:number):number{
  if(stateByte<3)return Math.floor(base*7/10);
  if(stateByte===3)return base;
  return Math.floor(base*12/10);
}

/** Outer getters 0x43F4FE/0x43F595/0x43F631/0x43F67F. */
export function nativeBattleStat(base:number,stateByte:number):number{
  return Math.min(400,nativeActorStatModifier(base,stateByte));
}
