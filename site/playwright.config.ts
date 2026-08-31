import { defineConfig } from '@playwright/test';

const PORT = 4399;

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  use: {
    // trailing slash must be kept: tests concatenate relative paths without a leading slash (e.g. 'zh/')
    baseURL: `http://localhost:${PORT}/`,
  },
  webServer: {
    command: `npm run build && npm run preview -- --port ${PORT}`,
    url: `http://localhost:${PORT}/zh/`,
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
});
