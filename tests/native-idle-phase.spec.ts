import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nextNativeIdlePhase,NATIVE_IDLE_WAIT_TICKS,NATIVE_IDLE_WAIT_MS} from '../src/rules/nativeIdlePhase';
test('idle wait cadence and phase progression match 15 original controller traces',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-idle-phase-wait.json','utf8'));
  expect(evidence.total).toBe(15);expect(evidence.passed).toBe(15);expect(NATIVE_IDLE_WAIT_MS).toBe(400);
  for(const row of evidence.rows){
    let phase=row.phase;const frames=[];
    for(let tick=1000+NATIVE_IDLE_WAIT_TICKS;tick<1000+row.elapsed;tick+=NATIVE_IDLE_WAIT_TICKS){phase=nextNativeIdlePhase(phase);frames.push({tick,phase});}
    expect(frames).toEqual(row.frames);expect(phase).toBe(row.finalPhase);
  }
});
