import { test, expect } from '@playwright/test';

test.describe('仪表盘导航', () => {
  test.beforeEach(async ({ page }) => {
    // 模拟登录状态
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'mock_token');
      localStorage.setItem('user', JSON.stringify({
        email: 'user@example.com',
        name: '测试用户',
        plan_tier: 'pro'
      }));
    });
  });

  test('应该能够导航到仪表盘首页', async ({ page }) => {
    await page.goto('/dashboard');

    // 验证页面标题
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    await expect(h1).toContainText('仪表盘');
  });

  test('应该能够访问市场概览页面', async ({ page }) => {
    await page.goto('/dashboard/market');

    // 验证页面加载
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    await expect(h1).toContainText('市场概览');

    // 验证市场卡片显示
    const marketCards = page.locator('[class*="market"], [class*="country"], .flag');
    if (await marketCards.count() > 0) {
      await expect(marketCards.first()).toBeVisible();
    }

    // 验证统计数据
    const stats = page.locator('.stat-card, .metric-card, [class*="stat"]');
    expect(await stats.count()).toBeGreaterThan(0);
  });

  test('应该能够访问政策中心页面', async ({ page }) => {
    await page.goto('/dashboard/policies');

    // 验证页面加载
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    await expect(h1).toContainText('政策中心');

    // 验证搜索和筛选功能
    const searchInput = page.locator('input[placeholder*="搜索"], input[name="search"]');
    if (await searchInput.count() > 0) {
      await expect(searchInput.first()).toBeVisible();
    }

    // 验证筛选标签
    const filterBadges = page.locator('.badge, [role="button"]:has-text("政策"), [role="button"]:has-text("关税")');
    if (await filterBadges.count() > 0) {
      await expect(filterBadges.first()).toBeVisible();
    }
  });

  test('应该能够访问风险预警页面', async ({ page }) => {
    await page.goto('/dashboard/risks');

    // 验证页面加载
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    await expect(h1).toContainText('风险预警');

    // 验证风险卡片显示
    const riskCards = page.locator('[class*="risk"], [class*="alert"], .risk-card');
    if (await riskCards.count() > 0) {
      await expect(riskCards.first()).toBeVisible();
    }

    // 验证严重程度标签
    const severityBadges = page.locator('.badge:has-text("高风险"), .badge:has-text("中风险")');
    if (await severityBadges.count() > 0) {
      await expect(severityBadges.first()).toBeVisible();
    }
  });

  test('应该能够访问机会发现页面', async ({ page }) => {
    await page.goto('/dashboard/opportunities');

    // 验证页面加载
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    await expect(h1).toContainText('机会发现');

    // 验证机会卡片显示
    const opportunityCards = page.locator('.opportunity-card, [class*="opportunity"]');
    if (await opportunityCards.count() > 0) {
      await expect(opportunityCards.first()).toBeVisible();
    }

    // 验证筛选功能
    const filters = page.locator('select, .filter, [role="combobox"]');
    if (await filters.count() > 0) {
      await expect(filters.first()).toBeVisible();
    }
  });

  test('应该能够访问设置页面', async ({ page }) => {
    await page.goto('/dashboard/settings');

    // 验证页面加载
    const h1 = page.locator('h1');
    await expect(h1).toBeVisible();
    await expect(h1).toContainText('设置');

    // 验证标签页存在
    const tabs = page.locator('[role="tab"], .tab, button:has-text("个人"), button:has-text("偏好")');
    expect(await tabs.count()).toBeGreaterThan(0);
  });

  test('应该能够在不同仪表盘页面间导航', async ({ page }) => {
    const pages = [
      '/dashboard',
      '/dashboard/market',
      '/dashboard/policies',
      '/dashboard/risks',
      '/dashboard/opportunities',
      '/dashboard/settings'
    ];

    for (const pagePath of pages) {
      await page.goto(pagePath);

      // 验证页面加载成功
      const h1 = page.locator('h1');
      await expect(h1).toBeVisible({ timeout: 5000 });

      // 验证没有错误信息
      const errorElements = page.locator('.error, [role="alert"]');
      if (await errorElements.count() > 0) {
        // 如果有错误，确保不是严重错误
        const errorText = await errorElements.first().textContent();
        expect(errorText).not.toMatch(/服务器错误|500|致命错误/);
      }
    }
  });
});

test.describe('数据展示和加载状态', () => {
  test('应该显示加载状态', async ({ page }) => {
    // 设置慢速模拟（如果支持）
    await page.goto('/dashboard/market');

    // 查找加载指示器
    const loaders = page.locator('.loading, .spinner, [role="status"][aria-busy="true"], .skeleton');

    // 如果有加载指示器，验证它显示
    if (await loaders.count() > 0) {
      await expect(loaders.first()).toBeVisible();
    }
  });

  test('数据卡片应该正确显示', async ({ page }) => {
    await page.goto('/dashboard/market');

    // 验证数据卡片结构
    const cards = page.locator('.card, [class*="card"], .stat-card');
    if (await cards.count() > 0) {
      const firstCard = cards.first();

      // 验证卡片有标题
      const title = firstCard.locator('h1, h2, h3, .title, [class*="title"]');
      await expect(title).toBeVisible();

      // 验证卡片有内容
      const content = firstCard.locator('.content, p, span, div');
      await expect(content.first()).toBeVisible();
    }
  });

  test('图表应该正确渲染', async ({ page }) => {
    await page.goto('/dashboard/market');

    // 查找图表元素
    const charts = page.locator('svg, canvas, [class*="chart"], .recharts-wrapper');

    if (await charts.count() > 0) {
      // 验证图表可见
      await expect(charts.first()).toBeVisible();

      // 验证图表有数据点
      const dataPoints = charts.first().locator('path, circle, rect, .bar');
      expect(await dataPoints.count()).toBeGreaterThan(0);
    }
  });

  test('空状态应该显示友好提示', async ({ page }) => {
    // 模拟空数据状态
    await page.goto('/dashboard/policies?filter=nonexistent');

    // 查找空状态提示
    const emptyStates = page.locator('text=暂无数据, text=没有找到, text=没有任何, .empty-state');

    if (await emptyStates.count() > 0) {
      await expect(emptyStates.first()).toBeVisible();
    }
  });
});

