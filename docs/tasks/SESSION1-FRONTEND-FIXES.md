# 会话1：前端修复任务清单

> **优先级**: P0（部署前必须完成）
> **预计工期**: 1-2小时
> **创建日期**: 2026-03-10
> **⚠️ 紧急补充**: 用户反馈页面链接点不开，请立即修复！

---

## 🔥 紧急问题（立即修复）⚠️

### 问题：用户点击链接无反应

**症状**:
- 首页"免费开始"、"查看演示"、"免费注册"按钮点击无反应
- Header"登录"、"免费注册"按钮点击无反应
- 缺少 `/login` 和 `/register` 页面

### 修复步骤

#### 步骤1：修复首页按钮

**文件**: `frontend/app/page.tsx`

将所有按钮包裹在 `Link` 组件中：
```tsx
// 修改前
<Button size="lg">免费开始</Button>

// 修改后
<Link href="/register">
  <Button size="lg">免费开始</Button>
</Link>
```

#### 步骤2：修复Header按钮

**文件**: `frontend/components/layout/Header.tsx`

同样用 `Link` 包裹按钮

#### 步骤3：创建登录页面

**新建**: `frontend/app/login/page.tsx`

#### 步骤4：创建注册页面

**新建**: `frontend/app/register/page.tsx`

---

## 🔴 Critical 问题（原有问题）

### 1. 修复API客户端认证头逻辑

**文件**: `frontend/lib/api.ts`

**问题**: `requiresAuth=false` 时仍然添加认证头，导致未登录用户请求失败

**当前代码**:
```typescript
async post(endpoint: string, data: any, requiresAuth = false) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: getAuthHeaders(),  // ❌ 总是添加认证头
        body: JSON.stringify(data),
    });
```

**修复后**:
```typescript
async post(endpoint: string, data: any, requiresAuth = false) {
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };

    // 只有需要认证时才添加认证头
    if (requiresAuth) {
        Object.assign(headers, getAuthHeaders());
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(data),
    });
```

**同样修复**: `get()`, `put()`, `delete()` 方法

---

### 2. 更新User类型定义

**文件**: `frontend/lib/api.ts`

**问题**: 类型定义与后端模型不匹配

**当前定义**:
```typescript
export interface User {
  id: string;
  email: string;
  name: string;
  plan_tier: 'free' | 'pro' | 'enterprise';
  plan_status: 'active' | 'suspended' | 'cancelled';  // ❌ 错误
  created_at: string;
  last_active_at: string;
  // 缺少: phone, avatar_url, region_preference, currency_preference
}
```

**修复后**:
```typescript
export interface User {
  id: string;
  email: string;
  name: string | null;
  phone: string | null;
  avatar_url: string | null;
  plan_tier: 'free' | 'pro' | 'enterprise';
  plan_status: 'active' | 'canceled' | 'expired';  // ✅ 修正
  region_preference: string | null;
  currency_preference: string;
  created_at: string;
  last_login_at: string | null;
  is_admin: boolean;  // ✅ 新增
}
```

---

## 🟠 High Priority 问题

### 3. 添加请求取消支持

**文件**: `frontend/lib/api.ts`

**问题**: 无法取消正在进行的请求

**修复**:
```typescript
export const apiClient = {
  // 添加 signal 参数
  async get(endpoint: string, requiresAuth = true, signal?: AbortSignal) {
    // ...
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'GET',
        headers,
        signal,  // ✅ 添加 signal
    });
  },

  async post(endpoint: string, data: any, requiresAuth = false, signal?: AbortSignal) {
    // ...
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(data),
        signal,  // ✅ 添加 signal
    });
  },

  // 创建 AbortController 的辅助函数
  createController(): AbortController {
    return new AbortController();
  }
};
```

**使用示例**:
```typescript
const controller = apiClient.createController();

try {
  const data = await apiClient.get('/api/data', true, controller.signal);
} catch (error) {
  if (error.name === 'AbortError') {
    console.log('Request was cancelled');
  }
}

// 取消请求
controller.abort();
```

