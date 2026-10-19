import {test,expect} from '@playwright/test';
import {EexCursor} from '../src/rules/eexCursor';

test('EEX cursor reads little-endian primitives and advances exactly',()=>{
  const data=Uint8Array.from([0x34,0x12,0x78,0x56,0x34,0x12,65,66,0,2,0,0x9a,0xbc]);
  const cursor=new EexCursor(data);
  expect(cursor.integer(2)).toBe(0x1234);expect(cursor.integer(4)).toBe(0x12345678);
  expect(Array.from(cursor.string())).toEqual([65,66]);expect(cursor.parameter(1)).toBe(2);
  expect(cursor.integer(2)).toBe(0xbc9a);expect(cursor.pos).toBe(data.length);
});

test('EEX cursor preserves native mismatch sentinels and rejects truncation',()=>{
  const mismatch=new EexCursor(Uint8Array.from([2,0,1,0]));
  expect(mismatch.parameter(4)).toBe(0x80000000);expect(mismatch.parameter(2)).toBe(0x8000);
  expect(()=>new EexCursor(Uint8Array.from([1])).integer(2)).toThrow('truncated EEX integer');
  expect(()=>new EexCursor(Uint8Array.from([65])).string()).toThrow('unterminated EEX string');
});
