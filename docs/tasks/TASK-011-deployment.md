# TASK-011: 部署上线

> **所属会话**: 会话3（基础设施线）配合项目经理
> **优先级**: P0（最高）
> **预计工期**: 3天
> **依赖任务**: 所有开发和测试任务
> **创建日期**: 2025-03-10
> **状态**: ⏳ 待开始

---

## 任务目标

将前端、后端、管理后台部署到生产环境，配置域名和SSL，确保系统可访问。

---

## 部署清单

### Vercel部署（前端）

```bash
# 用户前端
cd frontend
vercel link
vercel --prod

# 管理后台
cd ../admin
vercel link
vercel --prod
```

### Railway部署（后端）

```bash
cd backend
railway login
railway init
railway up
railway domain
```

### 域名配置

| 子域名 | 指向 | 服务 |
|--------|------|------|
| cb.3strategy.cc | Vercel | 用户前端 |
| admin.cb.3strategy.cc | Vercel | 管理后台 |
| api.cb.3strategy.cc | Railway | 后端API |

---

## 环境变量配置

### Vercel环境变量

```bash
# 前端环境变量
NEXT_PUBLIC_API_URL=https://api.cb.3strategy.cc
```

### Railway环境变量

```bash
# 后端环境变量
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=...
WECHAT_APP_ID=...
WECHAT_MCH_ID=...
WECHAT_API_KEY=...
```

---

## SSL证书配置

```nginx
# /etc/nginx/sites-available/cb.3strategy.cc
server {
    listen 443 ssl http2;
    server_name cb.3strategy.cc;

    ssl_certificate /etc/ssl/certs/cb.3strategy.cc.pem;
    ssl_certificate_key /etc/ssl/private/cb.3strategy.cc.key;

    location / {
        proxy_pass https://vercel-app;
        proxy_set_header Host $host;
    }
}
```

---

## 验收测试

- [ ] 前端可访问（cb.3strategy.cc）
- [ ] 管理后台可访问（admin.cb.3strategy.cc）
- [ ] API可访问（api.cb.3strategy.cc）
- [ ] SSL证书正常
- [ ] API文档可访问
- [ ] 用户注册登录正常
- [ ] 支付流程测试通过

---

## 提交规范

```bash
git commit -m "deploy(TASK-011): 完成生产环境部署

- 部署前端到Vercel
- 部署后端到Railway
- 配置域名解析
- 配置SSL证书
- 配置环境变量
- 完成生产验收测试

部署环境:
- cb.3strategy.cc (Vercel)
- admin.cb.3strategy.cc (Vercel)
- api.cb.3strategy.cc (Railway)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

*本任务书由主会话（项目经理）创建和维护*
