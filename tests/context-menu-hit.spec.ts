import {test,expect} from '@playwright/test';

test('native context menu buttons hit consistently at screen edges and after scroll',async({page})=>{
  const canvas=page.locator('canvas');
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>new Function('return window.battleGame')()?.scene.scenes[0]?.unitSprites?.length===32);
  const box=(await canvas.boundingBox())!;
  const open=async(x:number,y:number)=>page.evaluate(({x,y})=>{
    const scene=new Function('return window.battleGame')().scene.scenes[0];
    const unit=scene.units.find((candidate:any)=>candidate.side==='player'&&!candidate.acted);
    scene.openContextMenu(unit,x,y);
    return {x:scene.contextMenu.x,y:scene.contextMenu.y};
  },{x,y});
  const clickScene=async(x:number,y:number,button:'left'|'right'='left')=>
    page.mouse.click(box.x+x*box.width/960,box.y+y*box.height/640,{button});
  for(const point of [[8,70],[820,70],[820,470],[8,470]] as const){
    const menu=await open(...point);
    expect(menu.x).toBeGreaterThanOrEqual(0);
    expect(menu.y).toBeGreaterThanOrEqual(0);
    const attack=await page.evaluate(()=>{
      const scene=new Function('return window.battleGame')().scene.scenes[0];
      return Boolean(scene.contextMenu.list.find((object:any)=>object.getData?.('controlId')===1287));
    });
    expect(attack).toBeTruthy();
    await page.screenshot({path:`test-results/context-menu-${point[0]}-${point[1]}.png`});
    await clickScene(menu.x+55,menu.y+15);
    await expect.poll(()=>page.evaluate(()=>new Function('return window.battleGame')().scene.scenes[0].actionMode)).toBe('attack');
    await page.evaluate(()=>new Function('return window.battleGame')().scene.scenes[0].actionMode=undefined);
  }
  await page.mouse.move(box.x+300,box.y+300);await page.mouse.wheel(0,300);
  const visibleUnit=await page.evaluate(()=>{
    const scene=new Function('return window.battleGame')().scene.scenes[0];
    const unit=scene.units.find((candidate:any)=>candidate.side==='player'&&!candidate.acted&&candidate.hp>0&&
      56+candidate.y*48+24-scene.cameras.main.scrollY>56&&56+candidate.y*48+24-scene.cameras.main.scrollY<640);
    return {x:unit.x*48+24,y:56+unit.y*48+24-scene.cameras.main.scrollY};
  });
  await clickScene(visibleUnit.x,visibleUnit.y,'right');
  await expect.poll(()=>page.evaluate(()=>Boolean(new Function('return window.battleGame')().scene.scenes[0].contextMenu))).toBe(true);
  await page.evaluate(()=>new Function('return window.battleGame')().scene.scenes[0].closeContextMenu());
  const scrolled=await open(820,470);
  expect(scrolled.x).toBeGreaterThanOrEqual(0);expect(scrolled.y).toBeGreaterThanOrEqual(0);
  await clickScene(scrolled.x+55,scrolled.y+15);
  await expect.poll(()=>page.evaluate(()=>new Function('return window.battleGame')().scene.scenes[0].actionMode)).toBe('attack');
});
