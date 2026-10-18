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
