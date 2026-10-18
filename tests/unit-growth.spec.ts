import {test,expect} from '@playwright/test';
import {nativeUnitGrowth} from '../src/rules/unitGrowth';

test('native growth applies rank bonuses, experience levels and caps',()=>{
  expect(nativeUnitGrowth({unitId:0,level:1,experience:0,stats:[10,20,30,40,50,100,25],rankBases:[24,25,34,35,45],classGrowth:[3,3,3,3,3,5,1]},300)).toEqual({level:4,experience:0,stats:[16,26,36,49,59,115,28],levelsGained:3,eligible:true});
  expect(nativeUnitGrowth({unitId:0,level:49,experience:0,stats:[254,254,254,254,254,499,249],rankBases:[45,45,45,45,45],classGrowth:[3,3,3,3,3,5,1]},500)).toEqual({level:50,experience:255,stats:[255,255,255,255,255,500,250],levelsGained:1,eligible:true});
});
test('native growth leaves ineligible units unchanged',()=>{
  expect(nativeUnitGrowth({unitId:26,level:1,experience:0,stats:[1,2,3,4,5,6,7],rankBases:[0,0,0,0,0],classGrowth:[9,9,9,9,9,9,9]},500)).toEqual({level:1,experience:0,stats:[1,2,3,4,5,6,7],levelsGained:0,eligible:false});
});
