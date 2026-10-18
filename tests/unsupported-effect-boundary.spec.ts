import {test,expect} from '@playwright/test';

test('strategy and item target selection does not invent unverified result mutations',async({page})=>{
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>new Function('return window.battleGame')()?.scene.scenes[0]?.unitSprites?.length===32);
  const result=await page.evaluate(()=>{
    const scene=new Function('return window.battleGame')().scene.scenes[0];
    const source=scene.units.find((u:any)=>u.side==='player'&&u.hp>0&&!u.acted);
    const target=scene.units.find((u:any)=>u.side==='enemy'&&u.hp>0);
    const before={hp:target.hp,mp:target.mp,status:target.statusFlags,acted:source.acted};
    scene.selected=source;scene.beginUtilitySelection('strategy');
    scene.showActionNotice('test');
    const after={hp:target.hp,mp:target.mp,status:target.statusFlags,acted:source.acted,mode:scene.actionMode};
    return {before,after};
  });
  expect(result.after).toEqual({...result.before,mode:'strategy'});
});
