import {test,expect} from '@playwright/test';

test('indexed native scenario data loads for S_02',async({page})=>{
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>(window as any).battleGame?.scene.getScene('default')?.statusText?.active);
  await page.evaluate(()=>{const scene=(window as any).battleGame.scene.getScene('default');scene.scene.restart({mapId:2});});
  await expect.poll(()=>page.evaluate(()=>{
    const scene=(window as any).battleGame.scene.getScene('default');return {mapId:scene.mapId,count:scene.units.length,width:scene.map.width,height:scene.map.height,terrain:scene.map.terrain.length};
  })).toEqual({mapId:2,count:33,width:20,height:20,terrain:400});
  expect(errors).toEqual([]);
});
