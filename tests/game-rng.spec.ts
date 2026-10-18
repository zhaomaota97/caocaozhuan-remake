import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {GameRng} from '../src/rules/gameRng';

test('random outputs and state advancement match all original native batches',()=>{
  const rows=JSON.parse(readFileSync('tests/fixtures/native-rng.json','utf8'));
  expect(rows).toHaveLength(56);
  for(const row of rows){
    const rng=new GameRng(row.seed);
    const values=row.values.map(()=>row.kind==='sequence'?rng.draw():
      row.kind==='bounded'?rng.bounded(row.bound):rng.chance(row.percent));
    expect(values,`${row.kind} seed=${row.seed}`).toEqual(row.kind==='chance'?row.values.map(Boolean):row.values);
    expect(rng.state).toBe(row.state);
  }
});
