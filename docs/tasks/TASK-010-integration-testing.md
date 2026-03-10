# TASK-010: 集成测试

> **所属会话**: 会话2（后端开发线）配合会话1（前端开发线）
> **优先级**: P0（最高）
> **预计工期**: 2天
> **依赖任务**: 所有前端和后端任务
> **创建日期**: 2025-03-10
> **状态**: ⏳ 待开始

---

## 任务目标

进行全面的集成测试，验证前后端联调、支付流程、订阅流程等核心功能，确保系统可以正常运行。

---

## 测试清单

### 用户认证流程
- [ ] 用户注册 → 自动登录
- [ ] 用户登录 → 获取Token
- [ ] Token过期 → 重新登录
- [ ] 获取用户信息

### 订阅流程
- [ ] 创建订阅 → 支付订单
- [ ] 支付成功 → 订阅激活
- [ ] 付费功能解锁
- [ ] 使用限额控制

### 支付流程
- [ ] 创建支付订单 → 生成二维码
- [ ] 支付回调处理
- [ ] 订阅状态更新
- [ ] 支付记录查询

### 前后端联调
- [ ] API调用正常
- [ ] 数据展示正确
- [ ] 错误处理正常
- [ ] 加载状态正常

---

## 测试脚本

```python
# tests/test_integration.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
class TestAuthFlow:
    """测试认证流程"""

    async def test_register_login_flow(self, client: AsyncClient):
        # 注册
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "password123",
            "name": "测试用户"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]

        token = data["data"]["access_token"]

        # 获取用户信息
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["data"]["email"] == "test@example.com"

@pytest.mark.asyncio
class TestSubscriptionFlow:
    """测试订阅流程"""

    async def test_create_subscription(self, client: AsyncClient, token: str):
        response = await client.post(
            "/api/v1/subscriptions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "plan_tier": "pro",
                "billing_cycle": "monthly"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["plan_tier"] == "pro"
```

---

## E2E测试（前端）

```typescript
// frontend/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('用户认证', () => {
  test('注册新用户', async ({ page }) => {
    await page.goto('/register');

    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.fill('input[name="name"]', '测试用户');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
  });

  test('登录', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
  });
});
```

---

## 提交规范

```bash
git commit -m "test(TASK-010): 完成集成测试

- 编写认证流程测试
- 编写订阅流程测试
- 编写支付流程测试
- 编写E2E测试
- 修复发现的问题

测试覆盖:
- 用户认证
- 订阅管理
- 支付集成
- 前后端联调

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

*本任务书由主会话（项目经理）创建和维护*
