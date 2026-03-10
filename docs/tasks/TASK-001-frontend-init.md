# TASK-001: 前端项目初始化

> **所属会话**: 会话1（前端开发线）
> **优先级**: P0（最高）
> **预计工期**: 1天
> **依赖任务**: TASK-002（后端项目初始化）
> **创建日期**: 2025-03-10
> **状态**: ⏳ 待开始

---

## 任务目标

创建两个Next.js 15项目（用户前端和管理后台），配置shadcn/ui组件库，搭建基础项目结构，实现基础布局和路由，为后续页面开发做好准备。

---

## 背景信息

**项目上下文**：
- 这是一个面向国内跨境电商创业者的SaaS平台
- 采用 Freemium 工具型商业模式
- 前端使用 Next.js 15 App Router + shadcn/ui

**双前端架构**：
- **用户前端** (`cb.3strategy.cc`): 面向创业者的主站
- **管理后台** (`admin.cb.3strategy.cc`): 面向平台管理的后台

**依赖说明**：
本任务依赖 TASK-002 完成的：
- 后端API已启动
- 健康检查端点可访问

**为什么需要这个任务**：
前端项目初始化是所有UI开发的基础，需要建立项目结构、配置组件库、实现基础布局。

---

## 验收标准

### 用户前端 (frontend/)
- [ ] Next.js 15项目创建完成
- [ ] App Router配置正确
- [ ] TypeScript配置完成
- [ ] Tailwind CSS配置完成
- [ ] shadcn/ui组件库安装完成
- [ ] 基础布局组件（Header, Footer, Layout）
- [ ] 首页和定价页基础结构
- [ ] 与后端API可通信

### 管理后台 (admin/)
- [ ] Next.js 15项目创建完成
- [ ] App Router配置正确
- [ ] TypeScript配置完成
- [ ] Tailwind CSS配置完成
- [ ] shadcn/ui组件库安装完成
- [ ] 基础布局组件
- [ ] 登录页和Dashboard基础结构

### 共享配置
- [ ] 两个项目可同时运行（不同端口）
- [ ] 共享类型定义（如果有）
- [ ] ESLint和Prettier配置完成

---

## 技术要求

### 技术栈
```
- Next.js 15 (App Router)
- React 18
- TypeScript 5
- Tailwind CSS 3
- shadcn/ui (基于Radix UI)
- Lucide React (图标)
- Recharts (图表)
- next-intl (国际化，可选)
```

### 项目结构

```
/Users/kjonekong/Documents/cb-Business/
├── frontend/                    # 用户前端
│   ├── app/                    # Next.js App Router
│   │   ├── (routes)/           # 路由组
│   │   │   ├── page.tsx        # 首页
│   │   │   ├── pricing/        # 定价页
│   │   │   ├── dashboard/      # Dashboard（需登录）
│   │   │   └── layout.tsx      # 布局
│   │   ├── api/                # API代理
│   │   ├── layout.tsx          # 根布局
│   │   └── globals.css         # 全局样式
│   ├── components/             # 组件
│   │   ├── ui/                 # shadcn/ui组件
│   │   ├── layout/             # 布局组件
│   │   ├── dashboard/          # Dashboard组件
│   │   └── pricing/            # 定价组件
│   └── lib/                    # 工具库
│       ├── api.ts              # API客户端
│       └── utils.ts            # 工具函数
│
└── admin/                      # 管理后台
    ├── app/                    # Next.js App Router
    │   ├── (routes)/
    │   │   ├── page.tsx        # 后台首页
    │   │   ├── users/          # 用户管理
    │   │   ├── subscriptions/  # 订阅管理
    │   │   └── layout.tsx
    │   ├── layout.tsx
    │   └── globals.css
    ├── components/
    │   ├── ui/
    │   ├── users-table.tsx
    │   └── subscription-chart.tsx
    └── lib/
        └── api.ts
```

### 端口配置

| 项目 | 开发端口 | 生产域名 |
|------|----------|----------|
| 用户前端 | 3000 | cb.3strategy.cc |
| 管理后台 | 3001 | admin.cb.3strategy.cc |
| 后端API | 8000 | api.cb.3strategy.cc |

---

## 参考资料

**主计划文档**：
`/Users/kjonekong/.claude/plans/pure-crunching-lantern.md`

**后端API**：
- 健康检查：http://localhost:8000/health
- API文档：http://localhost:8000/docs

**技术文档**：
- Next.js 15: https://nextjs.org/docs
- shadcn/ui: https://ui.shadcn.com/
- Tailwind CSS: https://tailwindcss.com/docs

---

## 开发指南

