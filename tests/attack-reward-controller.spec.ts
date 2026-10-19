import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {applyNativeAttackerRewards} from '../src/rules/attackRewardController';

test('attacker reward controller matches all captured native writebacks',()=>{
  const evidence=JSON.parse(readFileSync(new URL('../docs/reverse-engineering/native-attack-reward-controller.json',import.meta.url),'utf8'));
  expect(evidence.rows).toHaveLength(2592);
  const failures=[];
  for(const row of evidence.rows){
    const result=applyNativeAttackerRewards({unitId:row.id,level:row.level,experience:row.xp,stats:Array(7).fill(10),rankBases:Array(5).fill(25),classGrowth:evidence.growth},[
      {slot:0,itemId:0,categoryByte:0,level:row.weaponLevel,experience:row.weaponXp},
      {slot:1,itemId:255,categoryByte:0,level:0,experience:0},
    ],{unit:row.award,weapon:row.weaponAward});
    const actual={level:result.growth.level,xp:result.growth.experience,stats:result.growth.stats,weaponLevel:result.equipment[0].level,weaponXp:result.equipment[0].experience};
    const expected={level:row.finalLevel,xp:row.finalXp,stats:row.stats,weaponLevel:row.finalWeaponLevel,weaponXp:row.finalWeaponXp};
    if(JSON.stringify(actual)!==JSON.stringify(expected))failures.push({input:row,actual,expected});
    expect(result.equipment[1]).toEqual({slot:1,itemId:255,categoryByte:0,level:0,experience:0});
  }
  expect(failures).toEqual([]);
});
