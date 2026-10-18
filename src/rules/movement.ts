import type { BattleMap, Unit } from '../model/battle';
export const directions = [[0,-1],[1,0],[0,1],[-1,0],[1,-1],[1,1],[-1,1],[-1,-1]] as const;
export function reachable(map: BattleMap, units: Unit[], unit: Unit): Set<string> {
  const occupied = new Set(units.filter(x=>x.id!==unit.id).map(x=>`${x.x},${x.y}`));
  const result = new Set<string>(); const queue: Array<[number,number,number]> = [[unit.x,unit.y,0]];
  const seen = new Set([`${unit.x},${unit.y}`]);
  while(queue.length){const [x,y,cost]=queue.shift()!; if(cost>0) result.add(`${x},${y}`); if(cost>=unit.move) continue;
    for(const [dx,dy] of directions){const nx=x+dx,ny=y+dy,key=`${nx},${ny}`; if(nx<0||ny<0||nx>=map.width||ny>=map.height||seen.has(key)||occupied.has(key)) continue; if(map.terrain[ny*map.width+nx]===255) continue; seen.add(key);queue.push([nx,ny,cost+1]);}}
  return result;
}
