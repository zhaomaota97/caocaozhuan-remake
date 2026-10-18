import {readFileSync,readdirSync,statSync} from 'node:fs';
import {join} from 'node:path';

const root=process.cwd();
const roots=['src','data','package.json','vite.config.ts','vite.config.js'];
const files=[];
function walk(path){const stat=statSync(path);if(stat.isFile()){files.push(path);return;}for(const name of readdirSync(path))walk(join(path,name));}
for(const path of roots){try{walk(join(root,path));}catch{} }
const needle=/C:[\\/]Users[\\/]40902[\\/]Desktop[\\/]sanguozhi|\\\\sanguozhi|\/sanguozhi/ig;
const violations=[];
for(const file of files){const text=readFileSync(file,'utf8');if(needle.test(text))violations.push(file.replace(root+'\\',''));}
if(violations.length){console.error('Runtime dependency paths found:',violations.join(', '));process.exit(1);}
console.log(`Independent runtime scan passed (${files.length} files).`);
