import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeEquipmentAttribute} from '../src/rules/equipmentAttribute';

test('equipment contribution matches all 104 original items at ten level boundaries',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-equipment-attribute.json','utf8'));
  expect(evidence.passed).toBe(true);
  expect(evidence.definitions).toHaveLength(104);
  expect(evidence.rows).toHaveLength(1040);
  expect(evidence.rows.filter((row:{id:number;level:number;result:number})=>nativeEquipmentAttribute(evidence.definitions[row.id],row.level)!==row.result)).toEqual([]);
});
