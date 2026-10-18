export interface NativeGrowthInput {unitId:number;level:number;experience:number;stats:number[];rankBases:number[];classGrowth:number[];}
export interface NativeGrowthOutput {level:number;experience:number;stats:number[];levelsGained:number;eligible:boolean;}
function rankBonus(base:number){return base<25?1:base<35?2:base<45?3:4;}
/** Native 0x408950/0x4073B8/0x406E17 level writeback. */
export function nativeUnitGrowth(input:NativeGrowthInput,totalExperience:number):NativeGrowthOutput{
  const stats=input.stats.slice();
  if(input.unitId>=26||input.level>=50)return {level:input.level,experience:input.level>=50?255:input.experience,stats,levelsGained:0,eligible:false};
  const target=Math.max(0,totalExperience|0),levels=Math.min(Math.max(0,Math.floor(target/100)-Math.floor(input.experience/100)),50-input.level);
  const increments=input.classGrowth.map((growth,index)=>index<5?Math.floor((growth+rankBonus(input.rankBases[index]??0))/2):growth);
  const limits=[255,255,255,255,255,500,250];
  for(let i=0;i<Math.min(7,stats.length);i++)stats[i]=Math.min(limits[i],stats[i]+levels*increments[i]);
  return {level:input.level+levels,experience:input.level+levels>=50?255:target%100,stats,levelsGained:levels,eligible:true};
}
