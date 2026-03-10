# TASK-008: 管理后台核心页面开发

> **所属会话**: 会话1（前端开发线）
> **优先级**: P1
> **预计工期**: 4天
> **依赖任务**: TASK-001（管理后台初始化）, TASK-004（认证系统）
> **创建日期**: 2025-03-10
> **状态**: ⏳ 待开始

---

## 任务目标

开发管理后台的核心页面，包括用户管理、订阅管理、财务报表、内容管理等平台管理功能。

---

## 页面清单

| 页面 | 路由 | 访问权限 | 优先级 |
|------|------|----------|--------|
| 后台首页 | / | 管理员 | P0 |
| 用户管理 | /users | 管理员 | P0 |
| 订阅管理 | /subscriptions | 管理员 | P0 |
| 财务报表 | /finance | 管理员 | P1 |
| 内容管理 | /content | 管理员 | P1 |
| 数据分析 | /analytics | 管理员 | P1 |

---

## 核心页面设计

### 用户管理

```typescript
// admin/app/users/page.tsx
'use client';

import { DataTable } from '@/components/users/data-table';
import { columns } from '@/components/users/columns';
import { useUsers } from '@/hooks/use-users';

export default function UsersPage() {
  const { data, isLoading } = useUsers();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">用户管理</h1>
        <Button>导出数据</Button>
      </div>

      <DataTable columns={columns} data={data?.users || []} />
    </div>
  );
}
```

### 订阅管理

```typescript
// admin/app/subscriptions/page.tsx
'use client';

import { Card } from '@/components/ui/card';
import { useSubscriptions } from '@/hooks/use-subscriptions';

export default function SubscriptionsPage() {
  const { data } = useSubscriptions();

  const stats = [
    { label: "总订阅数", value: data?.total || 0 },
    { label: "活跃订阅", value: data?.active || 0 },
    { label: "专业版", value: data?.pro || 0 },
    { label: "企业版", value: data?.enterprise || 0 },
    { label: "本月收入", value: `¥${data?.revenue || 0}` },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">订阅管理</h1>

      <div className="grid md:grid-cols-5 gap-4 mb-8">
        {stats.map((stat) => (
          <Card key={stat.label} className="p-6">
            <div className="text-sm text-muted-foreground">{stat.label}</div>
            <div className="text-2xl font-bold">{stat.value}</div>
          </Card>
        ))}
      </div>

      <SubscriptionTable data={data?.subscriptions || []} />
    </div>
  );
}
```

### 财务报表

```typescript
// admin/app/finance/page.tsx
'use client';

import { RevenueChart } from '@/components/finance/revenue-chart';
import { SubscriptionChart } from '@/components/finance/subscription-chart';
import { useFinanceData } from '@/hooks/use-finance';

export default function FinancePage() {
  const { data } = useFinanceData();

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">财务报表</h1>

      <div className="grid md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="font-semibold mb-4">月度收入</h3>
          <RevenueChart data={data?.monthlyRevenue || []} />
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold mb-4">订阅趋势</h3>
          <SubscriptionChart data={data?.subscriptionTrend || []} />
        </Card>
      </div>

      <Card className="mt-6 p-6">
        <h3 className="font-semibold mb-4">支付方式分布</h3>
        <PaymentMethodChart data={data?.paymentMethods || []} />
      </Card>
    </div>
  );
}
```

---

## 组件库

### 表格组件
- UsersTable.tsx - 用户表格
- SubscriptionsTable.tsx - 订阅表格
- PaymentsTable.tsx - 支付记录表格

### 图表组件
- RevenueChart.tsx - 收入图表
- SubscriptionChart.tsx - 订阅趋势图
- UserGrowthChart.tsx - 用户增长图

### 通用组件
- StatCard.tsx - 统计卡片
- DateRangePicker.tsx - 日期选择器
- ExportButton.tsx - 导出按钮

---

## Admin API

```typescript
// admin/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const adminApiClient = {
  // 用户管理
  async getUsers(filters: {}) {
    return fetch(`${API_BASE_URL}/api/v1/admin/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(filters),
    }).then(r => r.json());
  },

  // 订阅管理
  async getSubscriptions(filters: {}) {
    return fetch(`${API_BASE_URL}/api/v1/admin/subscriptions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(filters),
    }).then(r => r.json());
  },

  // 财务数据
  async getFinanceData(period: string) {
    return fetch(`${API_BASE_URL}/api/v1/admin/finance?period=${period}`)
      .then(r => r.json());
  },
};
```

---

## 提交规范

```bash
git commit -m "feat(TASK-008): 实现管理后台核心页面

- 实现用户管理页面（表格+筛选）
- 实现订阅管理页面（统计+表格）
- 实现财务报表页面（图表）
- 创建管理员认证
- 添加数据导出功能

页面列表:
- / 后台首页
- /users 用户管理
- /subscriptions 订阅管理
- /finance 财务报表
- /analytics 数据分析

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

*本任务书由主会话（项目经理）创建和维护*
