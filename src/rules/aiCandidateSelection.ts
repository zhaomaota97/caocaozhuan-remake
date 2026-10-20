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

export interface NativeAiOccupant {slot:number;groupSlot:number;hp:number;x:number;y:number;}
/** Native shape 0/1 enumeration; other shapes need their own ordered traces. */
export function collectNativeAdjacentCandidates(origin:{x:number;y:number},shape:number,width:number,height:number,actorGroupSlot:number,occupants:NativeAiOccupant[]):number[]{
  const kind=shape&127;
  if(kind!==0&&kind!==1)throw new Error(`Unverified ordered AI shape ${shape}`);
  const offsets=kind===0?[[0,-1],[1,0],[0,1],[-1,0]]:[[0,-1],[1,0],[0,1],[-1,0],[1,-1],[1,1],[-1,1],[-1,-1]];
  const result:number[]=[];
  for(const [dx,dy] of offsets){
    const x=origin.x+dx,y=origin.y+dy;
    if(x<0||y<0||x>=width||y>=height)continue;
    const occupant=occupants.find(row=>row.x===x&&row.y===y);
    if(occupant&&occupant.hp!==0&&(occupant.groupSlot<35)!==(actorGroupSlot<35))result.push(occupant.slot);
  }
  return result;
}
