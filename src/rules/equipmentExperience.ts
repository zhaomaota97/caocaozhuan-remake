export interface EquipmentExperienceInput {slot:number;itemId:number;categoryByte:number;level:number;experience:number;gain:number;}
export interface EquipmentExperienceOutput {level:number;experience:number;levelsGained:number;updated:boolean;}
/** Native 0x4082D6 equipment level/experience writeback. */
export function nativeEquipmentExperience(input:EquipmentExperienceInput):EquipmentExperienceOutput{
  if(input.slot>1||input.itemId===255)return {level:input.level,experience:input.experience,levelsGained:0,updated:false};
  const cap=input.categoryByte<18&&(input.categoryByte&1)?9:3;
  let level=input.level,total=Math.max(0,input.experience+input.gain),levels=0;
  while(total>=100&&level<cap){level++;total-=100;levels++;}
  return {level,experience:level>=cap?255:total,levelsGained:levels,updated:true};
}

export interface NativeEquipmentSlot {slot:number;itemId:number;categoryByte:number;level:number;experience:number;[key:string]:unknown;}
export function updateNativeEquipmentSlots(slots:NativeEquipmentSlot[],slot:number,gain:number):NativeEquipmentSlot[]{
  return slots.map(entry=>{
    if(entry.slot!==slot)return {...entry};
    const result=nativeEquipmentExperience({...entry,gain});
    return {...entry,level:result.level,experience:result.experience};
  });
}
