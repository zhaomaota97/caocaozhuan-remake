import type {EquipmentSlot,ItemCategory} from './equipmentCategory';

export interface MovementItem extends ItemCategory {baseValue:number;secondaryValue:number;}
export interface ClassMovement {id:number;baseMove:number;}
export interface BudgetActor {classId:number;statusFlags:number;movementTier:number;equipmentSlots:EquipmentSlot[];}

/** Original 0x40727B / 0x407C0E stat 7 / 0x43F74F. Byte additions wrap as in native code. */
export function movementBudget(actor:BudgetActor,items:MovementItem[],classes:ClassMovement[]):number{
  const base=classes.find(row=>row.id===actor.classId)?.baseMove;
  if(base===undefined)throw new Error(`Unknown class ${actor.classId}`);
  let bonus=0;
  for(let slot=0;slot<Math.min(3,actor.equipmentSlots.length);slot++){
    const item=items.find(row=>row.id===actor.equipmentSlots[slot].itemId);
    if(!item)continue;
    if(item.categoryByte===0x20)bonus=(bonus+item.baseValue)&255;
    if(slot<2 && item.categoryByte<0x12 && (item.categoryByte&1) && item.equipmentEffectCategory===0x20){
      bonus=(bonus+item.secondaryValue)&255;
    }
  }
  let budget=Math.min(255,base+bonus);
  if(actor.statusFlags&2)return 0;
  if(actor.movementTier>=4)budget=Math.min(255,budget+2);
  else if(actor.movementTier<3)budget=Math.max(0,budget-1);
  return budget;
}
