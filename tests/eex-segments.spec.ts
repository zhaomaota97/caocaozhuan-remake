import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('all migrated EEX files have validated ordered segment tables',()=>{
  const result=JSON.parse(readFileSync('data/mappings/eex-segments-runtime.json','utf8'));
  expect(result.files).toBe(117);
  expect(result.segments).toBeGreaterThan(117);
  for(const file of result.rows){
    expect(file.tableOffset).toBeGreaterThan(0);
    expect(file.segments.length).toBeGreaterThan(0);
    for(const segment of file.segments){
      expect(segment.offset).toBeGreaterThan(file.tableOffset);
      expect(segment.size).toBeGreaterThanOrEqual(4);
      expect(segment.lengthDelimitedBlock).toBe(segment.firstWord===1&&segment.secondWord===segment.size-4);
    }
  }
});
