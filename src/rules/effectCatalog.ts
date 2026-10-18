import catalog from '../../data/mappings/effects-runtime.json';

export interface RuntimeEffect {
  effectId:number; name:string; dispatchCode:number; resource:string;
  entry:number; sound:string; timelineFrames:number;
}

const effects=catalog as RuntimeEffect[];
export function effectById(effectId:number):RuntimeEffect|undefined{
  return effects.find(effect=>effect.effectId===effectId);
}
export function effectsForDispatch(dispatchCode:number):RuntimeEffect[]{
  return effects.filter(effect=>effect.dispatchCode===dispatchCode);
}
export function allRuntimeEffects():RuntimeEffect[]{return effects.slice();}
