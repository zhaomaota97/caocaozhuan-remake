/** Native 0x4075A7. storedIndex is int32(unit+4), not the roster index. */
export function portraitIndex(characterId:number,storedIndex:number,flags:number,phase:number):number {
  const identity=characterId&0xfff;
  if(identity===0){
    const expression=flags&15;
    return (phase>=2?4:0)+([1,2,3].includes(expression)?expression:0);
  }
  if(identity===1){
    if((flags&15)===4)return 224;
    return flags&128?storedIndex+7:223;
  }
  if(identity===35&&(flags&16))return 214;
  if(identity===8&&(flags&32))return 226;
  if(identity===4&&(flags&64))return 227;
  return storedIndex+7;
}

/** Native palette upload: stored channel order B,R,G, four-bit precision. */
export function portraitRgba(pixels:Uint8Array,palette:Uint8Array):Uint8ClampedArray {
  if(pixels.length!==64*80)throw new Error('FACE requires 64x80 index pixels');
  const rgba=new Uint8ClampedArray(pixels.length*4);
  for(let i=0;i<pixels.length;i++){
    const index=pixels[i],offset=index*3;
    if(offset+2>=palette.length)throw new Error(`Missing FACE palette index ${index}`);
    rgba[i*4]=palette[offset+1]&0xf0;
    rgba[i*4+1]=palette[offset+2]&0xf0;
    rgba[i*4+2]=palette[offset]&0xf0;
    rgba[i*4+3]=index===0?0:255;
  }
  return rgba;
}
