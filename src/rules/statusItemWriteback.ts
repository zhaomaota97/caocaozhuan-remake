/** Native 0x41CF61 -> 0x418DA0; action/visual flags are a different byte. */
export function nativeStatusItemWriteback(category:number,statusFlags:number,targetSelected:boolean):number{
  if(!targetSelected)return statusFlags;
  const mask=({65:8,66:16,67:2,68:4,69:30} as Record<number,number>)[category];
  if(mask===undefined)throw new RangeError(`Not a native status-item category: ${category}`);
  return statusFlags&~mask&255;
}
