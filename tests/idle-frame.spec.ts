import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { idleFrame } from '../src/rules/idleFrame';

interface NativeFrameCase {
  direction: number;
  injured: number;
  flags: number;
  status: number;
  phase: number;
  tile: number;
  match: boolean;
}

test('standalone idle selector matches every captured native result', () => {
  const evidence=JSON.parse(readFileSync(resolve('tests/fixtures/native-idle-frame-validation.json'),'utf8'));
  expect(evidence.cases).toBe(512);
  expect(evidence.matched).toBe(512);
  expect(evidence.rows).toHaveLength(512);
  for(const row of evidence.rows as NativeFrameCase[]){
    expect(row.match).toBe(true);
    expect(idleFrame(row.direction,row.flags,row.status,row.phase,Boolean(row.injured)),JSON.stringify(row)).toBe(row.tile);
  }
});
