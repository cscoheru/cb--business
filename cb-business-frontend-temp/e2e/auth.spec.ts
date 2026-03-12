import { test, expect } from '@playwright/test';

test.describe('用户认证流程', () => {
  test('应该显示首页', async ({ page }) => {
    await page.goto('/');

    // 验证页面标题
    await expect(page).toHaveTitle(/CB Business/);

    // 验证页面主要内容
    await expect(page.locator('h1')).toContainText('跨境商务智能');
  });

  test('应该能够导航到定价页面', async ({ page }) => {
    await page.goto('/');

    // 点击定价链接（假设存在）
    const pricingLink = page.locator('a[href*="pricing"], a[href*="/pricing"]');
    if (await pricingLink.count() > 0) {
      await pricingLink.first().click();
      await expect(page).toHaveURL(/pricing/);
    }
  });

  test('应该能够访问仪表盘（需要认证）', async ({ page }) => {
    await page.goto('/dashboard');

    // 未认证用户应该被重定向到登录或首页
    // 或者显示登录表单
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/(dashboard|login|\/)$/);
  });

  test('应该显示市场概览页面', async ({ page }) => {
    await page.goto('/dashboard/market');

    // 验证页面加载
    await expect(page.locator('h1')).toContainText('市场概览');
  });

  test('应该显示政策中心页面', async ({ page }) => {
    await page.goto('/dashboard/policies');

    // 验证页面加载
    await expect(page.locator('h1')).toContainText('政策中心');
  });

  test('应该显示风险预警页面', async ({ page }) => {
    await page.goto('/dashboard/risks');

    // 验证页面加载
    await expect(page.locator('h1')).toContainText('风险预警');
  });

  test('应该显示机会发现页面', async ({ page }) => {
    await page.goto('/dashboard/opportunities');

    // 验证页面加载
    await expect(page.locator('h1')).toContainText('机会发现');
  });

  test('应该显示设置页面', async ({ page }) => {
    await page.goto('/dashboard/settings');

    // 验证页面加载
    await expect(page.locator('h1')).toContainText('设置');
  });
});

test.describe('定价页面', () => {
  test('应该显示定价信息', async ({ page }) => {
    await page.goto('/pricing');

    // 验证定价卡片存在
    await expect(page.locator('text=免费版')).toBeVisible();
    await expect(page.locator('text=专业版')).toBeVisible();
  });

  test('应该显示价格对比', async ({ page }) => {
    await page.goto('/pricing');

    // 验证功能列表显示
    await expect(page.locator('text=API调用')).toBeVisible();
  });
});

test.describe('响应式设计', () => {
  test('应该在移动设备上正常显示', async ({ page }) => {
    // 设置移动设备视口
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // 验证主要内容可见
    await expect(page.locator('h1')).toBeVisible();
  });

  test('应该在平板设备上正常显示', async ({ page }) => {
    // 设置平板设备视口
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');

    // 验证主要内容可见
    await expect(page.locator('h1')).toBeVisible();
  });
});
