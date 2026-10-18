import {createHash} from 'node:crypto';
import {readFileSync,statSync} from 'node:fs';
import {join} from 'node:path';

const root=process.cwd();
const manifest=JSON.parse(readFileSync(join(root,'docs/RESOURCE-MANIFEST.json'),'utf8').replace(/^\uFEFF/,''));
const failures=[];
for(const entry of manifest.files){
  const file=join(root,entry.path);
  try{
    const bytes=statSync(file).size,hash=createHash('sha256').update(readFileSync(file)).digest('hex');
    if(bytes!==entry.bytes||hash!==entry.sha256)failures.push(`${entry.path} (expected ${entry.bytes}/${entry.sha256}, got ${bytes}/${hash})`);
  }catch(error){failures.push(`${entry.path} (${error.message})`);}
}
if(failures.length){console.error(`Resource manifest failed: ${failures.length}`);console.error(failures.slice(0,20).join('\n'));process.exit(1);}
console.log(`Resource manifest passed (${manifest.files.length} files).`);
