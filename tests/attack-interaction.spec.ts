import {test,expect} from '@playwright/test';

test('attack menu executes a strike, plays combat frames/audio and commits HP',async({page})=>{
  const errors:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('response',response=>{if(response.status()>=400)errors.push(`${response.status()} ${response.url()}`);});
  await page.goto('http://127.0.0.1:5173/');
  await page.evaluate(()=>localStorage.clear());
  await page.reload();await page.waitForFunction(()=>new Function('return window.battleGame')()?.scene.scenes[0]?.unitSprites?.length===32);
  const before=await page.evaluate(()=>{
    const scene=new Function('return window.battleGame')().scene.scenes[0];
    const a=scene.units.find((u:any)=>u.id==='unit-0'),d=scene.units.find((u:any)=>u.id==='unit-41');
    d.x=8;d.y=9;scene.unitSprites.find((entry:any)=>entry.unit===d).sprite.setPosition(408,512);
    (window as any).combatSounds=[];const play=scene.sound.play.bind(scene.sound);
    scene.sound.play=(key:string,...args:any[])=>{(window as any).combatSounds.push(key);return play(key,...args);};
    return {hp:d.hp,attackerHp:a.hp};
  });
  const box=(await page.locator('canvas').boundingBox())!;
  const click=async(x:number,y:number,button:'left'|'right'='left')=>page.mouse.click(box.x+x*box.width/960,box.y+y*box.height/640,{button});
  await click(408,464);await click(408,464,'right');await click(440,484);await click(408,512);
  await expect.poll(()=>page.evaluate(()=>new Function('return window.battleGame')().scene.scenes[0].animating)).toBe(true);
  await page.waitForTimeout(250);await page.screenshot({path:'test-results/attack-in-progress.png'});
  await expect.poll(()=>page.evaluate(()=>new Function('return window.battleGame')().scene.scenes[0].animating),{timeout:15000}).toBe(false);
  const after=await page.evaluate(()=>{
    const scene=new Function('return window.battleGame')().scene.scenes[0];
    return {targetHp:scene.units.find((u:any)=>u.id==='unit-41').hp,acted:scene.units.find((u:any)=>u.id==='unit-0').acted,
      strikes:scene.lastExchange,sounds:(window as any).combatSounds};
  });
  expect(after.strikes.length).toBeGreaterThan(0);
  expect(after.targetHp).toBeLessThan(before.hp);
  expect(after.acted).toBe(true);
  expect(after.sounds.some((key:string)=>/^combat-/.test(key))).toBe(true);
  expect(errors).toEqual([]);
  await page.screenshot({path:'test-results/attack-completed.png'});
});
