import {readFileSync,writeFileSync} from 'node:fs';
const corpus=JSON.parse(readFileSync('docs/reverse-engineering/native-palette-lookup-corpus.json','utf8'));
const scenes={};
for(const row of corpus.rows)if(row.name.startsWith('Spalet:'))scenes[row.name.slice(7)]=row.palette;
if(Object.keys(scenes).length!==58)throw new Error('Missing scene palettes');
writeFileSync('data/mappings/scene-palettes.json',JSON.stringify({scope:'Original four-bit Spalet channels with explicit zero-padded unused tail; not live transition state',scenes},null,2)+'\n');
console.log('Exported 58 readable scene palettes.');
