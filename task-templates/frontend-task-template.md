# 前端任务书模板

> **模板版本**: v1.0
> **适用于**: 会话1（前端开发线）
> **技术栈**: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui

---

# TASK-XXX: [任务名称]

> **所属会话**: 会话1（前端开发线）
> **优先级**: P0/P1/P2
> **预计工期**: X 天
> **依赖任务**: TASK-XXX（如有）
> **创建日期**: YYYY-MM-DD
> **状态**: ⏳ 待开始 / 🔄 进行中 / ✅ 已完成 / ❌ 已阻塞

---

## 任务目标

[清晰描述这个前端任务要达成的目标]

**示例**：
- 创建用户前端的首页和定价页面
- 实现用户Dashboard布局和组件
- 集成shadcn/ui组件库

---

## 背景信息

**项目上下文**：
- 这是一个面向国内跨境电商创业者的SaaS平台
- 采用 Freemium 工具型商业模式
- 前端使用 Next.js 15 App Router

**为什么需要这个任务**：
[说明这个任务在整体项目中的作用]

---

## 验收标准

- [ ] 页面/组件按设计稿完成
- [ ] 响应式设计正常（移动端 + 桌面端）
- [ ] 与后端API联调通过
- [ ] TypeScript 类型检查无错误
- [ ] 通过代码审查

---

## 技术要求

### 技术栈
```
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui (UI组件库)
- Recharts (图表)
- Lucide React (图标)
```

### 关键文件/路径
```
项目根目录: /Users/kjonekong/Documents/cb-Business/frontend/
组件目录: frontend/components/
页面目录: frontend/app/
工具目录: frontend/lib/
```

### 依赖接口

| API端点 | 方法 | 用途 | 状态 |
|---------|------|------|------|
| /api/v1/auth/login | POST | 用户登录 | ⏳ 待定义 |
| /api/v1/users/me | GET | 获取用户信息 | ⏳ 待定义 |

---

## 参考资料

**设计文档**：
- 主计划：`/Users/kjonekong/.claude/plans/pure-crunching-lantern.md`
- UI设计参考：SellerSprite（简化版）

**API文档**：
- OpenAPI规范：`/Users/kjonekong/Documents/cb-Business/docs/api/openapi.yaml`

**组件库文档**：
- shadcn/ui：https://ui.shadcn.com/
- Next.js 15：https://nextjs.org/docs

---

## 开发指南

### 步骤1：环境准备
```bash
cd /Users/kjonekong/Documents/cb-Business/frontend
npm install  # 安装依赖
npm run dev  # 启动开发服务器
```

### 步骤2：创建组件/页面
[具体的开发步骤]

### 步骤3：样式开发
- 使用 Tailwind CSS 类名
- 遵循设计规范
- 确保响应式

### 步骤4：API集成
```typescript
// 示例：API调用
import { apiClient } from '@/lib/api';

const data = await apiClient.get('/api/v1/users/me');
```

### 注意事项
1. 所有组件必须是 Server Components 优先，必要时使用 Client Components（添加 'use client'）
2. 使用 shadcn/ui 组件，不要自己重复造轮
3. 图片使用 Next.js Image 组件
4. API调用放在 Server Actions 或 API Routes 中

---

## 测试要求

### 功能测试
- [ ] 所有交互功能正常
- [ ] 表单验证正常
- [ ] 错误处理正常

### UI测试
- [ ] 桌面端（1920x1080）显示正常
- [ ] 平板端（768x1024）显示正常
- [ ] 移动端（375x667）显示正常

### 集成测试
- [ ] 与后端API联调
- [ ] 认证流程测试
- [ ] 付费功能解锁测试

---

## 提交规范

### Git提交格式
```bash
git add .
git commit -m "feat: 完成用户Dashboard页面

- 实现Dashboard布局
- 集成shadcn/ui组件
- 添加用户旅程追踪组件

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### 代码审查清单
- [ ] 代码符合 ESLint 规范
- [ ] 没有console.log调试代码
- [ ] 组件有合适的注释
- [ ] TypeScript 类型定义完整

---

## 进度更新

**开始时间**: YYYY-MM-DD HH:MM

**进度记录**:
- YYYY-MM-DD: 完成项目初始化
- YYYY-MM-DD: 完成首页开发
- ...

**完成时间**: YYYY-MM-DD HH:MM

---

## 问题记录

| 问题描述 | 发现时间 | 解决方案 | 状态 |
|----------|----------|----------|------|
| ... | ... | ... | ✅ 已解决 |

---

*本任务书由主会话（项目经理）创建和维护*
