export interface ExperienceAwardInput {enabled:boolean;attackerLevel:number;defenderLevel:number;hpDamage:number;defenderHp:number;multiplier:number;leaderMatch?:boolean;}
/** Native 0x40379B unit experience award. */
export function nativeUnitExperienceAward(input:ExperienceAwardInput):number{
  if(!input.enabled)return 0;
  const delta=input.defenderLevel-input.attackerLevel,lethal=input.hpDamage>=input.defenderHp;
  let base:number;
  if(lethal)base=delta>0?Math.min(200,32+8*delta):Math.max(10,32+4*delta);
  else base=delta>0?Math.min(100,8+2*delta):Math.max(1,8+delta);
  if(lethal&&input.leaderMatch)base*=2;
  return Math.floor(base*input.multiplier/10);
}

export function nativeWeaponExperienceAward(enabled:boolean,attackerLevel:number,defenderLevel:number,hpDamage:number,mpDamage:number,multiplier:number,weaponType:number):number{
  if(!enabled||weaponType!==0)return 0;
  const base=hpDamage===0&&mpDamage===0?1:attackerLevel>defenderLevel?2:3;
  return Math.floor(base*multiplier/10);
}

/** Native 0x403A85 defender armor experience award. */
export function nativeArmorExperienceAward(attackerLevel:number,defenderLevel:number,hpDamage:number,mpDamage:number,multiplier:number,defenderByte5:number):number{
  if(defenderByte5!==0)return 0;
  const base=hpDamage===0&&mpDamage===0?1:attackerLevel<defenderLevel?3:4;
  return Math.floor(base*multiplier/10);
}
