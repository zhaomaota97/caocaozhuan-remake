import {createHash} from 'node:crypto';
import {readFileSync,readdirSync,statSync,writeFileSync} from 'node:fs';
import {join,relative} from 'node:path';

const root=process.cwd();
const roots=['public/assets/native-extracted','public/assets/maps','public/assets/animations','public/assets/audio','public/assets/portraits','public/assets/ui','public/assets/effects'];
const files=[];
function walk(path){for(const name of readdirSync(path)){const full=join(path,name);if(statSync(full).isDirectory())walk(full);else files.push(full);}}
for(const path of roots){try{walk(join(root,path));}catch{} }
const manifest=files.sort().map(file=>({path:relative(root,file).replaceAll('\\','/'),bytes:statSync(file).size,sha256:createHash('sha256').update(readFileSync(file)).digest('hex')}));
writeFileSync(join(root,'docs/RESOURCE-MANIFEST.json'),JSON.stringify({generatedAt:new Date().toISOString(),files:manifest},null,2)+'\n');
console.log(`Manifest written: ${manifest.length} files.`);
