import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';

const manifest=JSON.parse(readFileSync('docs/reverse-engineering/TOOL-SOURCES-MANIFEST.json','utf8'));
for(const entry of manifest.files){
  const path=`docs/reverse-engineering/tool-sources/${entry.name}`;
  const bytes=execFileSync('git',['show',`:${path}`],{maxBuffer:8*1024*1024});
  const hash=createHash('sha256').update(bytes).digest('hex');
  if(bytes.length!==entry.bytes||hash!==entry.sha256)throw new Error(`Git index changes archived source bytes: ${entry.name}`);
}
console.log(`Git-index source evidence passed (${manifest.files.length} original byte sequences).`);
