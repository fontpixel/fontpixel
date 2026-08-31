import { defineConfig } from '@playwright/test';

const PORT = 4399;

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  use: {
    // 尾斜杠必须保留:测试里用不带前导斜杠的相对路径(如 'zh/')拼接
    baseURL: `http://localhost:${PORT}/`,
  },
  webServer: {
    command: `npm run build && npm run preview -- --port ${PORT}`,
    url: `http://localhost:${PORT}/zh/`,
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
});
