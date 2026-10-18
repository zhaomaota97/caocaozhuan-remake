import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {movementPath,movementFrames,directions} from '../src/rules/movementPath';

test('all 636 native animation samples match runtime frames and positions',()=>{
  const fixture=JSON.parse(readFileSync('tests/fixtures/native-movement-animation.json','utf8'));
  expect(fixture.rows).toHaveLength(636);
  for(const row of fixture.rows){
    const [dx,dy]=directions[row.direction];
    const samples=movementFrames(row.classId,row.direction,row.setting);
    expect(samples.map(sample=>({x:384+dx*sample.progress,y:440+dy*sample.progress,
      frameOffset:sample.frame*2304}))).toEqual(row.draws.map((draw:{x:number;y:number;frameOffset:number})=>({
        x:draw.x,y:draw.y,frameOffset:draw.frameOffset})));
  }
});

test('movement paths match all 933 native direction sequences',()=>{
  const fixture=JSON.parse(readFileSync('tests/fixtures/native-movement-paths.json','utf8'));
  const save=JSON.parse(readFileSync('data/saves/slot-08.json','utf8'));
  const items=JSON.parse(readFileSync('data/rules/item-categories.json','utf8'));
  for(const row of fixture.rows){
    const actor=save.actors.find((actor:{id:string})=>actor.id===`unit-${row.slot}`);
    expect(movementPath(save.width,save.height,actor.nativeMovementCosts,save.actors,actor,
      row.target[0],row.target[1],items),JSON.stringify(row)).toEqual(row.directions);
  }
});

test('mouse movement renders intermediate frames and plays terrain footsteps',async({page})=>{
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForTimeout(2500);
  expect(await page.locator('canvas').evaluate(canvas=>{
    const event=new MouseEvent('contextmenu',{bubbles:true,cancelable:true,button:2});
    canvas.dispatchEvent(event);return event.defaultPrevented;
  })).toBe(true);
  const inspect=()=>page.evaluate(async()=>{
    const game=new Function('return window.battleGame')();
    const scene=game.scene.scenes[0];
    const unit=scene.units.find((u:{id:string})=>u.id==='unit-3');
    const sprite=scene.unitSprites.find((entry:{unit:{id:string}})=>entry.unit.id===unit.id).sprite;
    return {x:unit.x,y:unit.y,spriteX:sprite.x,spriteY:sprite.y,frame:sprite.frame.name,animating:scene.animating,moving:scene.moving,
      menu:scene.contextMenu?.list.filter((object:{text?:string})=>object.text).map((object:{text:string})=>object.text)??[]};
  });
  await page.evaluate(async()=>{
    localStorage.clear();
    const game=new Function('return window.battleGame')();
    const scene=game.scene.scenes[0];
    (window as unknown as {steps:string[]}).steps=[];
    const original=scene.sound.play.bind(scene.sound);
    scene.sound.play=(key:string,...args:unknown[])=>{
      (window as unknown as {steps:string[]}).steps.push(key);return original(key,...args);
    };
  });
  const before=await inspect();
  const box=(await page.locator('canvas').boundingBox())!;
  const click=async(x:number,y:number)=>page.mouse.click(box.x+x*box.width/960,box.y+y*box.height/640);
  await click(before.x*48+24,56+before.y*48+24);
  await click(before.x*48+24,56+(before.y-1)*48+24);
  await page.waitForTimeout(35);
  const during=await inspect();
  expect(during.animating).toBe(true);
  expect(during.spriteY).toBeLessThan(before.spriteY);
  expect(during.spriteY).toBeGreaterThan(before.spriteY-48);
  await expect.poll(async()=> (await inspect()).animating).toBe(false);
  expect((await inspect()).y).toBe(before.y-1);
  expect((await inspect()).menu).toEqual(['攻击','策略','道具','待命','取消']);
  const steps=await page.evaluate(()=>(window as unknown as {steps:string[]}).steps);
  expect(steps.some(key=>/^step-2[3-9]$/.test(key))).toBe(true);
  const menuPosition=await page.evaluate(()=>{
    const scene=new Function('return window.battleGame')().scene.scenes[0];
    return {x:scene.contextMenu.x,y:scene.contextMenu.y};
  });
  await click(menuPosition.x+35,menuPosition.y+20);
  const selection=await page.evaluate(()=>{
    const scene=new Function('return window.battleGame')().scene.scenes[0];
    return {mode:scene.actionMode,menu:!!scene.contextMenu,
      highlighted:[...scene.cells.values()].filter((cell:any)=>cell.fillColor===0xc45442&&cell.fillAlpha>0).length};
  });
  expect(selection).toMatchObject({mode:'attack',menu:false});
  expect(selection.highlighted).toBeGreaterThan(0);
  await page.mouse.click(box.x+400*box.width/960,box.y+300*box.height/640,{button:'right'});
  expect((await inspect()).y).toBe(before.y-1);
  expect((await inspect()).menu).toEqual(['攻击','策略','道具','待命','取消']);
  await page.screenshot({path:'test-results/movement-completed.png'});
  await click(435,300+140);
  expect((await inspect()).y).toBe(before.y);
  expect((await inspect()).menu).toEqual([]);
});
