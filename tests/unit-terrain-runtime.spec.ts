import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
test('browser idle terrain clipping matches raw masks for normal and mirrored banks',async({page})=>{
  const palette=JSON.parse(readFileSync('data/mappings/scene-palettes.json','utf8')).scenes['0'];
  const mask=JSON.parse(readFileSync('data/mappings/unit-terrain-masks.json','utf8')).rows.find((row:any)=>row.size===48&&row.terrain===1).blocked;
  const raw=readFileSync('public/assets/native-extracted/Unit_mov/resource_0108.bin');
  const expected=[false,true].map(mirror=>{
    const bytes=Buffer.alloc(528*48*4);
    for(let frame=0;frame<11;frame++)for(let y=0;y<48;y++)for(let x=0;x<48;x++){
      const color=raw[frame*2304+y*48+x],mx=mirror&&[4,5,8].includes(frame)?47-x:x;
      if(!color||mask[y*48+mx])continue;
      const at=(y*528+frame*48+x)*4;
      bytes[at]=palette[color*3+1]*16;bytes[at+1]=palette[color*3+2]*16;bytes[at+2]=palette[color*3]*16;bytes[at+3]=255;
    }
    return createHash('sha256').update(bytes).digest('hex');
  });
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>(window as any).battleGame?.scene.getScene('default')?.statusText?.active);
  const actual=await page.evaluate(async()=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    const unit=scene.units.find((row:any)=>row.hp>0&&!row.nativeHidden);unit.art=108;unit.statusFlags=0;unit.acted=false;unit.actorFlags=0;
    scene.map.terrain[unit.y*scene.map.width+unit.x]=1;
    const hashes=[];
    for(const mirror of [false,true]){
      unit.mirror=mirror;scene.refreshUnitSprite(unit);
      const sprite=scene.unitSprites.find((row:any)=>row.unit===unit).sprite;
      const canvas=sprite.texture.getSourceImage() as HTMLCanvasElement;
      const bytes=canvas.getContext('2d')!.getImageData(0,0,528,48).data;
      hashes.push([...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(value=>value.toString(16).padStart(2,'0')).join(''));
    }
    return hashes;
  });
  expect(actual).toEqual(expected);
});
