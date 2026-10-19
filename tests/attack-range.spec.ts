import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {attackRange,inAttackRange} from '../src/rules/attackRange';

test('class and equipment attack ranges match all saved native actors',()=>{
  const read=(path:string)=>JSON.parse(readFileSync(path,'utf8'));
  const fixture=read('data/mappings/slot08-attack-ranges.json');
  const items=read('data/rules/item-categories.json'),classes=read('data/rules/class-attack-ranges.json');
  expect(fixture.rows).toHaveLength(32);
  for(const row of fixture.rows)expect(attackRange({...row,x:0,y:0},items,classes)).toBe(row.nativeRange);
  const shapes=read('data/rules/target-shapes.json').shapes;
  const actor={classId:0,equipmentSlots:[],x:8,y:8};
  expect(inAttackRange(actor,{x:9,y:9},0,shapes)).toBe(false);
  expect(inAttackRange(actor,{x:9,y:9},1,shapes)).toBe(true);
  expect(inAttackRange(actor,{x:9,y:8},0,shapes)).toBe(true);
});

test('range geometry matches all 320 native flag and boundary combinations',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-target-shapes.json','utf8'));
  const shapes=JSON.parse(readFileSync('data/rules/target-shapes.json','utf8')).shapes;
  expect(evidence.rows).toHaveLength(320);
  const failures=[];
  for(const row of evidence.rows){
    const actor={classId:0,equipmentSlots:[],x:row.origin[0],y:row.origin[1]};
    const actual=[];
    for(let index=0;index<640;index++){
      if(inAttackRange(actor,{x:index%20,y:Math.floor(index/20)},row.shape|row.high,shapes,row.flags))actual.push(index);
    }
    if(JSON.stringify(actual)!==JSON.stringify(row.cells))failures.push({origin:row.origin,shape:row.shape,high:row.high,flags:row.flags,actual,expected:row.cells});
  }
  expect(failures).toEqual([]);
  const actor={classId:0,equipmentSlots:[],x:8,y:8};
  expect(inAttackRange(actor,actor,255,shapes,1)).toBe(false);
});
