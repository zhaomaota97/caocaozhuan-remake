import type { Unit } from '../model/battle';
const key='caocaozhuan-remake-slot08-native-v2';
let currentRngState=0;
export function loadRngState():number{
  try{const state=JSON.parse(localStorage.getItem(key)??'null');return state?.version===2&&state.slot===8&&Number.isInteger(state.rngState)?state.rngState>>>0:0;}catch{return 0;}
}
export function setRngState(state:number){currentRngState=state>>>0;}
export function saveUnits(units: Unit[]): void {
  if (!units.length) return;
  localStorage.setItem(key, JSON.stringify({version:2,slot:8,units,rngState:currentRngState}));
}

export function restoreUnits(raw: string | null, baseline: Unit[]): Unit[] {
  if (!raw) return baseline;
  try {
    const saved=JSON.parse(raw);
    if(saved.version!==2 || saved.slot!==8 || !Array.isArray(saved.units) || saved.units.length!==baseline.length) return baseline;
    const records=new Map<string,Unit>();
    for(const unit of saved.units){
      if(!unit || typeof unit.id!=='string' || records.has(unit.id)) return baseline;
      records.set(unit.id,unit);
    }
    const restored: Unit[]=[];
    for(const original of baseline){
      const unit=records.get(original.id);
      if(!unit || unit.art!==original.art || unit.side!==original.side) return baseline;
      if(!Number.isInteger(unit.x) || unit.x<0 || unit.x>=20) return baseline;
      if(!Number.isInteger(unit.y) || unit.y<0 || unit.y>=32) return baseline;
      if(!Number.isInteger(unit.hp) || unit.hp<0 || unit.hp>original.maxHp || typeof unit.acted!=='boolean') return baseline;
      // Verified identities and actor fields always come from the exported native save.
      const mp=Number.isInteger(unit.mp)&&unit.mp!>=0&&unit.mp!<=(original.mp??0)?unit.mp:original.mp;
      const statusFlags=Number.isInteger(unit.statusFlags)&&unit.statusFlags!>=0&&unit.statusFlags!<=255?unit.statusFlags:original.statusFlags;
      const actorFlags=Number.isInteger(unit.actorFlags)&&unit.actorFlags!>=0&&unit.actorFlags!<=255?unit.actorFlags:original.actorFlags;
      const direction=Number.isInteger(unit.direction)&&unit.direction!>=0&&unit.direction!<=3?unit.direction:original.direction;
      restored.push({...original,x:unit.x,y:unit.y,hp:unit.hp,mp,statusFlags,actorFlags,direction,mirror:direction===1?true:direction===3?false:original.mirror,acted:unit.acted});
    }
    return restored;
  } catch { return baseline; }
}

export function loadUnits(baseline: Unit[]): Unit[] {
  try { return restoreUnits(localStorage.getItem(key),baseline); }
  catch { return baseline; }
}
