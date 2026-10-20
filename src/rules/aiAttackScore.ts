export interface NativeAiAttackScoreInput {
  currentHp:number; maxHp:number; predictedDamage:number;
  attackerMode:number; targetFlags:number; targetIdentity:number;
  leaderMatch:boolean; covered:boolean; sameSide:boolean; candidateRisk:boolean;
  targetSlot?:number;
}

/** Native 0x43FFED -> 0x43B470 -> 0x4077D0. */
export function nativeAiClassFiltered(classId:number):boolean{
  const type=classId<39?Math.floor(classId/3):classId<53?classId-26:27;
  return [8,9,10,11,18,19,20].includes(type);
}

/** Native 0x438A20 ordinary (non-special-range) score branch. */
export function nativeAiOrdinaryAttackScore(input:NativeAiAttackScoreInput):number{
  let score=0;
  if(!input.sameSide){
  score=2;
  if(input.predictedDamage>=input.currentHp)score=80;
  else if(Math.floor(input.predictedDamage*10/input.maxHp)!==0)score=16;
  else if(Math.floor(input.currentHp*100/input.maxHp)<41)score=16;
  else if(input.attackerMode===1)score=10;
  }
  if(input.targetFlags&8)score+=8;
  if(score!==0){
    if(input.targetIdentity<174)score+=input.leaderMatch||input.targetSlot===35?8:4;
  }
  if(input.covered&&score<75)return 0;
  if(input.candidateRisk&&score>1)score-=1;
  return Math.max(0,score);
}
