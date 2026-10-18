import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { restoreUnits } from '../src/save/localSave';
import type { Unit } from '../src/model/battle';

const baseline: Unit[] = JSON.parse(readFileSync('data/saves/slot-08.json','utf8')).actors.map((unit: Unit)=>({...unit,acted:false}));
test('invalid and empty browser saves cannot hide the native actor set',()=>{
  for(const raw of ['{',JSON.stringify({version:1,units:baseline}),JSON.stringify({version:2,slot:8,units:[]})]){
    expect(restoreUnits(raw,baseline)).toEqual(baseline);
  }
});
test('restoring browser state retains verified resource and actor fields',()=>{
  const units=baseline.map(unit=>({...unit}));
  units[0].name='untrusted name';
  units[0].direction=99;
  expect(restoreUnits(JSON.stringify({version:2,slot:8,units}),baseline)).toEqual(baseline);
});
