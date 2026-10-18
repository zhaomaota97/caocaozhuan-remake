import {test,expect} from '@playwright/test';

test('S_01 native unit dataset enters the battle scene',async({page})=>{
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto('http://127.0.0.1:5173/');
  await page.evaluate(()=>{const scene=(window as any).battleGame.scene.getScene('default');scene.scene.restart({mapId:1});});
  await expect.poll(()=>page.evaluate(()=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    return {mapId:scene.mapId,count:scene.units.length,first:scene.units[0]&&{x:scene.units[0].x,y:scene.units[0].y,hp:scene.units[0].hp}};
  })).toEqual({mapId:1,count:29,first:{x:19,y:9,hp:102}});
  expect(errors).toEqual([]);
});
