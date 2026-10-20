/** Static selection in 0x45137C, pixel clearing by native 0x430A07. */
export function nativeUnitTerrainMask(source:Uint8Array,size:48|64,terrain:number,masks:readonly {size:number;terrain:number;blocked:readonly boolean[]}[]):Uint8Array{
  if(source.length!==size*size)throw new RangeError('Invalid native unit tile size');
  const result=source.slice(),mask=masks.find(row=>row.size===size&&row.terrain===terrain);
  if(mask)for(let i=0;i<result.length;i++)if(mask.blocked[i])result[i]=0;
  return result;
}
