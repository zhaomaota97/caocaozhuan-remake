import {applyNativePortraitFlags} from './eexPortraitFlags';
import {applyNativeChapterPhase,applyOpcode58ChapterPhase} from './eexPortraitPhase';

/** Serializable projection of the native common record fields used by FACE. */
export interface NativeCommonState { portraitPhase:number; portraitFlags:number; }

export function applyEexOpcode32(state:NativeCommonState,tag:number,value:number):{status:number;state:NativeCommonState}{
  const result=applyNativePortraitFlags(state.portraitFlags,tag,value);
  return {status:result.status,state:result.status===1?{...state,portraitFlags:result.flags}:state};
}
export function applyEexOpcode103(state:NativeCommonState,tag:number,value:number):{status:number;state:NativeCommonState}{
  const result=applyNativeChapterPhase(value,tag);
  return {status:result.status,state:result.status===1?{...state,portraitPhase:result.phase}:state};
}
export function applyEexOpcode58(state:NativeCommonState,modeTag:number,mode:number,valueTag:number,value:number){
  const result=applyOpcode58ChapterPhase(state.portraitPhase,mode,value,modeTag,valueTag);
  return {status:result.status,state:{...state,portraitPhase:result.phase}};
}
