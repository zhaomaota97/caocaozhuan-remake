import { test, expect } from '@playwright/test';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
const images: Array<{url:string;sha256:string}> = JSON.parse(readFileSync(resolve('data/mappings/dll-image-assets.json'),'utf8'));

test('all decoded DLL images have unique independent paths and intact content', () => {
  expect(images).toHaveLength(304);
  expect(new Set(images.map(image => image.url)).size).toBe(304);
  for(const image of images){
    expect(image.url).toMatch(/^\/assets\/ui\/dll\/(cmdicon|itemicon|mapatr|mgcicon)\/\d+\.png$/);
    const bytes=readFileSync(resolve('public',image.url.slice(1)));
    expect(createHash('sha256').update(bytes).digest('hex')).toBe(image.sha256);
  }
});
