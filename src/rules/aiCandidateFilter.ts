import type {Unit} from '../model/battle';

/** Native 0x437A04 candidate collection boundary. */
export function nativeAiCandidates(actor:Unit,units:Unit[],width:number,height:number,relation:'opposing'|'allied'='opposing'):Unit[]{
  return units.filter(target=>{
    if(target===actor||target.hp<=0||target.nativeHidden)return false;
    if(target.x<0||target.y<0||target.x>=width||target.y>=height)return false;
    const same=target.side===actor.side;
    return relation==='allied'?same:!same;
  });
}

/** Native selector keeps the first candidate on equal score; score remains a
 * separate, unresolved 0x438A20/0x4395AE concern. */
export function nearestNativeCandidate(actor:Unit,units:Unit[],width:number,height:number):Unit|undefined{
  return nativeAiCandidates(actor,units,width,height).sort((a,b)=>
    (Math.abs(a.x-actor.x)+Math.abs(a.y-actor.y))-(Math.abs(b.x-actor.x)+Math.abs(b.y-actor.y))||a.id.localeCompare(b.id))[0];
}
