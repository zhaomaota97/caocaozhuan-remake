export interface NativeExperienceItemCallbacks {
  present:()=>void;
  grow:(totalExperience:number,display:1)=>void;
  maximumHp:()=>number;
  maximumMp:()=>number;
}

/** Native 0x41D3D9 ordering; growth and presentation remain explicit dependencies. */
export function runNativeExperienceItem(input:{targetSelected:boolean;level:number;experience:number;value:number;hp:number;mp:number},callbacks:NativeExperienceItemCallbacks){
  if(!input.targetSelected||input.level>=50)return {hp:input.hp,mp:input.mp};
  callbacks.present();
  callbacks.grow(input.experience+input.value,1);
  return {hp:callbacks.maximumHp(),mp:callbacks.maximumMp()};
}
