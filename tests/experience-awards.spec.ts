import {test,expect} from '@playwright/test';
import {nativeUnitExperienceAward,nativeWeaponExperienceAward} from '../src/rules/experienceAwards';

test('native unit award distinguishes lethal and level delta',()=>{
  expect(nativeUnitExperienceAward({enabled:true,attackerLevel:1,defenderLevel:4,hpDamage:10,defenderHp:100,multiplier:10})).toBe(14);
  expect(nativeUnitExperienceAward({enabled:true,attackerLevel:1,defenderLevel:4,hpDamage:100,defenderHp:100,multiplier:10,leaderMatch:true})).toBe(112);
});
test('native weapon award requires category-zero weapon',()=>{
  expect(nativeWeaponExperienceAward(true,5,5,10,0,10,0)).toBe(3);
  expect(nativeWeaponExperienceAward(true,5,5,10,0,10,10)).toBe(0);
});
