import {test,expect} from '@playwright/test';
import {dispatchNativeCommonCommand} from '../src/rules/eexCommonDispatcher';

test('dispatcher routes verified opcode 32',()=>{
  expect(dispatchNativeCommonCommand({portraitFlags:0,portraitPhase:0},{opcode:32,tag:74,value:7})).toEqual({status:1,state:{portraitFlags:7,portraitPhase:0}});
});
test('dispatcher routes verified opcode 103',()=>{
  expect(dispatchNativeCommonCommand({portraitFlags:0,portraitPhase:0},{opcode:103,tag:4,value:3})).toEqual({status:1,state:{portraitFlags:0,portraitPhase:2}});
});
