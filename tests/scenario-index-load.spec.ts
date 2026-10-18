import {test,expect} from '@playwright/test';

test('indexed native scenario data loads for S_02',async({page})=>{
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto('http://127.0.0.1:5173/');
  await page.evaluate(()=>{const scene=(window as any).battleGame.scene.getScene('default');scene.scene.restart({mapId:2});});
  await expect.poll(()=>page.evaluate(()=>{
    const scene=(window as any).battleGame.scene.getScene('default');return {mapId:scene.mapId,count:scene.units.length};
  })).toEqual({mapId:2,count:33});
  expect(errors).toEqual([]);
});
