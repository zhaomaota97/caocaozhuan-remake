import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {runNativeExperienceItem} from '../src/rules/experienceItemController';

test('XP item orchestration matches all 72 native traces and resource outcomes',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-experience-item-controller.json','utf8'));
  expect(evidence.total).toBe(72);expect(evidence.passed).toBe(72);
  const failures=[];
  for(const row of evidence.rows){
    const trace:unknown[]=[];let grown=false;
    const actual=runNativeExperienceItem({targetSelected:row.selected!==255,level:row.level,experience:row.xp,value:row.value,hp:10,mp:5},{
      present:()=>{trace.push({kind:'presentation'});},
      grow:(total,display)=>{trace.push({kind:'growth',total,display});grown=true;},
      maximumHp:()=>grown?120:100,maximumMp:()=>grown?60:50,
    });
    if(actual.hp!==row.hp||actual.mp!==row.mp||JSON.stringify(trace)!==JSON.stringify(row.trace))failures.push({row,actual,trace});
  }
  expect(failures).toEqual([]);
});
