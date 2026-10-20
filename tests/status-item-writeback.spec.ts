import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {nativeStatusItemWriteback} from '../src/rules/statusItemWriteback';

test('status-item writeback matches all 2560 original controller results',()=>{
  const evidence=JSON.parse(readFileSync('docs/reverse-engineering/native-status-item-controller.json','utf8'));
  expect(evidence.total).toBe(2560);expect(evidence.passed).toBe(2560);
  const failures=evidence.rows.filter((row:any)=>nativeStatusItemWriteback(row.category,row.status,row.target!==255)!==row.finalStatus||row.actorFlags!==165||row.returned!==Number(row.target!==255));
  expect(failures).toEqual([]);
});
