import {test,expect} from '@playwright/test';
import {readFileSync,readdirSync} from 'node:fs';
import {createHash} from 'node:crypto';

test('complete reverse tool source archive matches its captured manifest',()=>{
  const root='docs/reverse-engineering/tool-sources';
  const manifest=JSON.parse(readFileSync('docs/reverse-engineering/TOOL-SOURCES-MANIFEST.json','utf8'));
  expect(manifest.files.length).toBeGreaterThanOrEqual(277);
  expect(readdirSync(root).length).toBe(manifest.files.length);
  for(const entry of manifest.files){
    const bytes=readFileSync(`${root}/${entry.name}`);
    expect(bytes.length,entry.name).toBe(entry.bytes);
    expect(createHash('sha256').update(bytes).digest('hex'),entry.name).toBe(entry.sha256);
  }
});