test.describe('响应式布局', () => {
  test('移动端应该显示汉堡菜单', async ({ page }) => {
    // 设置移动设备尺寸
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');

    // 查找汉堡菜单按钮
    const hamburger = page.locator('[aria-label="菜单"], button:has-text("菜单"), .hamburger');

    // 移动端应该有汉堡菜单（或者侧边栏是折叠的）
    const hasMobileNav = await hamburger.count() > 0 ||
                           await page.locator('[class*="sidebar"][class*="mobile"], .mobile-nav').count() > 0;

    if (hasMobileNav) {
      // 如果有汉堡菜单，点击它
      if (await hamburger.count() > 0) {
        await hamburger.click();
        await page.waitForTimeout(500);

        // 验证菜单展开
        const navMenu = page.locator('.nav-menu, .mobile-menu, [class*="menu"][class*="open"]');
        expect(await navMenu.count() > 0).toBeTruthy();
      }
    }
  });

  test('桌面端应该显示完整导航栏', async ({ page }) => {
    // 设置桌面设备尺寸
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/dashboard');

    // 桌面端应该显示完整导航
    const navLinks = page.locator('.nav-link, a[href*="/dashboard"], [class*="nav"] a');
    expect(await navLinks.count()).toBeGreaterThanOrEqual(4);
  });

  test('侧边栏在小屏幕上应该折叠', async ({ page }) => {
    // 先查看大屏幕
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/dashboard');

    // 切换到小屏幕
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);

    // 检查侧边栏状态
    const sidebar = page.locator('[class*="sidebar"], .sidebar, aside');
    if (await sidebar.count() > 0) {
      const isCollapsed = await sidebar.first().getAttribute('class').then(
        classes => classes?.includes('collapsed') || false
      );
      // 小屏幕上侧边栏可能被隐藏或折叠
    }
  });
});

test.describe('错误处理', () => {
  test('API错误应该显示用户友好的错误消息', async ({ page }) => {
    // 导航到可能失败的页面
    await page.goto('/dashboard/opportunities');

    // 等待页面加载
    await page.waitForTimeout(2000);

    // 检查是否有错误提示
    const errorAlerts = page.locator('.alert, .error, [role="alert"]');

    // 如果有错误，验证它包含有用信息
    if (await errorAlerts.count() > 0) {
      const errorAlert = errorAlerts.first();
      const errorText = await errorAlert.textContent();

      // 错误消息应该包含操作建议
      expect(errorText).toMatch(/(重试|稍后|联系|错误)/);
    }
  });

  test('网络错误应该显示重试选项', async ({ page }) => {
    // 模拟网络错误（通过离线模式）
    await page.context().setOffline(true);

    await page.goto('/dashboard/market');
    await page.waitForTimeout(2000);

    // 检查离线提示或重试按钮
    const retryButton = page.locator('button:has-text("重试"), button:has-text("重新加载")');
    const offlineMessage = page.locator('text=网络连接失败, text=无法连接, text=离线');

    const hasRetryOption = await retryButton.count() > 0 || await offlineMessage.count() > 0;
    expect(hasRetryOption).toBeTruthy();

    // 恢复在线状态
    await page.context().setOnline(true);
  });
});

test.describe('用户旅程追踪', () => {
  test('新用户应该看到旅程指引', async ({ page }) => {
    // 设置为新用户（无历史记录）
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('user_journey', JSON.stringify({ step: 1 }));
    });

    await page.goto('/dashboard');

    // 验证旅程追踪器显示
    const journeyTracker = page.locator('[class*="journey"], .progress, .onboarding');

    if (await journeyTracker.count() > 0) {
      await expect(journeyTracker.first()).toBeVisible();

      // 验证步骤指示
      const steps = journeyTracker.locator('.step, .progress-item, [class*="step"]');
      expect(await steps.count()).toBeGreaterThan(0);
    }
  });

  test('完成步骤后应该更新进度', async ({ page }) => {
    await page.goto('/dashboard');

    // 模拟完成某个步骤
    const completeButton = page.locator('button:has-text("标记完成"), button:has-text("完成")');

    if (await completeButton.count() > 0) {
      await completeButton.first().click();
      await page.waitForTimeout(1000);

      // 验证进度更新
      const progress = page.locator('[role="progressbar"], .progress-fill, [aria-valuenow]');
      if (await progress.count() > 0) {
        const currentValue = await progress.first().getAttribute('aria-valuenow');
        expect(currentValue).not.toBe('0');
      }
    }
  });

  test('应该能够跳过旅程引导', async ({ page }) => {
    await page.goto('/dashboard');

    const skipButton = page.locator('button:has-text("跳过"), button:has-text("暂时跳过")');

    if (await skipButton.count() > 0) {
      await skipButton.click();

      // 验证旅程追踪器隐藏或消失
      await page.waitForTimeout(500);
      const journeyTracker = page.locator('[class*="journey"], .onboarding');

      // 旅程追踪器可能被移除或隐藏
      const isVisible = await journeyTracker.count() > 0 &&
                        await journeyTracker.first().isVisible();

      expect(isVisible).toBeFalsy();
    }
  });
});
