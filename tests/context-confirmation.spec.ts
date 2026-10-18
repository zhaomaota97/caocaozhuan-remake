import {test,expect} from '@playwright/test';

test('blank and completed-unit context actions open confirmation/info modals',async({page})=>{
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>new Function('return window.battleGame')()?.scene.scenes[0]?.unitSprites?.length===32);
  const state=await page.evaluate(()=>{
    const scene=new Function('return window.battleGame')().scene.scenes[0];
    scene.openEndTurnConfirm();
    const confirm=Boolean(scene.modal);
    scene.modal.destroy();scene.modal=undefined;
    const unit=scene.units.find((u:any)=>u.side==='player'&&u.hp>0&&!u.acted);
    unit.acted=true;scene.openContextMenu(unit,200,120);
    return {confirm,info:Boolean(scene.modal)};
  });
  expect(state).toEqual({confirm:true,info:true});
});
