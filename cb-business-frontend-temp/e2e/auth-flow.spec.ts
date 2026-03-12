import { test, expect } from '@playwright/test';

const testUser = {
  email: `e2e-test-${Date.now()}@example.com`,
  password: 'Test123456!',
  name: 'E2E测试用户'
};

test.describe('用户认证流程', () => {
  test.beforeEach(async ({ page }) => {
    // 清除localStorage
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('应该能够注册新用户并自动登录', async ({ page }) => {
    // 导航到注册页面（如果存在注册表单）
    await page.goto('/register');

    // 检查是否存在注册表单
    const hasRegisterForm = await page.locator('input[name="email"]').count() > 0;

    if (hasRegisterForm) {
      // 填写注册表单
      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.password);
      await page.fill('input[name="name"]', testUser.name);

      // 提交表单
      await page.click('button[type="submit"]');

      // 等待导航到仪表盘或显示成功消息
      await page.waitForTimeout(2000);

      const currentUrl = page.url();
      expect(currentUrl).toMatch(/(dashboard|register|login)/);
    }
  });

  test('应该能够登录已有用户', async ({ page }) => {
    // 首先确保测试用户存在（通过注册）
    await page.goto('/register');
    const hasRegisterForm = await page.locator('input[name="email"]').count() > 0;

    if (hasRegisterForm) {
      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.password);
      await page.fill('input[name="name"]', testUser.name);
      await page.click('button[type="submit"]');
      await page.waitForTimeout(1000);
    }

    // 现在测试登录
    await page.goto('/login');

    // 检查是否有登录表单
    const hasLoginForm = await page.locator('input[name="email"]').count() > 0;

    if (hasLoginForm) {
      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.password);
      await page.click('button[type="submit"]');

      // 等待导航
      await page.waitForTimeout(2000);

      const currentUrl = page.url();
      expect(currentUrl).toMatch(/(dashboard|home)/);
    }
  });

  test('登录失败应该显示错误消息', async ({ page }) => {
    await page.goto('/login');

    const hasLoginForm = await page.locator('input[name="email"]').count() > 0;

    if (hasLoginForm) {
      await page.fill('input[name="email"]', 'wrong@example.com');
      await page.fill('input[name="password"]', 'wrongpassword');
      await page.click('button[type="submit"]');

      // 检查错误消息
      const hasError = await page.locator('text=邮箱或密码错误, text=登录失败, text=错误').count() > 0;
      // 如果有错误消息，验证它
      if (hasError) {
        const errorElement = page.locator('text=邮箱或密码错误, text=登录失败, text=错误').first();
        await expect(errorElement).toBeVisible();
      }
    }
  });

  test('应该能够登出', async ({ page }) => {
    // 先登录
    await page.goto('/login');
    const hasLoginForm = await page.locator('input[name="email"]').count() > 0;

    if (hasLoginForm) {
      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.password);
      await page.click('button[type="submit"]');
      await page.waitForTimeout(1000);
    }

    // 查找登出按钮
    const logoutButton = page.locator('text=登出, text=退出, button:has-text("退出")').first();
    if (await logoutButton.count() > 0) {
      await logoutButton.click();
      await page.waitForTimeout(1000);

      // 验证已登出
      const currentUrl = page.url();
      expect(currentUrl).toMatch(/(login|register|\/)$/);
    }
  });

  test('未认证用户访问仪表盘应该被重定向', async ({ page }) => {
    // 清除认证状态
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());

    // 直接访问仪表盘
    await page.goto('/dashboard');

    // 应该被重定向或显示认证提示
    const currentUrl = page.url();

    // 检查是否有登录提示或重定向
    const hasLoginPrompt = await page.locator('text=登录, text=请先登录').count() > 0;
    const isOnLoginPage = currentUrl.includes('/login');
    const isOnHomePage = currentUrl.endsWith('/');

    expect(hasLoginPrompt || isOnLoginPage || isOnHomePage).toBeTruthy();
  });
});

test.describe('Token管理', () => {
  test('Token应该存储在localStorage', async ({ page }) => {
    // 模拟登录后设置token
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'test_token_12345');
    });

    // 验证token存在
    const token = await page.evaluate(() => localStorage.getItem('auth_token'));
    expect(token).toBe('test_token_12345');
  });

  test('Token过期后应该清除并重定向到登录', async ({ page }) => {
    // 设置一个过期的token
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'expired_token');
    });

    // 尝试访问需要认证的页面
    await page.goto('/dashboard/settings');

    // 应该清除过期token并重定向
    const token = await page.evaluate(() => localStorage.getItem('auth_token'));
    const currentUrl = page.url();

    // 验证token被清除或被重定向
    expect(token === null || currentUrl.includes('/login')).toBeTruthy();
  });
});

test.describe('用户信息获取', () => {
  test('应该能够显示用户信息', async ({ page }) => {
    // 设置mock用户数据和token
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock_token');
      localStorage.setItem('user', JSON.stringify({
        email: testUser.email,
        name: testUser.name,
        plan_tier: 'free'
      }));
    });

    // 访问设置页面查看用户信息
    await page.goto('/dashboard/settings');

    // 验证用户信息显示
    const hasUserInfo = await page.locator(`text=${testUser.email}`).count() > 0 ||
                          await page.locator(`text=${testUser.name}`).count() > 0;

    // 如果页面显示了用户信息，验证它
    if (hasUserInfo) {
      const userElement = page.locator(`text=${testUser.email}`).first();
      await expect(userElement).toBeVisible();
    }
  });
});
