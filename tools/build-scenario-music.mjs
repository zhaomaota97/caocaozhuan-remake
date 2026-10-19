import {readFileSync,writeFileSync} from 'node:fs';
const source=JSON.parse(readFileSync('data/mappings/script-music-events.json','utf8'));
const result={};
for(const row of source.rows){
  if(!/^S_\d\d\.eex$/.test(row.script)||row.operation!=='play'||result[row.script])continue;
  result[row.script]={track:row.nativeTrack,asset:row.webAsset,offset:row.offset,source:'script-music-events.json'};
}
if(Object.keys(result).length!==58)throw new Error(`Expected 58 scenario music mappings, got ${Object.keys(result).length}`);
writeFileSync('data/mappings/scenario-music.json',JSON.stringify(result,null,2)+'\n');
console.log(`Scenario music mappings passed (${Object.keys(result).length} scripts).`);
