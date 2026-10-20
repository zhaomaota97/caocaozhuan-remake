/** Native 0x41C4E9 only; range, faction and inventory gates are separate. */
export function nativeManualItemEligible(category:number,target:{statusFlags:number;classId:number;nativeLevel:number},checkMode:boolean):boolean{
  const mask=({65:8,66:16,67:2,68:4} as Record<number,number>)[category];
  if(checkMode&&mask!==undefined)return (target.statusFlags&mask)!==0;
  if(checkMode&&category===69)return target.statusFlags!==0;
  if(category===75)return target.nativeLevel<50;
  if(category===76)return target.classId<39&&target.classId%3!==2&&target.nativeLevel>=(target.classId%3+1)*15;
  return true;
}
