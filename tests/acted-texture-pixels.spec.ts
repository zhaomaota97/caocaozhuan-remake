import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {buildNativePaletteLookup} from '../src/rules/nativePaletteLookup';
import {nativeDarkenedPixel} from '../src/rules/actedDarkening';

test('browser acted sheet pixels match reconstructed original indexed transform',async({page})=>{
  const mapping=JSON.parse(readFileSync('data/mappings/acted-movement-art.json','utf8'));
  const native=JSON.parse(readFileSync('docs/reverse-engineering/native-palette-lookup-corpus.json','utf8'));
  const palette=native.rows.find((row:any)=>row.name==='Spalet:0').palette;
  const lookup=[...buildNativePaletteLookup(palette)],art=108;
  const source=readFileSync(`public/assets/native-extracted/Unit_mov/resource_${String(art).padStart(4,'0')}.bin`);
  const expected=Buffer.alloc(528*48*4);
  for(let frame=0;frame<11;frame++)for(let y=0;y<48;y++)for(let x=0;x<48;x++){
    const index=nativeDarkenedPixel(source[frame*2304+y*48+x],4,palette,lookup);
    const offset=(y*528+frame*48+x)*4;
    if(index!==0){expected[offset]=palette[index*3+1]*16;expected[offset+1]=palette[index*3+2]*16;expected[offset+2]=palette[index*3]*16;expected[offset+3]=255;}
  }
  const asset=mapping.banks.find((row:any)=>row.profile===mapping.scenes['0']).assets.find((row:any)=>row.art===art);
  await page.goto('http://127.0.0.1:5173/');
  const hash=await page.evaluate(async(url:string)=>{
    const image=new Image();image.src=url;await image.decode();
    const canvas=document.createElement('canvas');canvas.width=528;canvas.height=48;
    const context=canvas.getContext('2d')!;context.drawImage(image,0,0);
    const bytes=context.getImageData(0,0,528,48).data;
    return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(value=>value.toString(16).padStart(2,'0')).join('');
  },asset.url);
  expect(hash).toBe(createHash('sha256').update(expected).digest('hex'));
});
