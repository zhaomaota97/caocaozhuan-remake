/** Native EEX opcode 0x20 / handler 0x416FD8. */
export function applyNativePortraitFlags(oldFlags:number,tag:number,value:number):{status:number;flags:number}{
  if(tag!==74)return {status:5,flags:oldFlags&0xff};
  if((value&0xffff)===0x8000)return {status:5,flags:oldFlags&0xff};
  if((value&0xff)===0xff)return {status:1,flags:oldFlags&0xe0};
  return {status:1,flags:((oldFlags&0xf0)|(value&0xff))&0xff};
}
