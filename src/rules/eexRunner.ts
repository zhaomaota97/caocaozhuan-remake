import {dispatchNativeCommonCommand,type NativeEexCommonCommand} from './eexCommonDispatcher';
import {parseNativeDialogueSegments,type NativeDialogueSegment} from './eexDialogue';
import type {NativeCommonState} from './nativeCommonState';

export type VerifiedEexCommand=
  | {kind:'common';command:NativeEexCommonCommand}
  | {kind:'dialogue';text:string};
export interface EexRunnerState {common:NativeCommonState;dialogue:NativeDialogueSegment[];unsupported:number[];}

/** Executes only the opcode semantics independently verified from native code. */
export function runVerifiedEex(commands:VerifiedEexCommand[],initial:NativeCommonState):EexRunnerState{
  const state:EexRunnerState={common:initial,dialogue:[],unsupported:[]};
  for(const command of commands){
    if(command.kind==='common')state.common=dispatchNativeCommonCommand(state.common,command.command).state;
    else if(command.kind==='dialogue')state.dialogue.push(...parseNativeDialogueSegments(command.text));
  }
  return state;
}
