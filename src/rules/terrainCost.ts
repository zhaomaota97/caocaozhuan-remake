import {hasEquipmentCategory,type EquipmentSlot,type ItemCategory} from './equipmentCategory';

export interface TerrainMovement {movementType:number;costs:number[];}

/** Original 0x4077D0. Type 27 is the invalid/unmapped sentinel. */
export function movementType(classId:number):number{
  return classId<39 ? Math.floor(classId/3) : classId<53 ? classId-26 : 27;
}

/** Original 0x43F7CF. Equipment category 0x22 reduces passable cost to one. */
export function terrainCost(classId:number,slots:EquipmentSlot[],terrain:number,items:ItemCategory[],table:TerrainMovement[]):number{
  const kind=movementType(classId);
  if(kind>=27)return 255;
  const cost=table.find(row=>row.movementType===kind)?.costs[terrain];
  if(cost===undefined||cost===255)return 255;
  return hasEquipmentCategory(slots,items,0x22)?1:cost;
}
