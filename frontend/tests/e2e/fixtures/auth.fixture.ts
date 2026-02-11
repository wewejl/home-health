import { test as base } from '@playwright/test';

/**
 * 认证测试夹具
 *
 * 提供预配置的认证状态和登录辅助方法
 */

export interface AuthFixtures {
  authenticatedPage: ReturnType<typeof base['extend']>;
  loginAsAdmin: (page: ReturnType<typeof base['extend']>) => Promise<void>;
}

export const test = base.extend<AuthFixtures>({
  // 预认证的页面（已登录）
  authenticatedPage: async ({ page }, use) => {
    // 导航到登录页
    await page.goto('/login');

    // 登录（使用测试模式默认账号）
    await page.fill('input[id="username"]', 'admin');
    await page.fill('input[id="password"]', 'admin123');
    await page.click('button[type="submit"]');

    // 等待登录成功
    await page.waitForURL(/\/(dashboard|stats)/, { timeout: 10000 });

    // 使用已登录的页面
    await use(page);
  },

  // 登录辅助方法
  loginAsAdmin: async ({}, use) => {
    const loginHelper = async (page: ReturnType<typeof base['extend']>) => {
      await page.goto('/login');
      await page.fill('input[id="username"]', 'admin');
      await page.fill('input[id="password"]', 'admin123');
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/(dashboard|stats)/, { timeout: 10000 });
    };
    await use(loginHelper);
  },
});

export { expect } from '@playwright/test';
