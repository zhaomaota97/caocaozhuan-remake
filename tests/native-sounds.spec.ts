import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';

const manifest=JSON.parse(readFileSync('data/mappings/native-sound-assets.json','utf8'));

test('all native sound banks are served intact from the independent project',async({request})=>{
  expect(manifest.sounds).toHaveLength(89);
  expect(new Set(manifest.sounds.map((sound:{url:string})=>sound.url)).size).toBe(89);
  for(const sound of manifest.sounds){
    const response=await request.get('http://127.0.0.1:5173'+sound.url);
    expect(response.ok(),sound.url).toBe(true);
    const bytes=await response.body();
    expect(bytes.length,sound.url).toBe(sound.bytes);
    expect(createHash('sha256').update(bytes).digest('hex'),sound.url).toBe(sound.sha256);
  }
});

test('browser decodes all seven original movement sounds',async({page})=>{
  await page.goto('http://127.0.0.1:5173/');
  const urls=manifest.sounds.filter((sound:{id:number})=>sound.id>=23&&sound.id<=29)
    .map((sound:{url:string})=>sound.url);
  expect(urls).toHaveLength(7);
  const durations=await page.evaluate(async(paths:string[])=>{
    const audio=new AudioContext();
    try{
      const decoded=[];
      for(const path of paths){
        const response=await fetch(path);
        const buffer=await audio.decodeAudioData(await response.arrayBuffer());
        decoded.push(buffer.duration);
      }
      return decoded;
    }finally{await audio.close();}
  },urls);
  for(const duration of durations)expect(duration).toBeGreaterThan(0);
});
