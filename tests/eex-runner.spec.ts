import {test,expect} from '@playwright/test';
import {runVerifiedEex} from '../src/rules/eexRunner';

test('verified EEX runner applies common state then dialogue',()=>{
  expect(runVerifiedEex([
    {kind:'common',command:{opcode:103,tag:4,value:4}},
    {kind:'dialogue',text:'&03\n出击'}
  ],{portraitFlags:0,portraitPhase:0})).toEqual({common:{portraitFlags:0,portraitPhase:3},dialogue:[{speakerId:3,text:'出击'}],unsupported:[]});
});
