import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {selectNativeAiCandidate,collectNativeAdjacentCandidates} from '../src/rules/aiCandidateSelection';

test('ordered candidate selector matches all 6144 native selection records',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-ai-candidate-selection-validation.json','utf8'));
  expect(evidence.rows).toHaveLength(6144);
  const failures=[];
  for(const row of evidence.rows){
    const x=row.input;
    const occupants=evidence.cardinal.map(([dx,dy]:number[],index:number)=>({slot:index+1,groupSlot:x.side_mask&(1<<index)?35:0,hp:x.hp_mask&(1<<index)?1:0,x:x.xy[0]+dx,y:x.xy[1]+dy}));
    const candidates=collectNativeAdjacentCandidates({x:x.xy[0],y:x.xy[1]},x.shape,8,8,0,occupants);
    if(JSON.stringify(candidates)!==JSON.stringify(row.actual.candidates))failures.push({input:x,candidates,native:row.actual.candidates});
    const result=selectNativeAiCandidate(candidates,slot=>row.input.scores[slot-1]);
    if(result.score!==row.actual.score||result.target!==row.actual.target)failures.push({input:row.input,result,native:row.actual});
  }
  expect(failures).toEqual([]);
});

test('diagonal candidates follow native table order after cardinal candidates',()=>{
  const offsets=[[0,-1],[1,0],[0,1],[-1,0],[1,-1],[1,1],[-1,1],[-1,-1]];
  const occupants=offsets.map(([dx,dy],index)=>({slot:index+1,groupSlot:35,hp:1,x:4+dx,y:4+dy}));
  expect(collectNativeAdjacentCandidates({x:4,y:4},1,8,8,0,occupants)).toEqual([1,2,3,4,5,6,7,8]);
});

test('eight-neighbor generation and selection match 216 native diagonal cases',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-ai-diagonal-candidates.json','utf8'));
  expect(evidence.rows).toHaveLength(216);
  expect(evidence.passed).toBe(216);
  const offsets=[...evidence.cardinal,...evidence.diagonal];
  const failures=[];
  for(const row of evidence.rows){
    const x=row.input;
    const occupants=offsets.map(([dx,dy]:number[],index:number)=>({slot:index+1,groupSlot:x.side_mask&(1<<index)?35:0,hp:x.hp_mask&(1<<index)?1:0,x:x.xy[0]+dx,y:x.xy[1]+dy}));
    const candidates=collectNativeAdjacentCandidates({x:x.xy[0],y:x.xy[1]},1,8,8,0,occupants);
    const result=selectNativeAiCandidate(candidates,slot=>x.scores[slot-1]);
    if(JSON.stringify(candidates)!==JSON.stringify(row.actual.candidates)||result.score!==row.actual.score||result.target!==row.actual.target)failures.push({input:x,candidates,result,native:row.actual});
  }
  expect(failures).toEqual([]);
});

test('equal scores keep native input order and zero scores leave no target',()=>{
  expect(selectNativeAiCandidate([3,1,2],()=>10)).toEqual({score:10,target:3});
  expect(selectNativeAiCandidate([3,1,2],()=>256)).toEqual({score:0,target:255});
  expect(selectNativeAiCandidate([3,255,1],slot=>slot===1?255:10)).toEqual({score:10,target:3});
});
