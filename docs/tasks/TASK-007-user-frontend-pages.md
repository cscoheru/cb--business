# TASK-007: 用户前端核心页面开发

> **所属会话**: 会话1（前端开发线）
> **优先级**: P0（最高）
> **预计工期**: 5天
> **依赖任务**: TASK-001（前端项目初始化）, TASK-004（认证系统）
> **创建日期**: 2025-03-10
> **状态**: ⏳ 待开始

---

## 任务目标

开发用户前端的核心页面，包括首页、定价页、Dashboard、市场概览页、机会发现页、风险预警页等，实现完整的用户界面。

---

## 页面清单

| 页面 | 路由 | 访问权限 | 优先级 |
|------|------|----------|--------|
| 首页 | / | 公开 | P0 |
| 定价页 | /pricing | 公开 | P0 |
| Dashboard | /dashboard | 需登录 | P0 |
| 市场概览 | /dashboard/market | 需登录 | P1 |
| 机会发现 | /dashboard/opportunities | 需登录，Pro+ | P0 |
| 风险预警 | /dashboard/risks | 需登录，Pro+ | P0 |
| 政策中心 | /dashboard/policies | 需登录，Pro+ | P1 |
| 工具集 | /dashboard/tools | 需登录，Pro+ | P0 |
| 设置 | /dashboard/settings | 需登录 | P1 |

---

## 核心页面设计

### 首页 (/)

```typescript
// frontend/app/page.tsx
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Link from 'next/link';

export default function HomePage() {
  return (
    <>
      <Header />

      {/* Hero Section */}
      <section className="py-20 text-center bg-gradient-to-b from-primary/10">
        <h1 className="text-5xl font-bold mb-6">
          发现跨境电商新机会
        </h1>
        <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
          AI驱动的市场洞察，帮你在东南亚、欧美、拉美市场找到蓝海
        </p>
        <div className="flex gap-4 justify-center">
          <Button size="lg" asChild>
            <Link href="/pricing">免费开始</Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="/dashboard">查看Demo</Link>
          </Button>
        </div>
      </section>

      {/* Features */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">
            核心功能
          </h2>
          <div className="grid md:grid-cols-4 gap-6">
            {features.map((feature) => (
              <FeatureCard key={feature.title} {...feature} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-muted">
        <div className="container mx-auto px-4 text-center">
          <Button size="lg">立即免费注册</Button>
        </div>
      </section>

      <Footer />
    </>
  );
}
```

### 定价页 (/pricing)

```typescript
// frontend/app/pricing/page.tsx
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Check } from 'lucide-react';

const plans = [
  {
    name: "免费版",
    price: "¥0",
    period: "/月",
    features: [
      { name: "基础市场数据", included: true },
      { name: "每日5次API调用", included: true },
      { name: "社区支持", included: true },
      { name: "AI机会分析", included: false },
      { name: "成本计算器", included: false },
      { name: "数据导出", included: false },
    ],
    cta: "免费注册",
    highlighted: false,
  },
  {
    name: "专业版",
    price: "¥99",
    period: "/月",
    features: [
      { name: "全部市场数据", included: true },
      { name: "无限API调用", included: true },
      { name: "AI机会分析", included: true },
      { name: "风险预警", included: true },
      { name: "成本计算器", included: true },
      { name: "Excel导出", included: true },
      { name: "邮件支持", included: true },
    ],
    cta: "开始试用",
    highlighted: true,
    badge: "最受欢迎",
  },
];

export default function PricingPage() {
  return (
    <div className="container mx-auto px-4 py-16">
      <h1 className="text-4xl font-bold text-center mb-4">选择适合您的计划</h1>
      <p className="text-center text-muted-foreground mb-12">
        随时取消，无隐藏费用
      </p>

      <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {plans.map((plan) => (
          <PricingCard key={plan.name} plan={plan} />
        ))}
      </div>
    </div>
  );
}

function PricingCard({ plan }) {
  return (
    <Card className={`p-8 ${plan.highlighted ? 'border-primary border-2' : ''}`}>
      {plan.badge && (
        <div className="text-center mb-4">
          <span className="bg-primary text-primary-foreground px-3 py-1 rounded-full text-sm">
            {plan.badge}
          </span>
        </div>
      )}
      <h3 className="text-2xl font-bold text-center mb-2">{plan.name}</h3>
      <div className="text-center mb-6">
        <span className="text-4xl font-bold">{plan.price}</span>
        <span className="text-muted-foreground">{plan.period}</span>
      </div>
      <ul className="space-y-3 mb-8">
        {plan.features.map((feature) => (
          <li key={feature.name} className="flex items-center gap-2">
            {feature.included ? (
              <Check className="text-primary h-5 w-5" />
            ) : (
              <span className="h-5 w-5" />
            )}
            <span className={feature.included ? '' : 'text-muted-foreground'}>
              {feature.name}
            </span>
          </li>
        ))}
      </ul>
      <Button
        className="w-full"
        variant={plan.highlighted ? 'default' : 'outline'}
        asChild
      >
        <Link href="/dashboard">{plan.cta}</Link>
      </Button>
    </Card>
  );
}
```

