import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('all 104 item sprites decode in browser at native dimensions with visible pixels',async({page})=>{
  const mapping=JSON.parse(readFileSync('data/mappings/battle-item-art.json','utf8'));
  expect(mapping.rows).toHaveLength(104);
  await page.goto('http://127.0.0.1:5173/');
  const failures=await page.evaluate(async(rows:Array<{url:string;rgbaSha256:string}>)=>{
    const failures=[];
    for(const row of rows){
      const image=new Image();image.src=row.url;await image.decode();
      const canvas=document.createElement('canvas');canvas.width=32;canvas.height=32;
      const context=canvas.getContext('2d')!;context.drawImage(image,0,0);
      const pixels=context.getImageData(0,0,32,32).data;
      if(image.naturalWidth!==32||image.naturalHeight!==32||!pixels.some((value,index)=>index%4===3&&value===255))failures.push(row.url);
    }
    return failures;
  },mapping.rows);
  expect(failures).toEqual([]);
});
