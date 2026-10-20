import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('all 302 migrated combat sheets are loaded with native dimensions and frames',async({page})=>{
  const sheets=JSON.parse(readFileSync('data/mappings/combat-sheets-map31.json','utf8'));
  expect(sheets).toHaveLength(302);
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>(window as any).battleGame?.scene.getScene('default')?.statusText?.active);
  const failures=await page.evaluate((sheets:Array<{family:string;index:number;tileSize:number;frames:number}>)=>{
    const scene=(window as any).battleGame.scene.getScene('default'),failures=[];
    for(const sheet of sheets){
      const key=`${sheet.family}-${sheet.index}`;
      if(!scene.textures.exists(key)){failures.push(`${key}:missing`);continue;}
      const texture=scene.textures.get(key);
      for(let frame=0;frame<sheet.frames;frame++){
        if(!texture.has(frame)){failures.push(`${key}:${frame}:missing`);continue;}
        const image=texture.get(frame);
        if(image.width!==sheet.tileSize||image.height!==sheet.tileSize)failures.push(`${key}:${frame}:size`);
      }
    }
    return failures;
  },sheets);
  expect(failures).toEqual([]);expect(errors).toEqual([]);
});
