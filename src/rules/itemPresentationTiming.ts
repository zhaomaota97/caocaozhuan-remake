/** Native clock 0x47EB97 is floor(GetTickCount()/50). */
export function nativeItemWaitRemaining(startTick:number,waitTicks:number,currentTick:number):number{
  return Math.max(0,startTick+waitTicks-currentTick);
}

/** Static call order in 0x41C762; not including optional Meff execution. */
export function nativeItemPresentationStages(){
  return [
    {kind:'raised' as const,waitTicks:5},
    {kind:'origin' as const,waitTicks:10},
    ...Array.from({length:16},(_,frame)=>({kind:'blend' as const,frame,waitTicks:1})),
  ];
}
