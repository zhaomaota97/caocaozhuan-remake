import {test,expect} from '@playwright/test';
import {nativeAiCandidates,nearestNativeCandidate} from '../src/rules/aiCandidateFilter';

const unit=(id:string,side:'player'|'enemy',x:number,y:number,hp=10,nativeHidden=false)=>({id,name:id,side,x,y,hp,maxHp:hp,move:6,acted:false,nativeHidden});
test('native AI candidate boundary excludes dead hidden out-of-map and allied units',()=>{
  const actor=unit('s01-slot-35','enemy',5,5);
  const units=[actor,unit('s01-slot-0','player',6,5),unit('s01-slot-1','player',30,5),unit('s01-slot-2','player',4,5,0),unit('s01-slot-3','player',7,5,10,true),unit('s01-slot-36','enemy',4,5)];
  expect(nativeAiCandidates(actor,units,20,20).map(row=>row.id)).toEqual(['s01-slot-0']);
  expect(nearestNativeCandidate(actor,units,20,20)?.id).toBe('s01-slot-0');
});
