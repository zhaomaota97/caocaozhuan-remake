import {test,expect} from '@playwright/test';

test('enemy turn does not attack a stale pre-movement target',async({page})=>{
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>(window as any).battleGame?.scene.getScene('default')?.statusText?.active);
  const result=await page.evaluate(async()=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    scene.scene.restart({mapId:31});
    await new Promise(resolve=>setTimeout(resolve,300));
    const enemy=scene.units.find((unit:any)=>unit.side==='enemy'&&unit.hp>0);
    const players=scene.units.filter((unit:any)=>unit.side==='player'&&unit.hp>0);
    const target=players[0];
    enemy.x=0;enemy.y=0;target.x=15;target.y=15;
    for(const unit of players.slice(1)){unit.x=19;unit.y=31;}
    const before=target.hp;
    await scene.runEnemyTurn();
    return {before,after:target.hp,acted:enemy.acted};
  });
  expect(result.acted).toBe(true);
  expect(result.after).toBe(result.before);
});