### 步骤1：创建用户前端项目

```bash
# 进入项目目录
cd /Users/kjonekong/Documents/cb-Business

# 创建Next.js项目（用户前端）
npx create-next-app@latest frontend --typescript --tailwind --app --src-dir=false --import-alias="@/*"

# 配置选项确认：
# ✔ TypeScript: Yes
# ✔ ESLint: Yes
# ✔ Tailwind CSS: Yes
# ✔ `src/` directory: No (使用app目录)
# ✔ App Router: Yes
# ✔ Customize default import alias (@/*): Yes

# 进入项目目录
cd frontend

# 安装额外依赖
npm install @radix-ui/react-icons lucide-react recharts
npm install class-variance-authority clsx tailwind-merge

# 初始化shadcn/ui
npx shadcn-ui@latest init

# 配置选项：
# ✔ Style: Default
# ✔ Base color: Slate
# ✔ CSS variables: Yes

# 添加常用的shadcn/ui组件
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add input
npx shadcn-ui@latest add form
```

### 步骤2：配置用户前端

```typescript
// frontend/lib/utils.ts
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

```typescript
// frontend/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = {
  async get(endpoint: string) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) throw new Error('API request failed');
    return response.json();
  },

  async post(endpoint: string, data: any) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('API request failed');
    return response.json();
  },
};
```

```css
/* frontend/app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 48%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

### 步骤3：创建布局组件

```typescript
// frontend/components/layout/Header.tsx
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export function Header() {
  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <Link href="/" className="text-xl font-bold">
          CB Business
        </Link>
        <nav className="flex items-center gap-6">
          <Link href="/pricing">定价</Link>
          <Link href="/dashboard">Dashboard</Link>
          <Button variant="outline" size="sm">
            登录
          </Button>
          <Button size="sm">
            免费注册
          </Button>
        </nav>
      </div>
    </header>
  );
}
```

```typescript
// frontend/components/layout/Footer.tsx
export function Footer() {
  return (
    <footer className="border-t mt-20">
      <div className="container mx-auto px-4 py-8 text-center text-muted-foreground">
        <p>© 2025 Cross-Border Business. All rights reserved.</p>
      </div>
    </footer>
  );
}
```

### 步骤4：创建首页

```typescript
// frontend/app/page.tsx
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export default function HomePage() {
  return (
    <>
      {/* Hero Section */}
      <section className="py-20 text-center">
        <div className="container mx-auto px-4">
          <h1 className="text-5xl font-bold mb-6">
            发现跨境电商新机会
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            AI驱动的市场洞察，帮你在东南亚、欧美、拉美市场找到蓝海
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg">免费开始</Button>
            <Button size="lg" variant="outline">查看演示</Button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">
            为什么选择我们
          </h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { icon: "🔍", title: "机会发现", desc: "AI分析市场趋势" },
              { icon: "⚠️", title: "风险预警", desc: "实时政策监控" },
              { icon: "📋", title: "实操指南", desc: "详细操作手册" },
              { icon: "💰", title: "成本计算", desc: "精确利润分析" },
            ].map((feature) => (
              <Card key={feature.title} className="p-6">
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.desc}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-muted">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">
            开始你的跨境电商之旅
          </h2>
          <Button size="lg">免费注册</Button>
        </div>
      </section>
    </>
  );
}
```

### 步骤5：创建管理后台项目

```bash
# 回到项目根目录
cd /Users/kjonekong/Documents/cb-Business

# 创建管理后台项目
npx create-next-app@latest admin --typescript --tailwind --app --src-dir=false --import-alias="@/*"

cd admin

# 安装依赖（与用户前端相同）
npm install @radix-ui/react-icons lucide-react recharts
npm install class-variance-authority clsx tailwind-merge

# 初始化shadcn/ui
npx shadcn-ui@latest init

# 添加组件
npx shadcn-ui@latest add button card dialog input table
```

### 步骤6：配置管理后台

```typescript
// admin/lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const adminApiClient = {
  async get(endpoint: string, token?: string) {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(`${API_BASE_URL}${endpoint}`, { headers });
    if (!response.ok) throw new Error('API request failed');
    return response.json();
  },
  // ... 其他方法
};
```

```typescript
// admin/app/page.tsx
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export default function AdminHomePage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">管理后台</h1>

      <div className="grid md:grid-cols-3 gap-6">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-2">用户管理</h2>
          <p className="text-muted-foreground mb-4">查看和管理平台用户</p>
          <Button asChild><Link href="/users">管理用户</Link></Button>
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-2">订阅管理</h2>
          <p className="text-muted-foreground mb-4">查看订阅和支付记录</p>
          <Button asChild><Link href="/subscriptions">管理订阅</Link></Button>
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-2">数据分析</h2>
          <p className="text-muted-foreground mb-4">查看平台数据统计</p>
          <Button asChild><Link href="/analytics">查看数据</Link></Button>
        </Card>
      </div>
    </div>
  );
}
```

### 步骤7：配置环境变量

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

```bash
# admin/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 步骤8：配置同时运行

