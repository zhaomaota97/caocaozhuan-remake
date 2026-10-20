import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeConsumableCount} from '../src/rules/consumableInventory';

test('ten native saved inventory exports preserve all 170 stock bytes',()=>{
  const evidence=JSON.parse(readFileSync('data/saves/consumable-stock.json','utf8'));
  const manifest=JSON.parse(readFileSync('docs/SOURCE-MIGRATION-MANIFEST.json','utf8'));
  expect(evidence.rows).toHaveLength(10);
  for(const row of evidence.rows){
    const entry=manifest.entries.find((item:any)=>item.name.toLowerCase()===row.file.toLowerCase());
    const raw=readFileSync(entry.destination);
    expect(row.nativeConsumed).toBe(654);expect(row.stock).toHaveLength(17);
    expect(row.stock).toEqual([...raw.subarray(evidence.stockFileOffset,evidence.stockFileOffset+17)]);
    for(let id=87;id<=103;id++)expect(nativeConsumableCount(row.stock,id)).toBe(raw[evidence.stockFileOffset+id-87]);
  }
});

test('slot08 item menu lists actual nonzero native stock only',async({page})=>{
  const evidence=JSON.parse(readFileSync('data/saves/consumable-stock.json','utf8'));
  const stock=evidence.rows.find((row:any)=>row.slot===8).stock;
  await page.goto('http://127.0.0.1:5173/');
  await page.waitForFunction(()=>(window as any).battleGame?.scene.getScene('default')?.statusText?.active);
  await page.evaluate(()=>{(window as any).battleGame.scene.getScene('default').scene.restart({mapId:31});});
  await page.waitForFunction(()=>(window as any).battleGame.scene.getScene('default').units[0]?.id?.startsWith('unit-'));
  const actual=await page.evaluate(()=>{
    const scene=(window as any).battleGame.scene.getScene('default');
    scene.selected=scene.units.find((unit:any)=>unit.side==='player'&&unit.hp>0);
    scene.beginUtilitySelection('item');
    return {stock:scene.consumableStock,ids:scene.utilityMenu.list.filter((row:any)=>row.type==='Text'&&row.getData('controlId')!==undefined).map((row:any)=>row.getData('controlId'))};
  });
  expect(actual.stock).toEqual(stock);
  expect(actual.ids).toEqual(stock.flatMap((count:number,index:number)=>count>0?[87+index]:[]));
});