---

### 4. 改进错误处理

**文件**: `frontend/lib/api.ts`

**问题**: 错误处理不够详细

**修复**:
```typescript
// 定义错误类型
export class APIError extends Error {
  code: string;
  status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = 'APIError';
    this.code = code;
    this.status = status;
  }
}

// 在 handleResponse 中使用
async function handleResponse(response: Response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: response.statusText,
      code: 'UNKNOWN_ERROR'
    }));

    throw new APIError(
      error.detail || 'Request failed',
      error.code || 'HTTP_ERROR',
      response.status
    );
  }

  return response.json();
}

// 使用示例
try {
  const data = await apiClient.get('/api/users/me');
} catch (error) {
  if (error instanceof APIError) {
    if (error.code === 'UNAUTHORIZED') {
      // 重定向到登录
      router.push('/login');
    } else if (error.code === 'FORBIDDEN') {
      // 显示权限错误
      showToast('没有权限访问此资源');
    }
  }
}
```

---

### 5. 添加请求重试逻辑

**文件**: `frontend/lib/api.ts`

**针对网络错误自动重试**:
```typescript
async function fetchWithRetry(
  url: string,
  options: RequestInit,
  maxRetries = 3
): Promise<Response> {
  let lastError: Error | null = null;

  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.ok || response.status < 500) {
        return response;
      }
    } catch (error) {
      lastError = error as Error;
      // 如果是网络错误，等待后重试
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
      }
    }
  }

  throw lastError || new Error('Max retries exceeded');
}

// 在 API 方法中使用
async get(endpoint: string, requiresAuth = true) {
  const headers = getHeaders(requiresAuth);

  const response = await fetchWithRetry(
    `${API_BASE_URL}${endpoint}`,
    {
      method: 'GET',
      headers,
    }
  );

  return handleResponse(response);
}
```

---

## 🟡 Medium Priority 问题（可选）

### 6. 添加请求缓存

**文件**: `frontend/lib/api.ts`

**对GET请求添加内存缓存**:
```typescript
const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5分钟

async get(endpoint: string, requiresAuth = true, useCache = true) {
  // 检查缓存
  if (useCache) {
    const cached = cache.get(endpoint);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      return cached.data;
    }
  }

  // 发起请求
  const data = await this._fetch(endpoint, 'GET', null, requiresAuth);

  // 更新缓存
  if (useCache) {
    cache.set(endpoint, { data, timestamp: Date.now() });
  }

  return data;
}

// 清除缓存
clearCache(endpoint?: string) {
  if (endpoint) {
    cache.delete(endpoint);
  } else {
    cache.clear();
  }
}
```

---

### 7. 添加请求拦截器

**文件**: `frontend/lib/api.ts`

**在请求前和响应后执行自定义逻辑**:
```typescript
type Interceptor = (config: RequestConfig) => RequestConfig;
type ResponseInterceptor = (response: any) => any;

const requestInterceptors: Interceptor[] = [];
const responseInterceptors: ResponseInterceptor[] = [];

export const apiClient = {
  // 添加请求拦截器
  addRequestInterceptor(interceptor: Interceptor) {
    requestInterceptors.push(interceptor);
  },

  // 添加响应拦截器
  addResponseInterceptor(interceptor: ResponseInterceptor) {
    responseInterceptors.push(interceptor);
  },

  async get(endpoint: string, requiresAuth = true) {
    let config = { endpoint, requiresAuth, method: 'GET' as const };

    // 执行请求拦截器
    for (const interceptor of requestInterceptors) {
      config = interceptor(config);
    }

    const response = await fetch(/* ... */);
    let data = await handleResponse(response);

    // 执行响应拦截器
    for (const interceptor of responseInterceptors) {
      data = interceptor(data);
    }

    return data;
  }
};

// 使用示例：自动添加认证token
apiClient.addRequestInterceptor((config) => {
  const token = localStorage.getItem('access_token');
  if (token && config.requiresAuth) {
    config.headers = {
      ...config.headers,
      'Authorization': `Bearer ${token}`
    };
  }
  return config;
});
```

