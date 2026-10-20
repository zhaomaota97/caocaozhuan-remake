import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
test('status icon assets come from exact original MARK offsets',()=>{
  const mapping=JSON.parse(readFileSync('data/mappings/status-icon-art.json','utf8'));
  const manifest=JSON.parse(readFileSync('docs/SOURCE-MIGRATION-MANIFEST.json','utf8'));
  const entry=manifest.entries.find((row:any)=>row.name.toLowerCase()==='mark.e5');
  const raw=readFileSync(entry.destination);
  expect(raw.length).toBe(mapping.sourceBytes);
  for(const icon of mapping.rows)expect(createHash('sha256').update(raw.subarray(icon.offset,icon.offset+256)).digest('hex')).toBe(icon.sha256);
});
test('browser status icons follow native resources and relative phase positions',async({page})=>{
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>(window as any).battleGame?.scene.getScene('default')?.statusText?.active);
  const result=await page.evaluate(()=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    const unit=scene.units.find((row:any)=>row.hp>0&&!row.nativeHidden);
    const sprite=scene.unitSprites.find((row:any)=>row.unit===unit).sprite;
    unit.statusFlags=6;
    const states=[];
    for(const phase of [0,1]){scene.phase=phase;scene.refreshStatusIcon(unit);const icon=scene.statusIcons.get(unit);states.push({key:icon.texture.key,x:icon.x-(sprite.x-24),y:icon.y-(sprite.y-24),visible:icon.visible});}
    unit.statusFlags=0;scene.refreshStatusIcon(unit);
    return {states,cleared:!scene.statusIcons.get(unit).visible};
  });
  expect(result).toEqual({states:[{key:`status-icon-${0x1a3c0}`,x:28,y:0,visible:true},{key:`status-icon-${0x1a4c0}`,x:4,y:0,visible:true}],cleared:true});
});
