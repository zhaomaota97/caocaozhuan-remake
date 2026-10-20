/** 0x42FD5A as invoked by item animation: current palette, invert=1, strength=0. */
export function nativeItemBlendPixel(source:number,background:number,frame:number,palette:readonly number[],lookup:readonly number[]):number{
  if(source===0)return background;
  const rgb=palette.slice(source*3,source*3+3);
  const quantize=(channels:readonly number[])=>lookup[channels[0]*256+channels[1]*16+channels[2]];
  if(frame===0)return quantize(rgb);
  const coefficient=frame*16;
  const weight=256-coefficient;
  const channels=rgb.map((value,index)=>Math.min(15,((palette[background*3+index]*coefficient+value*weight)>>8)&255));
  return quantize(channels);
}
