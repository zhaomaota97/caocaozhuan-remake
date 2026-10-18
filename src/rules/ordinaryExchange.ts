import {ordinaryResult,ordinaryWriteback,repeatsAttack} from './ordinaryDamage';
import {hasEquipmentCategory} from './equipmentCategory';
import {attackRange,inAttackRange} from './attackRange';
import {GameRng} from './gameRng';
import type {MovementItem} from './movementBudget';

export interface ExchangeActor {
  id:string;x:number;y:number;hp:number;mp:number;actorFlags:number;statusFlags:number;
  attack:number;defense:number;agility:number;luck:number;adaptation:number;nativeLevel:number;classId:number;
  equipmentSlots:{slot:number;itemId:number;byte1:number;byte2:number}[];
}
export interface ExchangeStrike {
  attacker:string;defender:string;depth:number;round:number;
  hpDamage:number;mpDamage:number;critical:boolean;
  after:{hp:number;mp:number;statusFlags:number;actorFlags:number};
}

/** Verified primary-target path; unsupported splash/automatic-item actions are rejected before mutation. */
export function ordinaryExchange(attacker:ExchangeActor,defender:ExchangeActor,rng:GameRng,rules:{items:MovementItem[];classes:{id:number;range:number}[];shapes:{id:number;fullMap:boolean;offsets:number[][]}[]}){
  const {items,classes,shapes}=rules;
  const actors=new Map([attacker,defender].map(actor=>[actor.id,{...actor}]));
  const strikes:ExchangeStrike[]=[];
  for(const actor of actors.values()){
    if([16,17,43].includes(actor.classId)||hasEquipmentCategory(actor.equipmentSlots,items,43)||hasEquipmentCategory(actor.equipmentSlots,items,62)){
      return {supported:false as const,strikes,reason:'此装备或兵种的多目标、自动道具流程尚未接入'};
    }
  }
  const reachable=(a:ExchangeActor,d:ExchangeActor)=>inAttackRange(a,d,attackRange(a,items,classes),shapes);
  if(attacker.hp<=0||defender.hp<=0||!reachable(attacker,defender))return {supported:false as const,strikes,reason:'目标不在攻击范围内'};
  let a=actors.get(attacker.id)!,d=actors.get(defender.id)!;
  for(let depth=0;depth<3;depth++){
    for(let round=0;round<2;round++){
      const result=ordinaryResult(a,d,items,rng,depth!==0,round);
      // 0x405744 consumes this dialogue draw before status writeback and repeat.
      if(result.critical)rng.chance(25);
      const after=ordinaryWriteback(a,d,result,items,rng);
      Object.assign(d,after);strikes.push({attacker:a.id,defender:d.id,depth,round,...result,after});
      if(!repeatsAttack(a,d,rng,depth,round))break;
    }
    if(depth>=2||(depth!==0&&!hasEquipmentCategory(d.equipmentSlots,items,40))||d.hp<=0||(d.statusFlags&8)||hasEquipmentCategory(a.equipmentSlots,items,44)||!reachable(d,a))break;
    [a,d]=[d,a];
  }
  return {supported:true as const,strikes};
}
