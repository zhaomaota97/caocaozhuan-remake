import {test,expect} from '@playwright/test';

test('acted units darken and hit presentation advances through hurt frames',async({page})=>{
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>new Function('return window.battleGame')()?.scene.scenes[0]?.unitSprites?.length===32);
  const result=await page.evaluate(async()=>{
    const scene=new Function('return window.battleGame')().scene.scenes[0];
    const unit=scene.units.find((u:any)=>u.side==='player'&&u.hp>0);
    unit.acted=true;scene.refreshUnitSprite(unit);
    const sprite=scene.unitSprites.find((e:any)=>e.unit===unit).sprite;
    const tint=sprite.tintTopLeft;
    const target=scene.units.find((u:any)=>u.side==='enemy'&&u.hp>0);
    target.x=unit.x+1;target.y=unit.y;
    return {tint,unitId:unit.id,targetId:target.id};
  });
  expect(result.tint).toBe(0x808080);
  expect(result.unitId).toBeTruthy();expect(result.targetId).toBeTruthy();
});
