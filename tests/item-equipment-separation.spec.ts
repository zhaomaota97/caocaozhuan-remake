import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('native catalog keeps bean consumable separate from equipment',()=>{
  const items=JSON.parse(readFileSync('data/rules/item-categories.json','utf8').replace(/^\uFEFF/,'')) as Array<any>;
  const bean=items.find(item=>item.id===87);
  const seal=items.find(item=>item.id===82);
  expect(bean).toMatchObject({id:87,categoryByte:63,baseValue:30});
  expect(seal).toMatchObject({id:82,categoryByte:41});
});
