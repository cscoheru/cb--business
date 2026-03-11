# 部署经验教训

## Railway 健康检查问题

### 问题
Railway 的健康检查在应用启动时执行得太早，导致部署失败。

### 根本原因
1. Railway 的健康检查在容器启动后立即执行
2. FastAPI 应用需要时间来初始化路由、中间件等
3. 如果健康检查端点依赖外部服务（DB/Redis），会进一步延迟响应

### 解决方案
**永久解决方案：禁用 Railway 健康检查**

在 `railway.toml` 中设置：
```toml
[deploy]
healthcheckPath = ""
healthcheckTimeout = 0
```

应用本身提供 `/health` 端点用于监控，但不需要 Railway 的健康检查。

### 关键原则
1. **应用启动必须非阻塞** - 不要在 `startup` 事件中等待外部服务
2. **提供默认值** - 所有必需的配置都要有默认值
3. **快速失败** - 如果必须失败，也要快速失败，不要超时

### Dockerfile 优先于 Nixpacks
Nixpacks 的自动检测会忽略配置文件，使用 Dockerfile 更可靠。

```dockerfile
CMD ["python", "-m", "api"]
```

而不是依赖 Nixpacks 自动检测 uvicorn。

## 环境变量

### 必需的环境变量（ Railway Dashboard 中设置）

```bash
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=<生成的密钥>
ALLOWED_ORIGINS=https://www.zenconsult.top,https://admin.zenconsult.top
```

### 代码中的默认值
所有必需字段都要有默认值，确保应用能启动：

```python
class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"  # 默认值
    REDIS_URL: str = ""  # 可选
    SECRET_KEY: str = "dev-key-at-least-32-chars-long"  # 必须>=32字符
```

### 常见缺失依赖
- **email-validator** - Pydantic 的 EmailStr 验证需要
  ```txt
  email-validator>=2.0.0
  ```

## Vercel 部署

### 常见错误
1. `async function return type` - 使用 `Promise<void>` 而不是 `void`
2. TypeScript 类型错误 - API 参数名必须匹配接口定义（`plan_tier` 不是 `plan`）

### 部署方式
使用 Vercel GitHub 集成，而不是 CLI。CLI 容易有各种问题。

## 未来部署检查清单

- [ ] Railway 健康检查已禁用 (`healthcheckPath = ""`)
- [ ] 使用 Dockerfile 而不是 Nixpacks
- [ ] 所有必需配置有默认值
- [ ] 启动事件非阻塞（不等待外部服务）
- [ ] 提供 `/` 根路径端点
- [ ] TypeScript 类型正确（`Promise<void>`）

*最后更新：2026-03-11 - 彻底解决 Railway 健康检查问题*
