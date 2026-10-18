import {test,expect} from '@playwright/test';

test('battle surface has no development-only navigation/action buttons',async({page})=>{
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForTimeout(1500);
  const surface=await page.evaluate(()=>{
    const scene=new Function('return window.battleGame')().scene.scenes[0];
    return scene.children.list.filter((object:any)=>typeof object.text==='string').map((object:any)=>object.text);
  });
  expect(surface.some((text:string)=>text==='上一关'||text==='下一关'||text==='取消移动'||text==='结束操作')).toBe(false);
});
