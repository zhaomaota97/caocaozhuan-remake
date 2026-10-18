import {hasEquipmentCategory,type EquipmentSlot,type ItemCategory} from './equipmentCategory';
import {terrainCost,type TerrainMovement} from './terrainCost';
import {movementBudget,type BudgetActor,type MovementItem,type ClassMovement} from './movementBudget';

export interface MovementActor extends BudgetActor {
  id: string;
  x: number;
  y: number;
  classId: number;
  equipmentSlots: EquipmentSlot[];
}

/** Native 0x437D59: category 0x21 bypasses the four-neighbor hostile adjacency check. */
export function stopsExpansion(width:number,height:number,actors:MovementActor[],actor:MovementActor,index:number,items:ItemCategory[]):boolean{
  if(hasEquipmentCategory(actor.equipmentSlots,items,0x21))return false;
  const x=index%width,y=Math.floor(index/width);
  const friendly=Number(actor.id.slice(5))<35;
  for(const [dx,dy] of [[0,-1],[1,0],[0,1],[-1,0]]){
    const nx=x+dx,ny=y+dy;
    if(nx<0||ny<0||nx>=width||ny>=height)continue;
    const occupant=actors.find(unit=>unit.x===nx&&unit.y===ny);
    if(occupant && (Number(occupant.id.slice(5))<35)!==friendly)return true;
  }
  return false;
}

/** 0x438308, flags=0/restriction_mode=1. */
export function movementCosts(width: number, height: number, terrain: number[], actors: MovementActor[], actor: MovementActor,items:MovementItem[],table:TerrainMovement[],classes:ClassMovement[]): number[] {
  const budget=movementBudget(actor,items,classes);
  const costs=Array<number>(width*height).fill(255);
  const start=actor.y*width+actor.x;
  costs[start]=0;
  if(terrainCost(actor.classId,actor.equipmentSlots,terrain[start],items,table)===255)return costs;
  const friendly=(unit:MovementActor)=>Number(unit.id.slice(5))<35;
  const occupied=new Map(actors.map(unit=>[unit.y*width+unit.x,unit]));
  let wave=0;
  while(wave<budget){
    for(let index=0;index<costs.length;index++){
      if(costs[index]!==wave)continue;
      if(index!==start && stopsExpansion(width,height,actors,actor,index,items))continue;
      const x=index%width,y=Math.floor(index/width);
      for(const [dx,dy] of [[0,-1],[1,0],[0,1],[-1,0]]){
        const nx=x+dx,ny=y+dy;
        if(nx<0||ny<0||nx>=width||ny>=height)continue;
        const next=ny*width+nx;
        if(costs[next]!==255)continue;
        const step=terrainCost(actor.classId,actor.equipmentSlots,terrain[next],items,table);
        if(step===undefined||step===255||wave+step>budget)continue;
        const occupant=occupied.get(next);
        if(occupant && friendly(occupant)!==friendly(actor))continue;
        costs[next]=wave+step;
      }
    }
    const pending=costs.filter(cost=>cost>wave && cost!==255);
    if(!pending.length)break;
    wave=Math.min(...pending);
  }
  return costs;
}
