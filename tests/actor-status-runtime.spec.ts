import {test,expect} from '@playwright/test';
test('native status phase switches cached textures and composes with acted appearance',async({page})=>{
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>(window as any).battleGame?.scene.getScene('default')?.statusText?.active);
  const result=await page.evaluate(()=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    const unit=scene.units.find((row:any)=>row.hp>0&&!row.nativeHidden);
    const sprite=scene.unitSprites.find((row:any)=>row.unit===unit).sprite;
    unit.statusFlags=16;unit.acted=false;unit.actorFlags=0;scene.phase=2;scene.refreshUnitSprite(unit);
    const status=sprite.texture.key;
    const canvas=sprite.texture.getSourceImage() as HTMLCanvasElement;
    const pixels=canvas.getContext('2d')!.getImageData(0,0,528,48).data;
    const nonblank=pixels.some((value,index)=>index%4===3&&value!==0);
    unit.acted=true;scene.refreshUnitSprite(unit);const combined=sprite.texture.key;
    scene.phase=0;scene.refreshUnitSprite(unit);const acted=sprite.texture.key;
    unit.acted=false;scene.refreshUnitSprite(unit);const normal=sprite.texture.key;
    return {status,combined,acted,normal,nonblank,tint:sprite.tintTopLeft};
  });
  expect(result.status).toMatch(/^mov-status-.*-0$/);expect(result.combined).toMatch(/^mov-status-.*-1$/);
  expect(result.acted).toMatch(/^mov-acted-/);expect(result.normal).toMatch(/^mov-\d+$/);
  expect(result.nonblank).toBe(true);expect(result.tint).toBe(0xffffff);
});
