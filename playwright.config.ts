import { defineConfig } from '@playwright/test';
export default defineConfig({ use: { channel: 'msedge', viewport: { width: 1280, height: 900 } } });
