import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('all 58 scenario scripts have native first-play BGM mappings',()=>{
  const mapping=JSON.parse(readFileSync('data/mappings/scenario-music.json','utf8'));
  expect(Object.keys(mapping)).toHaveLength(58);
  for(let id=0;id<58;id++){
    const row=mapping[`S_${String(id).padStart(2,'0')}.eex`];
    expect(row.track).toBeGreaterThan(0);
    expect(row.asset).toMatch(/^\/assets\/audio\/bgm\/\d\d-AudioTrack \d\d\.mp3$/);
  }
});
