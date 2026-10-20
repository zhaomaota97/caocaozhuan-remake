import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('scenario strategy menu uses native actor level rather than level one',async({page})=>{
  const learning=JSON.parse(readFileSync('data/mappings/effect-learning-runtime.json','utf8').replace(/^\uFEFF/,''));
  const source=JSON.parse(readFileSync('data/scenarios/S_01-units-native.json','utf8'));
  const learned=(unit:any)=>learning.filter((row:any)=>Number(row.class_id)===unit.classId&&Number(row.required_level)<=unit.level&&row.learnable==='True');
  const unit=source.units.find((row:any)=>row.slot<35&&row.hp>0&&row.level>1&&learned(row).some((spell:any)=>Number(spell.required_level)>1));
  expect(unit,'S_01 fixture must exercise learning above level one').toBeTruthy();
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>(window as any).battleGame?.scene.getScene('default')?.statusText?.active);
  await page.evaluate(()=>{(window as any).battleGame.scene.getScene('default').scene.restart({mapId:1});});
  await page.waitForFunction(()=>(window as any).battleGame.scene.getScene('default').units[0]?.id?.startsWith('s01-'));
  const actual=await page.evaluate((slot:number)=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    scene.selected=scene.units.find((row:any)=>row.id===`s01-slot-${slot}`);
    scene.beginUtilitySelection('strategy');
    return scene.utilityMenu?.list.filter((row:any)=>row.type==='Text'&&row.getData('controlId')!==undefined).map((row:any)=>row.text)??[];
  },unit.slot);
  expect(actual).toEqual(learned(unit).slice(0,8).map((row:any)=>row.name_gbk));
});
