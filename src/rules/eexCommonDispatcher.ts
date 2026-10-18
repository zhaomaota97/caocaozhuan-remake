import {applyEexOpcode32,applyEexOpcode58,applyEexOpcode103,type NativeCommonState} from './nativeCommonState';

export type NativeEexCommonCommand=
  | {opcode:32;tag:number;value:number}
  | {opcode:58;modeTag:number;mode:number;valueTag:number;value:number}
  | {opcode:103;tag:number;value:number};

/** Dispatch only handlers whose native common-record writes are verified. */
export function dispatchNativeCommonCommand(state:NativeCommonState,command:NativeEexCommonCommand){
  switch(command.opcode){
    case 32:{const result=applyEexOpcode32(state,command.tag,command.value);return result;}
    case 58:{const result=applyEexOpcode58(state,command.modeTag,command.mode,command.valueTag,command.value);return result;}
    case 103:{const result=applyEexOpcode103(state,command.tag,command.value);return result;}
  }
}
