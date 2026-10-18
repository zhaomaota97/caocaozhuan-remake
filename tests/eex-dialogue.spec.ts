import {test,expect} from '@playwright/test';
import {parseNativeDialogueSegments} from '../src/rules/eexDialogue';

test('native dialogue splits speaker sections at newline ampersand',()=>{
  expect(parseNativeDialogueSegments('&03\n甲说\n&04\n乙说')).toEqual([
    {speakerId:3,text:'甲说'},{speakerId:4,text:'乙说'}
  ]);
});
test('native dialogue preserves plain narration and named speaker token',()=>{
  expect(parseNativeDialogueSegments('旁白\n&曹操\n乱世')).toEqual([
    {text:'旁白'},{speakerToken:'曹操',text:'乱世'}
  ]);
});
