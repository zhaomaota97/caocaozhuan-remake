import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeManualRestoreDispatch} from '../src/rules/manualRestoreDispatch';

test('manual restoration dispatch matches all 48 native stock and success boundaries',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-manual-item-dispatch-inventory.json','utf8'));
  expect(evidence.total).toBe(48);expect(evidence.passed).toBe(48);
  const failures=[];
  for(const row of evidence.rows){
    const actual=nativeManualRestoreDispatch({category:row.category,itemId:87,value:30,targetSelected:row.target!==255,presentationCompleted:row.success,freeUse:row.free!==0,stock:[row.stock],target:{hp:50,maxHp:100,mp:50,maxMp:100}});
    if(actual.hp!==row.hp||actual.mp!==row.mp||Number(actual.completed)!==row.returned||actual.stock[0]!==row.finalStock)failures.push({row,actual});
  }
  expect(failures).toEqual([]);
});
