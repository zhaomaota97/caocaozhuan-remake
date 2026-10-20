import {test,expect} from '@playwright/test';

test('manual item preview uses native adjacent-plus-origin range and allied targets',async({page})=>{
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>(window as any).battleGame?.scene.getScene('default')?.statusText?.active);
  await page.evaluate(()=>{(window as any).battleGame.scene.getScene('default').scene.restart({mapId:1});});
  await page.waitForFunction(()=>(window as any).battleGame.scene.getScene('default').units[0]?.id?.startsWith('s01-'));
  const result=await page.evaluate(()=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    const actor=scene.units.find((unit:any)=>unit.side==='player'&&unit.hp>0);
    scene.consumableStock=Array(17).fill(0);scene.consumableStock[0]=1;
    actor.x=5;actor.y=5;actor.nativeHidden=false;
    scene.selected=actor;scene.actionMode='item';scene.selectedItemId=87;scene.showStrategyReach();
    const count=[...scene.cells.values()].filter((cell:any)=>cell.fillAlpha===0.35).length;
    const notices:string[]=[];scene.showActionNotice=(text:string)=>notices.push(text);
    scene.previewVerifiedItem({...actor,id:'far',x:7,y:5});
    scene.previewVerifiedItem({...actor,id:'enemy',side:'enemy',x:6,y:5});
    const rejected=notices.length===0;
    scene.previewVerifiedItem(actor);
    return {count,rejected,selfAccepted:notices.length===1};
  });
  expect(result).toEqual({count:9,rejected:true,selfAccepted:true});
});
