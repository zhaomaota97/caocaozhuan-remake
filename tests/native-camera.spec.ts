import {test,expect} from '@playwright/test';
import {nativeCameraSteps,clampNativeCamera,nativeCameraTargetFromActorRecord} from '../src/rules/nativeCamera';

test('native camera advances at most four tiles per axis per commit',()=>{
  expect(nativeCameraSteps({x:0,y:0},{x:10,y:9})).toEqual([
    {x:3,y:3},{x:5,y:5},{x:7,y:7},{x:8,y:8},{x:9,y:9},{x:10,y:9}
  ]);
});
test('native camera mode 1 clamps target to viewport bounds',()=>{
  expect(clampNativeCamera({x:-2,y:99},{width:20,height:20},{width:8,height:6})).toEqual({x:0,y:14});
});
test('native camera target reads actor record offsets 0x06 and 0x07',()=>{
  const record=new Uint8Array(0x24);record[0]=99;record[6]=14;record[7]=17;
  expect(nativeCameraTargetFromActorRecord(record)).toEqual({x:14,y:17});
});
