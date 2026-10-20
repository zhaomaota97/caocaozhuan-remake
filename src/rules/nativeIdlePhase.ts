/** Native 0x406730; phase is explicitly advanced by individual control loops. */
export function nextNativeIdlePhase(phase:number):number{return (phase+1)&7;}
/** Idle wait 0x455CB2 uses 0x42C4CB(4), which doubles 50ms clock ticks. */
export const NATIVE_IDLE_WAIT_TICKS=8;
export const NATIVE_IDLE_WAIT_MS=NATIVE_IDLE_WAIT_TICKS*50;
