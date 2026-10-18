import {test,expect} from '@playwright/test';
import items from '../data/rules/item-categories.json';

test('native catalog keeps bean consumable separate from equipment',()=>{
  const bean=(items as Array<any>).find(item=>item.id===87);
  const seal=(items as Array<any>).find(item=>item.id===82);
  expect(bean).toMatchObject({id:87,categoryByte:63,baseValue:30});
  expect(seal).toMatchObject({id:82,categoryByte:41});
});
