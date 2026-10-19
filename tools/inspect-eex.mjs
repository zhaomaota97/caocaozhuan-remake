import {readdirSync,readFileSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';

const root=process.cwd(),assetRoot=join(root,'public','assets','native-extracted');
function u16(data,offset){return data.readUInt16LE(offset);}
function u32(data,offset){return data.readUInt32LE(offset);}
function inspect(file){
  const data=readFileSync(file);
  if(data.subarray(0,4).toString('ascii')!=='EEX\0')throw new Error(`${file}: invalid EEX magic`);
  let pos=6;
  while(true){
    if(pos+4>data.length)throw new Error(`${file}: truncated extension header`);
    const kind=u16(data,pos),length=u16(data,pos+2);pos+=4+length;
    if(pos>data.length)throw new Error(`${file}: extension outside file`);
    if(kind===0)break;
  }
  const first=u32(data,pos),tableBytes=first-pos;
  if(first<=pos||tableBytes%4)throw new Error(`${file}: invalid offset table`);
  const offsets=[];for(let at=pos;at<first;at+=4)offsets.push(u32(data,at));
  for(let i=1;i<offsets.length;i++)if(offsets[i]<offsets[i-1])throw new Error(`${file}: unsorted offsets`);
  if(offsets.at(-1)>=data.length)throw new Error(`${file}: offset outside file`);
  const segments=offsets.map((offset,index)=>{const end=offsets[index+1]??data.length;const marker=u16(data,offset),length=u16(data,offset+2);return {offset,size:end-offset,firstWord:marker,secondWord:length,lengthDelimitedBlock:marker===1&&length===end-offset-4};});
  return {file:file.slice(assetRoot.length+1).replaceAll('\\','/'),tableOffset:pos,segments};
}
const files=[];function walk(path){for(const name of readdirSync(path,{withFileTypes:true})){const full=join(path,name.name);if(name.isDirectory())walk(full);else if(name.name.toLowerCase().endsWith('.eex'))files.push(full);}}
walk(assetRoot);const rows=files.sort().map(inspect);const result={files:rows.length,segments:rows.reduce((sum,row)=>sum+row.segments.length,0),rows};
writeFileSync(join(root,'data','mappings','eex-segments-runtime.json'),JSON.stringify(result,null,2)+'\n');
console.log(`EEX segment validation passed (${result.files} files, ${result.segments} segments).`);
