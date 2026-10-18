/** Native public-record +6 writes used by EEX opcode 103 and opcode 58. */
export function applyNativeChapterPhase(value:number,tag:number):{status:number;phase:number}{
  if(tag!==4)return {status:5,phase:0};
  if((value&0xffff)===0x8000)return {status:5,phase:0};
  return {status:1,phase:Math.max((value&0xff)-1,0)};
}

/** Opcode 58 direct phase branch: tag40 must equal 1; tag4 supplies the byte. */
export function applyOpcode58ChapterPhase(oldPhase:number,mode:number,value:number,modeTag:number,valueTag:number){
  if(modeTag!==40||valueTag!==4||mode!==1)return {status:1,phase:oldPhase&0xff};
  return {status:1,phase:value&0xff};
}
