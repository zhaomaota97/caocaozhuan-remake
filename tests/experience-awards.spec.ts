import {test,expect} from '@playwright/test';
import {nativeUnitExperienceAward,nativeWeaponExperienceAward,nativeArmorExperienceAward,aggregateNativeExperience} from '../src/rules/experienceAwards';

test('native unit award distinguishes lethal and level delta',()=>{
  expect(nativeUnitExperienceAward({enabled:true,attackerLevel:1,defenderLevel:4,hpDamage:10,defenderHp:100,multiplier:10})).toBe(14);
  expect(nativeUnitExperienceAward({enabled:true,attackerLevel:1,defenderLevel:4,hpDamage:100,defenderHp:100,multiplier:10,leaderMatch:true})).toBe(112);
});
test('native weapon award requires category-zero weapon',()=>{
  expect(nativeWeaponExperienceAward(true,5,5,10,0,10,0)).toBe(3);
  expect(nativeWeaponExperienceAward(true,5,5,10,0,10,10)).toBe(0);
});
test('native armor award uses defender byte five and defender multiplier',()=>{
  expect(nativeArmorExperienceAward(3,5,10,0,10,0)).toBe(3);
  expect(nativeArmorExperienceAward(5,3,10,0,20,0)).toBe(8);
  expect(nativeArmorExperienceAward(3,5,10,0,20,1)).toBe(0);
});
test('native multi-target aggregation keeps max unit and weapon awards per action',()=>{
  const first=aggregateNativeExperience({unit:0,weapon:0,armorByTarget:{}},'a',12,2,3);
  expect(aggregateNativeExperience(first,'b',8,5,4)).toEqual({unit:12,weapon:5,armorByTarget:{a:3,b:4}});
});