### Dashboard (/dashboard)

```typescript
// frontend/app/dashboard/page.tsx
import { Card } from '@/components/ui/card';
import { useUser } from '@/hooks/use-user';

export default function DashboardPage() {
  const { user } = useUser();

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">
          早上好，{user?.name || '用户'}！
        </h1>
        <p className="text-muted-foreground">
          今天有 <span className="text-primary font-bold">3个</span> 新机会等待您
        </p>
      </div>

      {/* 用户旅程追踪 */}
      <JourneyTracker />

      {/* 快捷操作 */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <QuickActionCard
          icon="🔍"
          title="发现机会"
          description="查看AI推荐的新机会"
          href="/dashboard/opportunities"
        />
        <QuickActionCard
          icon="⚠️"
          title="风险预警"
          description="查看最新风险提示"
          href="/dashboard/risks"
        />
        <QuickActionCard
          icon="💰"
          title="成本计算"
          description="计算产品成本和利润"
          href="/dashboard/tools/cost-calculator"
        />
      </div>

      {/* 推荐机会 */}
      <section>
        <h2 className="text-2xl font-bold mb-4">为您推荐</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <OpportunityCard />
          <OpportunityCard />
        </div>
      </section>
    </div>
  );
}
```

### 付费引导组件

```typescript
// frontend/components/upsell/FeatureUnlockModal.tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Check } from 'lucide-react';

interface FeatureUnlockModalProps {
  feature: string;
  open: boolean;
  onUpgrade: () => void;
  onClose: () => void;
}

export function FeatureUnlockModal({
  feature,
  open,
  onUpgrade,
  onClose
}: FeatureUnlockModalProps) {
  const content = {
    cost_calculator: {
      title: "解锁精确成本计算器",
      description: "您正在深入调研，精确的成本分析能帮您做出更好的决策",
      benefits: [
        "多维度成本计算（含税费、物流、仓储）",
        "不同物流方案对比",
        "历史记录保存",
        "一键导出Excel"
      ]
    },
    supplier_database: {
      title: "解锁供应商数据库",
      description: "找到可靠供应商是成功的关键一步",
      benefits: [
        "10,000+ verified suppliers",
        "直接联系方式",
        "MOQ和价格区间",
        "供应商评分和评价"
      ]
    },
  }[feature] || content.cost_calculator;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{content.title}</DialogTitle>
          <DialogDescription>{content.description}</DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <h4 className="font-semibold mb-3">专业版功能：</h4>
          <ul className="space-y-2">
            {content.benefits.map((benefit) => (
              <li key={benefit} className="flex items-start gap-2">
                <Check className="text-primary h-5 w-5 mt-0.5" />
                <span>{benefit}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-muted p-4 rounded-lg mb-4">
          <div className="flex items-baseline justify-center gap-1">
            <span className="text-3xl font-bold">¥99</span>
            <span className="text-muted-foreground">/月</span>
          </div>
          <p className="text-sm text-center text-muted-foreground mt-1">
            随时取消，无隐藏费用
          </p>
        </div>

        <div className="flex gap-3">
          <Button variant="outline" className="flex-1" onClick={onClose}>
            以后再说
          </Button>
          <Button className="flex-1" onClick={onUpgrade}>
            立即升级
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

---

## 组件库

### 布局组件
- Header.tsx - 顶部导航
- Footer.tsx - 页脚
- Sidebar.tsx - 侧边栏

### Dashboard组件
- JourneyTracker.tsx - 用户旅程追踪
- OpportunityCard.tsx - 机会卡片
- RiskAlertCard.tsx - 风险预警卡片
- QuickActionCard.tsx - 快捷操作卡片

### 通用组件
- LoadingSpinner.tsx - 加载状态
- EmptyState.tsx - 空状态
- ErrorBoundary.tsx - 错误边界

---

## API集成

```typescript
// frontend/hooks/use-user.ts
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

export function useUser() {
  return useQuery({
    queryKey: ['user'],
    queryFn: () => apiClient.get('/api/v1/users/me'),
  });
}

// frontend/hooks/use-opportunities.ts
export function useOpportunities(filters?: {}) {
  return useQuery({
    queryKey: ['opportunities', filters],
    queryFn: () => apiClient.post('/api/v1/opportunities/search', filters),
  });
}
```

---

## 提交规范

```bash
git commit -m "feat(TASK-007): 实现用户前端核心页面

- 实现首页（Hero + Features + CTA）
- 实现定价页（3档对比）
- 实现Dashboard主页
- 实现付费引导模态框
- 创建用户旅程追踪组件
- 实现机会卡片和风险预警卡片
- 集成用户认证
- 添加API数据hooks

页面列表:
- / 首页
- /pricing 定价页
- /dashboard Dashboard
- /dashboard/opportunities 机会发现
- /dashboard/risks 风险预警

组件库:
- 布局组件
- Dashboard组件
- 付费引导组件

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

*本任务书由主会话（项目经理）创建和维护*
