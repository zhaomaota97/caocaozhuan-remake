/** Native 0x430480; retain transparency, subtract four-bit channels then quantize. */
export function nativeDarkenedPixel(index:number,amount:number,palette:readonly number[],lookup:readonly number[]):number{
  if(index===0)return 0;
  const a=Math.max(0,palette[index*3]-amount),b=Math.max(0,palette[index*3+1]-amount),c=Math.max(0,palette[index*3+2]-amount);
  return lookup[a*256+b*16+c];
}
/** Native 0x43EB1F checks both action bits and nonzero current HP. */
export function nativeActorIsDarkened(actorFlags:number,hp:number):boolean{
  return (actorFlags&6)===6&&hp!==0;
}
