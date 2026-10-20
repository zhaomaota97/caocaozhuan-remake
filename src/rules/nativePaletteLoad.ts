/** Native 0x41E050 after successful resource read; preserve unwritten bytes. */
export function nativePaletteLoad(previous:readonly number[],resource:readonly number[]):number[]{
  if(previous.length!==768||resource.length>768)throw new RangeError('Invalid native palette span');
  const next=previous.slice();
  for(let i=0;i<resource.length;i++)next[i]=resource[i];
  return next.map(value=>(value&255)>>>4);
}
