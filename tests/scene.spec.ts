import { test, expect } from '@playwright/test';

test('saved battlefield renders without browser errors and idle pixels change', async ({ page }) => {
  const errors: string[] = [];
  const audioRequests: string[] = [];
  page.on('request',request=>{if(request.url().includes('/audio/bgm/'))audioRequests.push(decodeURIComponent(request.url()));});
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:5173/');
  await expect(page.locator('canvas')).toBeVisible();
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'test-results/slot08-desktop.png' });
  expect(errors).toEqual([]);
  expect(audioRequests.some(url=>url.endsWith('/05-AudioTrack 05.mp3'))).toBe(true);
  const first = await page.locator('canvas').screenshot();
  let changed = false;
  for(let i=0;i<12;i++){
    await page.waitForTimeout(100);
    const current=await page.locator('canvas').screenshot();
    if(!first.equals(current)){changed=true;break;}
  }
  expect(changed).toBe(true);
  const canvas=page.locator('canvas');
  const box=await canvas.boundingBox();
  expect(box).not.toBeNull();
  const header={x:box!.x,y:box!.y,width:box!.width,height:Math.floor(box!.width*56/960)};
  const before=await page.screenshot({clip:header});
  await page.mouse.move(box!.x+box!.width/2,box!.y+box!.height/2);
  await page.mouse.wheel(0,900);
  await page.waitForTimeout(200);
  const after=await page.screenshot({clip:header});
  expect(before.equals(after)).toBe(true);
  await page.screenshot({path:'test-results/slot08-enemy-viewport.png'});
});

