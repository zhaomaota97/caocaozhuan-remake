/** Native 0x43053E for actor renderer arguments (4,8,4). */
export function nativeActorStatusPixel(index:number,palette:readonly number[],lookup:readonly number[]):number{
  if(index===0)return 0;
  const a=Math.max(0,palette[index*3]-6),b=Math.max(0,palette[index*3+1]-6),c=Math.min(15,palette[index*3+2]+2);
  return lookup[a*256+b*16+c];
}
/** Static gate in native 0x43EB1F; uses phase byte from 0x41C2D0. */
export function nativeActorStatusColorActive(statusFlags:number,phase:number):boolean{
  return (statusFlags&16)!==0&&(phase&3)>1;
}
