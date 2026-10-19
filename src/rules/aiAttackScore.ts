export interface NativeAiAttackScoreInput {
  currentHp:number; maxHp:number; predictedDamage:number;
  attackerMode:number; targetFlags:number; targetIdentity:number;
  leaderMatch:boolean; covered:boolean; sameSide:boolean; candidateRisk:boolean;
}

/** Native 0x438A20 ordinary (non-special-range) score branch. */
export function nativeAiOrdinaryAttackScore(input:NativeAiAttackScoreInput):number{
  if(input.sameSide||input.covered||input.currentHp<=0)return 0;
  let score=2;
  if(input.predictedDamage>=input.currentHp)score=80;
  else if(Math.floor(input.predictedDamage*10/input.maxHp)!==0)score=16;
  else if(Math.floor(input.currentHp*100/input.maxHp)<41)score=16;
  else if(input.attackerMode===1)score=10;
  if(input.targetFlags&8)score+=8;
  if(score!==0){
    if(input.targetIdentity===174)score+=input.leaderMatch?8:4;
  }
  if(input.candidateRisk&&score===1)score-=1;
  return Math.max(0,score);
}
