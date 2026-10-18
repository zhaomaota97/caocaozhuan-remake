/** Confirmed from native 0x454CEF/0x454B7E. Coordinates are camera tiles. */
export function nativeCameraSteps(from:{x:number;y:number},to:{x:number;y:number}):Array<{x:number;y:number}>{
  let x=from.x|0,y=from.y|0;
  const steps:Array<{x:number;y:number}>=[];
  while(x!==to.x||y!==to.y){
    const dx=Math.abs(x-to.x),dy=Math.abs(y-to.y);
    const sx=Math.min(4,Math.floor(dx/4)+1),sy=Math.min(4,Math.floor(dy/4)+1);
    if(x<to.x)x=Math.min(to.x,x+sx); else if(x>to.x)x=Math.max(to.x,x-sx);
    if(y<to.y)y=Math.min(to.y,y+sy); else if(y>to.y)y=Math.max(to.y,y-sy);
    steps.push({x,y});
  }
  return steps;
}

/** Native 0x454B7E mode 1 viewport clamp, expressed in tile units. */
export function clampNativeCamera(target:{x:number;y:number},map:{width:number;height:number},viewport:{width:number;height:number}){
  return {x:Math.max(0,Math.min(target.x,map.width-viewport.width)),y:Math.max(0,Math.min(target.y,map.height-viewport.height))};
}

/** Decode the two bytes read by native 0x403360 from a 0x24-byte actor record. */
export function nativeCameraTargetFromActorRecord(record:Uint8Array|number[]):{x:number;y:number}{
  if(record.length<8)throw new Error('native actor record requires at least 8 bytes');
  return {x:record[6]&0xff,y:record[7]&0xff};
}
