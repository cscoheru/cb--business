# 认证系统前端集成设计方案

> **日期**: 2026-03-13
> **优先级**: P0（最高）
> **目标**: 让用户能够真正登录注册，打通前后端认证流程

---

## 📋 现状分析

### ✅ 已完成部分

| 组件 | 文件 | 状态 |
|------|------|------|
| AuthContext | `/lib/auth-context.tsx` | ✅ 已实现 |
| 登录页面 | `/app/login/page.tsx` | ✅ 已实现 |
| 注册页面 | `/app/register/page.tsx` | ✅ 已实现 |
| ProtectedRoute | `/components/auth/ProtectedRoute.tsx` | ✅ 已实现 |
| authApi 函数 | `/lib/api.ts` | ✅ 已实现 |
| AuthProvider | `/components/providers/Providers.tsx` | ✅ 已集成 |

### ⚠️ 需要修复的问题

| 问题 | 影响 | 优先级 |
|------|------|--------|
| Token 存储键不一致 | token 可能丢失 | P0 |
| 缺少 token 自动验证 | 可能使用过期 token | P0 |
| 登录后跳转到 dashboard | UX 不佳 | P1 |
| 导航栏未显示用户状态 | 无法看到登录状态 | P1 |

---

## 🎯 设计方案

### 1. Token 存储统一

**问题**: `auth-context.tsx` 使用 `token` 键，但 `api.ts` 使用 `auth_token` 键

**解决方案**: 统一使用 `auth_token` 作为键名

**修改文件**:
- `/lib/auth-context.tsx`
- `/components/providers/Providers.tsx`

**修改内容**:
```typescript
// 修改前
localStorage.setItem('token', response.access_token);
localStorage.getItem('token');

// 修改后
localStorage.setItem('auth_token', response.access_token);
localStorage.getItem('auth_token');
```

### 2. Token 自动验证

**用户选择**: 自动验证 token 有效性

**实现方案**: 在 AuthProvider 初始化时调用 `/api/v1/users/me` 验证 token

**流程**:
```
应用启动
  ↓
从 localStorage 读取 auth_token
  ↓
调用 GET /api/v1/users/me (带 token)
  ↓
┌─────────────┬──────────────────────────────┐
│ Token 有效   │ Token 无效/过期             │
├─────────────┼──────────────────────────────┤
│ 设置 user    │ 清除 localStorage           │
│ 设置 token   │ user = null                 │
│ isLoading = false │ token = null               │
│              │ isLoading = false             │
└─────────────┴──────────────────────────────┘
```

**修改文件**: `/lib/auth-context.tsx`

### 3. 登录后行为优化

**用户选择**: 停留在当前页面

**实现方案**:
1. 登录前记录当前路径
2. 登录成功后跳转回原路径
3. 如果原路径是 /login 或 /register，跳转到 /cards

**修改文件**: `/lib/auth-context.tsx`

### 4. 导航栏状态显示

**需要实现**:
- 未登录: 显示 "登录" 和 "注册" 按钮
- 已登录: 显示用户头像/名称、下拉菜单（登出、我的收藏、设置等）

**修改文件**: `/components/layout/Header.tsx`

---

## 📁 文件修改清单

### 必须修改 (P0)

| 文件 | 修改内容 | 预计时间 |
|------|----------|----------|
| `lib/auth-context.tsx` | Token 键统一、自动验证、跳转优化 | 20分钟 |
| `components/providers/Providers.tsx` | 移除 FavoritesProvider（后续单独处理） | 5分钟 |

### 建议修改 (P1)

| 文件 | 修改内容 | 预计时间 |
|------|----------|----------|
| `components/layout/Header.tsx` | 显示用户登录状态、登出功能 | 30分钟 |
| `app/dashboard/page.tsx` | 创建用户面板或重定向到首页 | 15分钟 |

---

## 🔐 安全考虑

1. **Token 过期处理**: API 返回 401 时自动清除本地存储并跳转登录
2. **XSS 防护**: 使用 React 的 `textContent` 而非 `innerHTML` 显示用户输入
3. **HTTPS Only**: 生产环境强制 HTTPS 传输 token
4. **Token 刷新**: 后端返回的 token 应该有合理的过期时间

---

## 📊 数据流设计

```
┌─────────────────────────────────────────────────────────────┐
│                    用户操作流程                              │
└─────────────────────────────────────────────────────────────┘

1. 注册流程
   用户填写表单 → POST /api/v1/auth/register
   → 返回 access_token + user
   → 存储 localStorage (auth_token, user)
   → 停留在当前页面

2. 登录流程
   用户填写表单 → POST /api/v1/auth/login
   → 返回 access_token + user
   → 存储 localStorage (auth_token, user)
   → 停留在当前页面

3. 自动登录 (刷新页面)
   应用启动 → 读取 localStorage auth_token
   → GET /api/v1/users/me (带 token)
   → 成功: 设置 user state / 失败: 清除 localStorage

4. 登出流程
   点击登出 → 清除 localStorage
   → user = null, token = null
   → 停留在当前页面
```

---

## 🧪 测试计划

### 功能测试

- [ ] 注册新用户 - 验证数据库创建成功
- [ ] 登录已注册用户 - 验证 token 正确存储
- [ ] 刷新页面后保持登录状态 - 验证自动验证有效
- [ ] 登出功能 - 验证 localStorage 清除
- [ ] Token 过期处理 - 验证 401 时清除状态

### 边界测试

- [ ] 无 token 访问受保护页面 - 重定向到登录
- [ ] Token 过期后访问 API - 显示错误并清除
- [ ] 网络错误处理 - 显示友好的错误提示

---

## 🚀 实施步骤

### Step 1: 修复 auth-context.tsx
1. 统一 token 键为 `auth_token`
2. 添加 `verifyToken` 函数
3. 在 useEffect 中调用验证逻辑
4. 修改 login/register 成功后的跳转逻辑

### Step 2: 清理 Providers.tsx
1. 移除未实现的 FavoritesProvider
2. 只保留 AuthProvider

### Step 3: 更新 Header 组件
1. 添加用户状态显示
2. 添加登出按钮
3. 根据登录状态显示不同导航

### Step 4: 处理 dashboard 页面
1. 创建简单的用户面板
2. 或重定向到 /cards

### Step 5: 测试
1. 注册/登录功能测试
2. Token 验证测试
3. 刷新页面测试
4. 登出测试

---

## ⏱️ 预计工时

| 步骤 | 工时 |
|------|------|
| Step 1: 修复 auth-context | 20分钟 |
| Step 2: 清理 Providers | 5分钟 |
| Step 3: 更新 Header | 30分钟 |
| Step 4: 处理 dashboard | 15分钟 |
| Step 5: 测试 | 20分钟 |
| **总计** | **90分钟** |

---

## 📝 后续优化

1. **"记住我"功能**: 延长 token 有效期（需要后端支持）
2. **社交登录**: 微信/Google 第三方登录
3. **忘记密码**: 密码重置流程
4. **邮箱验证**: 注册时邮箱验证
