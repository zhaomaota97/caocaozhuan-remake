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
  expect(actors).toEqual(native.units.filter((unit:any)=>unit.hp>0&&unit.type===2).map((unit:any)=>({slot:unit.slot,level:unit.level})));
  const captured=JSON.parse(readFileSync('data/scenarios/native-units/S_01.json','utf8'));
  const movementStates=await page.evaluate(()=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    return scene.movementActors().map((actor:any)=>({slot:Number(actor.id.split('-slot-')[1]),tier:actor.movementTier,move:actor.move}));
  });
  expect(movementStates).toEqual(captured.units.filter((unit:any)=>unit.hp>0&&unit.type===2).map((unit:any)=>({slot:unit.slot,tier:Buffer.from(unit.actorHex,'hex')[0x1d],move:unit.nativeMove})));
  const liveStats=await page.evaluate(()=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    return scene.units.filter((unit:any)=>unit.hp>0&&!unit.nativeHidden).map((unit:any)=>{
      const actor=scene.combatActor(unit);
      return {slot:Number(unit.id.split('-slot-')[1]),attack:actor.attack,defense:actor.defense,agility:actor.agility,luck:actor.luck};
    });
  });
  expect(liveStats).toEqual(captured.units.filter((unit:any)=>unit.hp>0&&unit.type===2).map((unit:any)=>({slot:unit.slot,...unit.combat})));
  const hidden=await page.evaluate(()=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    return scene.units.filter((unit:any)=>unit.nativeHidden).map((unit:any)=>({slot:Number(unit.id.split('-slot-')[1]),visible:scene.unitSprites.find((entry:any)=>entry.unit===unit).sprite.visible}));
  });
  expect(hidden).toEqual(captured.units.filter((unit:any)=>unit.type===1).map((unit:any)=>({slot:unit.slot,visible:false})));
  const changed=await page.evaluate(()=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    const unit=scene.units.find((row:any)=>row.id==='s01-slot-0');
    const original=unit.nativeEquipment[0].byte1;
    const before=scene.combatActor(unit).attack;
    unit.nativeEquipment[0].byte1=original+1;
    const after=scene.combatActor(unit).attack;
    unit.nativeEquipment[0].byte1=original;
    return {before,after};
  });
  expect(changed.after).toBeGreaterThan(changed.before);
  expect(errors).toEqual([]);
});
