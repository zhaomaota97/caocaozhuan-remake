import {test,expect} from '@playwright/test';

test('ending a complete player turn returns control to the next player phase',async({page})=>{
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>new Function('return window.battleGame')()?.scene.scenes[0]?.unitSprites?.length===32);
  await page.evaluate(()=>{
    const scene=new Function('return window.battleGame')().scene.scenes[0];
    scene.finishTurn();
  });
  await expect.poll(()=>page.evaluate(()=>{
    const scene=new Function('return window.battleGame')().scene.scenes[0];
    return {transitioning:scene.turnTransitioning,acted:scene.units.filter((u:any)=>u.side==='player'&&u.hp>0).some((u:any)=>u.acted)};
  }),{timeout:5000}).toEqual({transitioning:false,acted:false});
});
