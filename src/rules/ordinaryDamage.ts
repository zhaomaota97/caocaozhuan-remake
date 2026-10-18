import type {EquipmentSlot} from './equipmentCategory';
import {hasEquipmentCategory} from './equipmentCategory';
import type {MovementItem} from './movementBudget';
import type {GameRng} from './gameRng';

interface CombatActor {
  attack:number;defense:number;adaptation:number;nativeLevel:number;hp:number;
  classId:number;equipmentSlots:EquipmentSlot[];
}

function modifier(actor:CombatActor,items:MovementItem[],category:number):number{
  let value=0;
  for(const [slot,equipment] of actor.equipmentSlots.entries()){
    const item=items.find(row=>row.id===equipment.itemId);
    if(!item)continue;
    if(slot<2&&item.categoryByte<18&&(item.categoryByte&1)&&item.equipmentEffectCategory===category)value=item.secondaryValue;
    if(slot===2&&item.categoryByte===category)value=item.baseValue;
  }
  return value;
}

/** 0x43BC4B mode=0. Deterministic preview, without hit checks or random perturbation. */
function baseDamage(attacker:CombatActor,defender:CombatActor,items:MovementItem[],counter=false):number{
  const attack=Math.floor(attacker.attack*attacker.adaptation/10);
  const defense=Math.floor(defender.defense*defender.adaptation/10);
  let value=attack<defense?Math.max(1,attacker.nativeLevel+25-Math.floor((defense-attack)/2)):
    attacker.nativeLevel+25+Math.floor((attack-defense)/2);
  const kind=(actor:CombatActor)=>actor.classId<39?Math.floor(actor.classId/3):actor.classId-26;
  const a=kind(attacker),d=kind(defender);
  if(a===1){
    if(d===3)value=Math.max(1,Math.floor(value*3/5));
    else if([2,5].includes(d))value=Math.floor(value*3/2);
  }else if([2,4,5].includes(a)){
    if([3,17,16].includes(d))value=Math.floor(value*3/2);
    value-=Math.floor(modifier(defender,items,61)*value/100);
  }
  if(d===3)value+=Math.floor(modifier(attacker,items,45)*value/100);
  if(counter)value=Math.max(1,Math.floor(value*3/4));
  return value;
}

export function ordinaryDamage(attacker:CombatActor,defender:CombatActor,items:MovementItem[],counter=false):number{
  return Math.min(baseDamage(attacker,defender,items,counter),defender.hp);
}

type AccuracyActor=CombatActor&{agility:number;statusFlags:number};

/** Native 0x405CE6 / 0x405D69 ratio thresholds. */
function followupChance(attack:number,defense:number):number{
  if(attack>=defense*3)return 100;
  if(attack>=defense*2)return 20+Math.floor((attack-defense*2)*80/defense);
  if(attack>=defense)return 2+Math.floor((attack-defense)*18/defense);
  return 1;
}

export function doubleAttackChance(attacker:{agility:number},defender:{agility:number}):number{
  return followupChance(attacker.agility,defender.agility);
}

/** Native 0x406181: reactions and round 1 do not consume the follow-up random draw. */
export function repeatsAttack(attacker:{agility:number},defender:{agility:number},rng:GameRng,reactionDepth:number,round:number):boolean{
  return reactionDepth===0&&round===0&&rng.chance(doubleAttackChance(attacker,defender));
}

export function criticalChance(attacker:CombatActor&{luck:number},defender:{luck:number},items:MovementItem[]):number{
  if(hasEquipmentCategory(attacker.equipmentSlots,items,0x29))return 100;
  return followupChance(attacker.luck,defender.luck);
}

/** Native 0x43B50D, attack-side mode 0. Does not consume random numbers. */
export function ordinaryAccuracy(attacker:AccuracyActor,defender:AccuracyActor,items:MovementItem[]):number{
  const type=attacker.classId<39?Math.floor(attacker.classId/3):attacker.classId-26;
  if([2,4,5].includes(type)&&hasEquipmentCategory(defender.equipmentSlots,items,56))return 0;
  if(defender.statusFlags&8)return 100;
  const a=attacker.agility,d=defender.agility;
  let chance:number;
  if(a>=d*2)chance=100;
  else if(a>=d)chance=90+Math.floor((a-d)*10/d);
  else if(a>=Math.floor(d/2))chance=60+Math.floor(Math.max(0,a-Math.floor(d/2))*30/Math.floor(d/2));
  else chance=30+Math.floor(Math.max(0,a-Math.floor(d/3))*30/Math.floor(d/3));
  chance=Math.min(100,chance+modifier(attacker,items,39));
  chance=Math.max(0,chance-modifier(defender,items,53));
  return Math.max(0,chance-modifier(defender,items,55));
}

/** Native 0x43BC4B mode=1; this is one strike, not the whole attack/counter sequence. */
export function ordinaryStrike(attacker:AccuracyActor,defender:AccuracyActor,items:MovementItem[],rng:GameRng,counter=false):number{
  if(!rng.chance(ordinaryAccuracy(attacker,defender,items)))return 0;
  const value=baseDamage(attacker,defender,items,counter),draw=rng.bounded(7);
  const varied=draw<3?Math.max(1,value-draw):value-2+draw;
  return Math.min(varied,defender.hp);
}

/** 0x405E03 primary target result; XP and animation dispatch are separate stages. */
export function ordinaryResult(attacker:AccuracyActor&{luck:number},defender:AccuracyActor&{luck:number;mp:number},
  items:MovementItem[],rng:GameRng,counter=false,round=0){
  let damage=ordinaryStrike(attacker,defender,items,rng,counter);
  const critical=defender.hp>0&&rng.chance(criticalChance(attacker,defender,items));
  if(critical)damage=hasEquipmentCategory(defender.equipmentSlots,items,57)?0:Math.floor(damage*3/2);
  if(round!==0&&hasEquipmentCategory(defender.equipmentSlots,items,58))damage=0;
  const mpShield=defender.mp>0&&hasEquipmentCategory(defender.equipmentSlots,items,60);
  return {hpDamage:mpShield?0:Math.min(damage,defender.hp),mpDamage:mpShield?Math.min(damage,defender.mp):0,critical};
}

/** Native 0x405889 data writeback; automatic items and reward callbacks are separate. */
export function ordinaryWriteback(attacker:CombatActor,defender:AccuracyActor&{mp:number;actorFlags:number},
  result:{hpDamage:number;mpDamage:number},items:MovementItem[],rng:GameRng){
  let status=defender.statusFlags;
  if(result.hpDamage!==0||result.mpDamage!==0){
    for(const [category,mask,specialClass] of [[35,8,50],[36,16,49],[37,2,42],[38,4,-1]]){
      if(hasEquipmentCategory(attacker.equipmentSlots,items,category))status|=mask;
      if(attacker.classId===specialClass&&rng.chance(60))status|=mask;
    }
  }
  return {hp:defender.hp-result.hpDamage,mp:defender.mp-result.mpDamage,statusFlags:status,actorFlags:defender.actorFlags&~32};
}
