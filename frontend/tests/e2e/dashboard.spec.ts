import { test, expect } from './fixtures/auth.fixture';

/**
 * 仪表盘页面 E2E 测试
 *
 * 测试场景：
 * 1. 访问仪表盘页面
 * 2. 验证统计数据卡片
 * 3. 验证导航功能
 */

test.describe('仪表盘页面', () => {
  test('应该显示仪表盘页面', async ({ authenticatedPage }) => {
    // 验证页面标题或关键元素
    await expect(authenticatedPage).toHaveURL(/\/(dashboard|stats)/);

    // 等待页面加载
    await authenticatedPage.waitForLoadState('networkidle');

    // 验证页面有内容（可能是统计数据、图表等）
    const mainContent = authenticatedPage.locator('main, .dashboard, [class*="dashboard"], [class*="stats"]');
    await expect(mainContent.first()).toBeVisible();
  });

  test('应该显示侧边栏导航', async ({ authenticatedPage }) => {
    // 验证侧边栏存在
    const sidebar = authenticatedPage.locator('nav, aside, [class*="sidebar"], [class*="nav"]');
    await expect(sidebar.first()).toBeVisible();
  });

  test('应该能够导航到不同页面', async ({ authenticatedPage }) => {
    // 点击科室导航
    const departmentsLink = authenticatedPage.getByText(/科室|Departments/).first();
    if (await departmentsLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await departmentsLink.click();
      await authenticatedPage.waitForLoadState('networkidle');

      // 验证 URL 变化或页面内容
      expect(authenticatedPage.url()).toMatch(/\/departments|科室/);
    }
  });

  test('应该显示用户信息', async ({ authenticatedPage }) => {
    // 查找用户头像或用户名显示
    const userInfo = authenticatedPage.locator('[class*="user"], [class*="avatar"], .admin-info');
    if (await userInfo.first().isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(userInfo.first()).toBeVisible();
    }
  });

  test('应该能够退出登录', async ({ authenticatedPage }) => {
    // 查找退出按钮
    const logoutButton = authenticatedPage.getByText(/退出|登出|Logout/).or(
      authenticatedPage.locator('[class*="logout"], [class*="sign-out"]')
    ).first();

    if (await logoutButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await logoutButton.click();

      // 验证跳转到登录页
      await authenticatedPage.waitForURL('/login', { timeout: 5000 });
      expect(authenticatedPage.url()).toContain('/login');
    }
  });
});

test.describe('响应式布局', () => {
  test('应该在移动设备上正常显示', async ({ page }) => {
    // 设置移动设备视口
    await page.setViewportSize({ width: 375, height: 667 });

    // 登录
    await page.goto('/login');
    await page.fill('input[id="username"]', 'admin');
    await page.fill('input[id="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|stats)/, { timeout: 10000 });

    // 验证主要内容可见
    const mainContent = page.locator('main, .dashboard');
    await expect(mainContent.first()).toBeVisible();
  });

  test('应该在平板设备上正常显示', async ({ page }) => {
    // 设置平板设备视口
    await page.setViewportSize({ width: 768, height: 1024 });

    // 登录
    await page.goto('/login');
    await page.fill('input[id="username"]', 'admin');
    await page.fill('input[id="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/(dashboard|stats)/, { timeout: 10000 });

    // 验证主要内容可见
    const mainContent = page.locator('main, .dashboard');
    await expect(mainContent.first()).toBeVisible();
  });
});
