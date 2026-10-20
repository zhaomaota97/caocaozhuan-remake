/** Native 0x43EB1F overlay call, relative to the actor tile's top-left. */
export function nativeActorStatusIcon(status:number,phase:number){
  const mask=status&14,odd=(phase&1)!==0;
  if(mask===0)return undefined;
  const single=({2:0x1a4c0,4:0x1a3c0,8:0x1a2c0} as Record<number,number>)[mask];
  if(single!==undefined)return {x:odd?28:4,y:0,width:16,height:16,offset:single,mode:4};
  const pair=({6:[0x1a3c0,0x1a4c0],10:[0x1a4c0,0x1a2c0],12:[0x1a3c0,0x1a2c0],14:[0x1a4c0,0x1a2c0]} as Record<number,number[]>)[mask];
  return {x:odd?4:28,y:0,width:16,height:16,offset:pair[Number(odd)],mode:4};
}
