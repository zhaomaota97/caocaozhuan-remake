import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {selectNativeAiCandidate} from '../src/rules/aiCandidateSelection';

test('ordered candidate selector matches all 6144 native selection records',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-ai-candidate-selection-validation.json','utf8'));
  expect(evidence.rows).toHaveLength(6144);
  const failures=[];
  for(const row of evidence.rows){
    const result=selectNativeAiCandidate(row.actual.candidates,slot=>row.input.scores[slot-1]);
    if(result.score!==row.actual.score||result.target!==row.actual.target)failures.push({input:row.input,result,native:row.actual});
  }
  expect(failures).toEqual([]);
});

test('equal scores keep native input order and zero scores leave no target',()=>{
  expect(selectNativeAiCandidate([3,1,2],()=>10)).toEqual({score:10,target:3});
  expect(selectNativeAiCandidate([3,1,2],()=>256)).toEqual({score:0,target:255});
  expect(selectNativeAiCandidate([3,255,1],slot=>slot===1?255:10)).toEqual({score:10,target:3});
});
