import {stopsExpansion,type MovementActor} from './movementCosts';
import type {ItemCategory} from './equipmentCategory';

export const directions=[[0,-1],[1,0],[0,1],[-1,0]] as const;

/** Native 0x437E2E: descend the cost map in N/E/S/W order, then reverse. */
export function movementPath(width:number,height:number,costs:number[],actors:MovementActor[],actor:MovementActor,x:number,y:number,items:ItemCategory[]):number[]{
  if(costs[y*width+x]===255)return [];
  const reverse:number[]=[];
  for(let count=0;count<width*height && (x!==actor.x || y!==actor.y);count++){
    let best=costs[y*width+x],chosen=-1;
    for(let direction=0;direction<4;direction++){
      const [dx,dy]=directions[direction],nx=x+dx,ny=y+dy;
      if(nx<0||ny<0||nx>=width||ny>=height)continue;
      const origin=nx===actor.x&&ny===actor.y;
      if(!origin&&stopsExpansion(width,height,actors,actor,ny*width+nx,items))continue;
      if(costs[ny*width+nx]<best){best=costs[ny*width+nx];chosen=direction;}
    }
    if(chosen<0)return [];
    reverse.push((chosen+2)&3);
    x+=directions[chosen][0];y+=directions[chosen][1];
  }
  return reverse.reverse();
}

/** Native 0x44201B; setting 1 is the middle speed option. */
export function movementFrames(classId:number,direction:number,setting=1){
  const type=classId<39?Math.floor(classId/3):classId-26;
  const step=([0,3,4,11,13,17,20].includes(type)?[48,24,12]:[48,12,6])[setting];
  const bank=[1,2,0,2][direction];
  return Array.from({length:48/step},(_,i)=>{
    const progress=(i+1)*step;
    return {progress,frame:bank*2+Math.floor((progress-1)/24)};
  });
}
