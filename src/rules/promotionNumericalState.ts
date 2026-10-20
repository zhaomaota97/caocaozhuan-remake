/** Numerical helper sequence in 0x41D4DB; caller must check promotion eligibility. */
export function nativePromotionNumericalState(unit:{classId:number;maxHpBase:number;maxMpBase:number},oldClass:{hpGrowth:number;mpGrowth:number}){
  return {classId:(unit.classId+1)&255,maxHpBase:Math.min(500,unit.maxHpBase+((oldClass.hpGrowth*2)&255)),maxMpBase:Math.min(250,unit.maxMpBase+((oldClass.mpGrowth*2)&255))};
}
