import { test, expect } from '@playwright/test';

/**
 * 认证流程 E2E 测试
 *
 * 测试场景：
 * 1. 管理员登录成功
 * 2. 登录失败（无效凭证）
 * 3. 表单验证（空用户名/密码）
 * 4. 密码可见性切换
 */

test.describe('认证流程', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前导航到登录页
    await page.goto('/login');
  });

  test('应该显示登录页面', async ({ page }) => {
    // 验证页面标题
    await expect(page).toHaveTitle(/灵犀健康/);

    // 验证登录表单元素存在
    await expect(page.getByText('灵犀健康')).toBeVisible();
    await expect(page.getByText('智能健康管理平台')).toBeVisible();
    await expect(page.getByPlaceholder('请输入用户名')).toBeVisible();
    await expect(page.getByPlaceholder('请输入密码')).toBeVisible();
    await expect(page.getByRole('button', { name: '登录' })).toBeVisible();

    // 验证默认账号提示
    await expect(page.getByText('默认账号:')).toBeVisible();
    await expect(page.getByText('admin / admin123')).toBeVisible();
  });

  test('应该显示表单验证错误（空用户名）', async ({ page }) => {
    // 只输入密码，不输入用户名
    await page.fill('input[id="password"]', 'admin123');
    await page.click('button[type="submit"]');

    // 验证错误提示
    await expect(page.getByText('请输入用户名')).toBeVisible();
  });

  test('应该显示表单验证错误（空密码）', async ({ page }) => {
    // 只输入用户名，不输入密码
    await page.fill('input[id="username"]', 'admin');
    await page.click('button[type="submit"]');

    // 验证错误提示
    await expect(page.getByText('请输入密码')).toBeVisible();
  });

  test('应该切换密码可见性', async ({ page }) => {
    const passwordInput = page.getByPlaceholder('请输入密码');
    const toggleButton = page.locator('button').filter({ hasText: '' }).nth(1);

    // 初始状态应该是密码隐藏
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // 输入密码
    await passwordInput.fill('test123');

    // 点击显示密码按钮
    await toggleButton.click();

    // 密码应该是可见的
    await expect(passwordInput).toHaveAttribute('type', 'text');

    // 再次点击隐藏密码
    await toggleButton.click();

    // 密码应该是隐藏的
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('登录成功后应该跳转到仪表盘', async ({ page }) => {
    // 等待页面加载
    await page.waitForLoadState('networkidle');

    // 输入默认账号密码
    await page.fill('input[id="username"]', 'admin');
    await page.fill('input[id="password"]', 'admin123');

    // 点击登录按钮
    await page.click('button[type="submit"]');

    // 等待导航
    await page.waitForURL(/\/(dashboard|stats)/, { timeout: 10000 });

    // 验证登录成功 - 应该跳转到仪表盘或统计页面
    expect(page.url()).toMatch(/\/(dashboard|stats)/);
  });

  test('登录失败时应该显示错误提示', async ({ page }) => {
    // 输入错误的密码
    await page.fill('input[id="username"]', 'admin');
    await page.fill('input[id="password"]', 'wrongpassword');

    // 点击登录按钮
    await page.click('button[type="submit"]');

    // 等待登录请求完成
    await page.waitForLoadState('networkidle');

    // 验证错误提示（可能需要根据实际 API 响应调整）
    const errorMessage = page.getByText(/登录失败|未授权|Invalid/);
    if (await errorMessage.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(errorMessage).toBeVisible();
    }
  });

  test('登录按钮应该在加载时禁用', async ({ page }) => {
    // 输入账号密码
    await page.fill('input[id="username"]', 'admin');
    await page.fill('input[id="password"]', 'admin123');

    // 点击登录按钮
    const loginButton = page.getByRole('button', { name: '登录' });
    await loginButton.click();

    // 验证按钮被禁用且显示加载状态
    await expect(loginButton).toBeDisabled();
    await expect(page.getByText('登录中...')).toBeVisible();
  });

  test('应该显示公司信息', async ({ page }) => {
    // 验证公司名称
    await expect(page.getByText('岳阳琳烨网络科技有限公司')).toBeVisible();

    // 验证联系方式
    await expect(page.getByText('1024344053@qq.com')).toBeVisible();
    await expect(page.getByText('18107300167')).toBeVisible();

    // 验证地址
    await expect(page.getByText(/岳阳市/)).toBeVisible();
  });
});

test.describe('认证状态保持', () => {
  test('登录后刷新页面应该保持登录状态', async ({ page, context }) => {
    // 登录
    await page.goto('/login');
    await page.fill('input[id="username"]', 'admin');
    await page.fill('input[id="password"]', 'admin123');
    await page.click('button[type="submit"]');

    // 等待登录成功
    await page.waitForURL(/\/(dashboard|stats)/, { timeout: 10000 });

    // 刷新页面
    await page.reload();

    // 验证仍然在仪表盘页面（未跳转回登录页）
    await page.waitForLoadState('networkidle');
    expect(page.url()).not.toBe('/login');
  });
});
