import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('S_01 native unit dataset enters the battle scene',async({page})=>{
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>(window as any).battleGame?.scene.getScene('default')?.statusText?.active);
  await page.evaluate(()=>{const scene=(window as any).battleGame.scene.getScene('default');scene.scene.restart({mapId:1});});
  await expect.poll(()=>page.evaluate(()=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    return {mapId:scene.mapId,count:scene.units.length,first:scene.units[0]&&{x:scene.units[0].x,y:scene.units[0].y,hp:scene.units[0].hp}};
  })).toEqual({mapId:1,count:29,first:{x:19,y:9,hp:102}});
  const native=JSON.parse(readFileSync('data/scenarios/S_01-units-native.json','utf8'));
  const actors=await page.evaluate(()=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    return scene.units.filter((unit:any)=>unit.hp>0&&!unit.nativeHidden).map((unit:any)=>({slot:Number(unit.id.split('-slot-')[1]),level:scene.combatActor(unit).nativeLevel}));
  });
  expect(actors.length).toBeGreaterThan(0);
  expect(actors).toEqual(native.units.filter((unit:any)=>unit.hp>0).map((unit:any)=>({slot:unit.slot,level:unit.level})));
  const captured=JSON.parse(readFileSync('data/scenarios/native-units/S_01.json','utf8'));
  const liveStats=await page.evaluate(()=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    return scene.units.filter((unit:any)=>unit.hp>0&&!unit.nativeHidden).map((unit:any)=>{
      const actor=scene.combatActor(unit);
      return {slot:Number(unit.id.split('-slot-')[1]),attack:actor.attack,defense:actor.defense,agility:actor.agility,luck:actor.luck};
    });
  });
  expect(liveStats).toEqual(captured.units.filter((unit:any)=>unit.hp>0).map((unit:any)=>({slot:unit.slot,...unit.combat})));
  expect(errors).toEqual([]);
});
