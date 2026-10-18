import type {MovementItem} from './movementBudget';
import type {EquipmentSlot} from './equipmentCategory';

interface RangeActor {classId:number;equipmentSlots:EquipmentSlot[];x:number;y:number;}
interface RangeShape {id:number;fullMap:boolean;offsets:number[][];}

/** Original 0x43F8BE / 0x407AF2: later equipment slots override earlier range effects. */
export function attackRange(actor:RangeActor,items:MovementItem[],classes:{id:number;range:number}[]):number{
  let range=classes.find(row=>row.id===actor.classId)?.range??255;
  for(const [index,slot] of actor.equipmentSlots.entries()){
    const item=items.find(row=>row.id===slot.itemId);
    if(!item)continue;
    if(index<2&&item.categoryByte<18&&(item.categoryByte&1)&&item.equipmentEffectCategory===42)range=item.secondaryValue;
    if(index===2&&item.categoryByte===42)range=item.baseValue;
  }
  return range;
}

export function inAttackRange(actor:RangeActor,target:{x:number;y:number},range:number,shapes:RangeShape[]):boolean{
  if(range===255)return false;
  const shape=shapes.find(row=>row.id===(range&127));
  return Boolean(shape&&(shape.fullMap||shape.offsets.some(([dx,dy])=>actor.x+dx===target.x&&actor.y+dy===target.y)));
}
