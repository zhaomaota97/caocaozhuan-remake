import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativePaletteLoad} from '../src/rules/nativePaletteLoad';
test('short palette conversion preserves native prior-tail behavior',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-short-palette-tail.json','utf8'));
  expect(evidence.passed).toBe(4);expect(evidence.resourceBytes).toBe(738);
  const resource=evidence.rows[0].palette.slice(0,738).map((value:number)=>value<<4);
  for(const row of evidence.rows)expect(nativePaletteLoad(Array(768).fill(row.initial),resource)).toEqual(row.palette);
});
