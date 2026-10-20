/** Native 0x438965 selector over an already ordered native slot list. */
export function selectNativeAiCandidate(candidates:readonly number[],scoreFor:(slot:number)=>number):{score:number;target:number}{
  let score=0,target=255;
  for(const slot of candidates){
    if(slot<0||slot>=115)break;
    const value=scoreFor(slot)&255;
    if(value>score){score=value;target=slot;}
  }
  return {score,target};
}
