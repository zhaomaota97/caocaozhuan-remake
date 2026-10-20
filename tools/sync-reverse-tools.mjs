import {mkdirSync,readdirSync,readFileSync,copyFileSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';

const source=process.argv[2];
if(!source)throw new Error('Usage: node tools/sync-reverse-tools.mjs <reverse-workspace-tools>');
const destination='docs/reverse-engineering/tool-sources';
mkdirSync(destination,{recursive:true});
const files=[];
for(const entry of readdirSync(source,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name))){
  if(!entry.isFile())continue;
  const bytes=readFileSync(join(source,entry.name));
  copyFileSync(join(source,entry.name),join(destination,entry.name));
  files.push({name:entry.name,bytes:bytes.length,sha256:createHash('sha256').update(bytes).digest('hex')});
}
writeFileSync('docs/reverse-engineering/TOOL-SOURCES-MANIFEST.json',JSON.stringify({scope:'Exact source archive; original root-relative paths retained, not standalone execution',files},null,2)+'\n');
console.log(`Archived ${files.length} reverse tool source files.`);