---

## 📋 验证清单

完成所有修复后，请验证：

- [ ] 注册接口不需要认证可以调用
- [ ] 登录接口正常工作
- [ ] 未登录访问受保护API时正确处理401错误
- [ ] User类型定义与后端一致
- [ ] 请求可以正常取消
- [ ] 网络错误时有重试机制
- [ ] 错误信息清晰明确

---

## 🧪 测试场景

### 场景1：注册流程
```typescript
// 不需要认证
const response = await apiClient.post('/api/v1/auth/register', {
  email: 'test@example.com',
  password: 'password123',
  name: '测试用户'
}, false);  // requiresAuth = false
```

### 场景2：登录后获取用户信息
```typescript
// 登录
const loginResponse = await apiClient.post('/api/v1/auth/login', {
  email: 'test@example.com',
  password: 'password123'
}, false);

// 保存token
localStorage.setItem('access_token', loginResponse.access_token);

// 获取用户信息（需要认证）
const user = await apiClient.get('/api/v1/users/me', true);
```

### 场景3：取消请求
```typescript
const controller = apiClient.createController();

// 1秒后取消
setTimeout(() => controller.abort(), 1000);

try {
  await apiClient.get('/api/slow-endpoint', true, controller.signal);
} catch (error) {
  console.log('Request cancelled:', error.message);
}
```

---

## 📁 修改文件清单

| 文件 | 操作 | 类型 |
|------|------|------|
| `lib/api.ts` | 修改 | 代码 |

---

## 📝 修复后的完整api.ts结构

```typescript
// lib/api.ts

// 类型定义
export interface User {
  id: string;
  email: string;
  name: string | null;
  phone: string | null;
  avatar_url: string | null;
  plan_tier: 'free' | 'pro' | 'enterprise';
  plan_status: 'active' | 'canceled' | 'expired';
  region_preference: string | null;
  currency_preference: string;
  created_at: string;
  last_login_at: string | null;
  is_admin: boolean;
}

// 错误类
export class APIError extends Error {
  code: string;
  status: number;
  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = 'APIError';
    this.code = code;
    this.status = status;
  }
}

// 配置
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// 认证头处理
function getAuthHeaders() {
  const token = localStorage.getItem('access_token');
  if (!token) return {};

  return {
    'Authorization': `Bearer ${token}`
  };
}

// 错误处理
async function handleResponse(response: Response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: response.statusText,
      code: 'UNKNOWN_ERROR'
    }));

    throw new APIError(
      error.detail || 'Request failed',
      error.code || 'HTTP_ERROR',
      response.status
    );
  }

  return response.json();
}

// API客户端
export const apiClient = {
  // GET请求
  async get(endpoint: string, requiresAuth = true, signal?: AbortSignal) {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (requiresAuth) {
      Object.assign(headers, getAuthHeaders());
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers,
      signal,
    });

    return handleResponse(response);
  },

  // POST请求
  async post(endpoint: string, data: any, requiresAuth = false, signal?: AbortSignal) {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (requiresAuth) {
      Object.assign(headers, getAuthHeaders());
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
      signal,
    });

    return handleResponse(response);
  },

  // PUT请求
  async put(endpoint: string, data: any, requiresAuth = true, signal?: AbortSignal) {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (requiresAuth) {
      Object.assign(headers, getAuthHeaders());
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data),
      signal,
    });

    return handleResponse(response);
  },

  // DELETE请求
  async delete(endpoint: string, requiresAuth = true, signal?: AbortSignal) {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (requiresAuth) {
      Object.assign(headers, getAuthHeaders());
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers,
      signal,
    });

    return handleResponse(response);
  },

  // 辅助方法
  createController(): AbortController {
    return new AbortController();
  }
};
```

---

*本修复清单由代码审查报告生成*