```bash
# 创建启动脚本
cat > /Users/kjonekong/Documents/cb-Business/dev.sh << 'EOF'
#!/bin/bash

# 启动开发环境

echo "Starting development environment..."

# 启动后端（在backend目录）
cd /Users/kjonekong/Documents/cb-Business/backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# 等待后端启动
sleep 3

# 启动前端
cd /Users/kjonekong/Documents/cb-Business/frontend
npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID) on http://localhost:3000"

# 启动管理后台
cd /Users/kjonekong/Documents/cb-Business/admin
PORT=3001 npm run dev &
ADMIN_PID=$!
echo "Admin started (PID: $ADMIN_PID) on http://localhost:3001"

echo ""
echo "All services started:"
echo "  - Frontend:  http://localhost:3000"
echo "  - Admin:     http://localhost:3001"
echo "  - Backend:   http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"

# 捕获Ctrl+C，停止所有服务
trap "kill $BACKEND_PID $FRONTEND_PID $ADMIN_PID; exit" INT

# 等待所有后台进程
wait
EOF

chmod +x /Users/kjonekong/Documents/cb-Business/dev.sh
```

---

## 测试要求

### 启动测试
```bash
# 使用启动脚本
/Users/kjonekong/Documents/cb-Business/dev.sh

# 或分别启动
# Terminal 1: 后端
cd backend && source venv/bin/activate && python main.py

# Terminal 2: 前端
cd frontend && npm run dev

# Terminal 3: 管理后台
cd admin && PORT=3001 npm run dev
```

### 访问测试
在浏览器中打开：
- http://localhost:3000 - 用户前端
- http://localhost:3001 - 管理后台
- http://localhost:8000/docs - 后端API文档

### 验证清单
- [ ] 用户前端首页正常显示
- [ ] 管理后台首页正常显示
- [ ] shadcn/ui组件可正常使用
- [ ] 前端可以调用后端API
- [ ] 样式（Tailwind）正常应用
- [ ] TypeScript无类型错误
- [ ] 两个项目可同时运行

---

## 提交规范

```bash
cd /Users/kjonekong/Documents/cb-Business

# 添加所有文件
git add frontend/ admin/ dev.sh

# 提交
git commit -m "feat(TASK-001): 完成前端项目初始化

- 创建用户前端Next.js项目
- 创建管理后台Next.js项目
- 配置shadcn/ui组件库
- 创建基础布局组件
- 实现首页和管理后台首页
- 配置API客户端
- 添加开发环境启动脚本

项目结构:
- frontend/ 用户前端（端口3000）
- admin/ 管理后台（端口3001）

技术栈:
- Next.js 15 (App Router)
- TypeScript 5
- Tailwind CSS 3
- shadcn/ui (Radix UI)
- Lucide React

验收:
- ✅ 两个项目可正常运行
- ✅ 首页显示正常
- ✅ shadcn/ui组件可用
- ✅ 与后端API可通信
- ✅ 开发脚本可同时启动所有服务

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 进度更新

**开始时间**: [填写开始时间]

**进度记录**:
- [ ] 创建用户前端项目
- [ ] 配置shadcn/ui
- [ ] 创建布局组件
- [ ] 实现首页
- [ ] 创建管理后台项目
- [ ] 配置管理后台
- [ ] 配置API客户端
- [ ] 创建启动脚本

**完成时间**: [填写完成时间]

---

## 问题记录

| 问题描述 | 发现时间 | 解决方案 | 状态 |
|----------|----------|----------|------|
| （如有问题记录在这里） | | | |

---

## 注意事项

1. **端口冲突**：
   - 确保3000和3001端口未被占用
   - 如有冲突，修改admin的端口配置

2. **API配置**：
   - 确保后端已启动（TASK-002完成）
   - 环境变量NEXT_PUBLIC_API_URL配置正确

3. **依赖安装**：
   - npm install可能需要一些时间
   - 如遇网络问题，可使用cnpm或yarn

---

## 下一步

完成本任务后，可以继续：
- **TASK-007**: 用户前端核心页面开发
- **TASK-008**: 管理后台核心页面开发

*本任务书由主会话（项目经理）创建和维护*
