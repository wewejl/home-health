import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E 测试配置
 *
 * 测试环境：
 * - 本地开发: http://localhost:8150
 * - CI 环境: 使用 webServer 启动开发服务器
 *
 * 运行测试：
 * - npx playwright test              # 运行所有测试
 * - npx playwright test --ui         # UI 模式运行
 * - npx playwright test --headed     # 显示浏览器窗口
 * - npx playwright test --debug      # 调试模式
 */
export default defineConfig({
  // 测试文件位置
  testDir: './tests/e2e',

  // 是否并行运行测试
  fullyParallel: true,

  // CI 环境下禁止 only 运行
  forbidOnly: !!process.env.CI,

  // 失败重试次数
  retries: process.env.CI ? 2 : 0,

  // 并行 worker 数量
  workers: process.env.CI ? 1 : undefined,

  // 报告格式
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],

  // 全局测试配置
  use: {
    // 基础 URL
    baseURL: 'http://localhost:8150',

    // 失败时记录 trace
    trace: 'on-first-retry',

    // 失败时截图
    screenshot: 'only-on-failure',

    // 失败时录制视频
    video: 'retain-on-failure',

    // 浏览器窗口大小
    viewport: { width: 1280, height: 720 },

    // 测试超时时间（毫秒）
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },

  // 测试项目配置
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // 移动端测试
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  // CI 环境下启动开发服务器
  webServer: process.env.CI
    ? {
        command: 'npm run dev',
        url: 'http://localhost:8150',
        timeout: 120000,
        reuseExistingServer: false,
      }
    : undefined,

  // 期待超时时间
  expect: {
    timeout: 5000,
  },
});
