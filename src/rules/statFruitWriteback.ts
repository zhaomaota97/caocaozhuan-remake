/** Native 0x41D080 state part, following successful target selection. */
export function nativeStatFruitWriteback(category:number,value:number,stats:readonly number[],ranks:readonly number[],states:readonly number[]){
  const index=({70:0,71:2,72:1,73:3,74:4} as Record<number,number>)[category];
  if(index===undefined)throw new RangeError('Not a native stat fruit');
  const nextStats=stats.slice(),nextRanks=ranks.slice(),nextStates=states.slice();
  const gain=Math.floor((value&255)/2);
  nextStats[index]=Math.min(255,stats[index]+gain);
  nextRanks[index]=Math.min(50,ranks[index]+gain);
  nextStates[index]=states[index]<3?3:6;
  return {stats:nextStats,ranks:nextRanks,states:nextStates};
}
