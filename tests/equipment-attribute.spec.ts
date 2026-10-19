import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeEquipmentAttribute,nativeEquipmentAttributeTotal} from '../src/rules/equipmentAttribute';
import {nativeBattleAttributes} from '../src/rules/battleAttributes';

test('equipment contribution matches all 104 original items at ten level boundaries',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-equipment-attribute.json','utf8'));
  expect(evidence.passed).toBe(true);
  expect(evidence.definitions).toHaveLength(104);
  expect(evidence.rows).toHaveLength(1040);
  expect(evidence.rows.filter((row:{id:number;level:number;result:number})=>nativeEquipmentAttribute(evidence.definitions[row.id],row.level)!==row.result)).toEqual([]);
});

test('complete slot accumulator matches 23400 native attribute comparisons',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-equipment-accumulator.json','utf8'));
  expect(evidence.rows).toHaveLength(2600);
  const failures=[];
  for(const row of evidence.rows){
    const slots=row.ids.map((itemId:number,slot:number)=>({slot,itemId,byte1:row.level}));
    const actual=Array.from({length:9},(_,attribute)=>nativeEquipmentAttributeTotal(slots,evidence.definitions,attribute));
    if(JSON.stringify(actual)!==JSON.stringify(row.values))failures.push({row,actual});
  }
  expect(failures).toEqual([]);
});

test('recalculated battle attributes match native getters across all 58 scenarios',()=>{
  const equipment=JSON.parse(readFileSync('data/rules/native-equipment-attributes.json','utf8'));
  const failures=[];
  for(let id=0;id<58;id++){
    const source=JSON.parse(readFileSync(`data/scenarios/native-units/S_${String(id).padStart(2,'0')}.json`,'utf8'));
    for(const unit of source.units){
      const unitBytes=Buffer.from(unit.unitHex,'hex'),actorBytes=Buffer.from(unit.actorHex,'hex');
      const slots=unit.equipment.map((row:number[],slot:number)=>({slot,itemId:row[0],byte1:row[1]}));
      const actual=nativeBattleAttributes([...unitBytes.subarray(0x15,0x1a)],[...actorBytes.subarray(0x18,0x1d)],slots,equipment);
      if(JSON.stringify(actual)!==JSON.stringify(unit.combat))failures.push({id,slot:unit.slot,actual,expected:unit.combat});
    }
  }
  expect(failures).toEqual([]);
});
