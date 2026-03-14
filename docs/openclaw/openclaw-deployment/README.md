# OpenClaw HK 节点部署文档

## 概述

在香港节点 (103.59.103.85) 部署 OpenClaw AI Agent 平台，集成 GLM-4.7 模型。

## 架构

```
┌─────────────────────────────────────────────────────┐
│                  HK 节点 (香港)                       │
│              IP: 103.59.103.85                       │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │            OpenClaw 容器                     │  │
│  │  - 端口: 18789                               │  │
│  │  - 模型: GLM-4 Plus / GLM-4 Air             │  │
│  │  - API: https://open.bigmodel.cn/api/paas/v4 │  │
│  └──────────────────────────────────────────────┘  │
│                      ↓                               │
│              GLM API (智谱云)                         │
└─────────────────────────────────────────────────────┘
         ↑
         │ 远程访问
         │
┌─────────────────────────────────────────────────────┐
│              本地管理终端                             │
│  网关: http://103.59.103.85:18789                  │
└─────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 部署到 HK 节点

```bash
cd ~/infrastructure/openclaw-deployment
chmod +x deploy.sh
./deploy.sh
```

### 2. 验证部署

```bash
# 检查容器状态
ssh hk "docker ps | grep openclaw"

# 查看日志
ssh hk "docker logs -f openclaw"

# 测试网关连接
curl -H "Authorization: Bearer VqCkbaVWUtIQv5A-AYKSXTegmNWy2V2X8Y06KcZGA30" \
     http://103.59.103.85:18789/health
```

## 配置说明

### 环境变量 (.env)

| 变量 | 值 | 说明 |
|------|-----|------|
| OPENCLAW_AUTH_TOKEN | VqCkbaVWUtIQv5A-AYKSXTegmNWy2V2X8Y06KcZGA30 | 网关认证令牌 |
| GLM_API_KEY | ed79dfb6bd5d442b9818011010d6faed.ExkY3SyIQqoyDpaO | GLM API 密钥 |
| GLM_BASE_URL | https://open.bigmodel.cn/api/paas/v4 | GLM API 端点 |

### OpenClaw 配置 (config/openclaw.json)

**已配置的模型:**
- `glm-4-plus` - GLM-4 Plus (主要模型)
- `glm-4-air` - GLM-4 Air (轻量级模型)

**配置特点:**
- 网关模式: `remote` (允许远程访问)
- 网关端口: `18789`
- 上下文窗口: 128K tokens
- 最大输出: 4096/8192 tokens

## 管理命令

### 容器管理

```bash
# 查看容器状态
ssh hk "cd /opt/openclaw && docker-compose ps"

# 重启服务
ssh hk "cd /opt/openclaw && docker-compose restart"

# 停止服务
ssh hk "cd /opt/openclaw && docker-compose down"

# 启动服务
ssh hk "cd /opt/openclaw && docker-compose up -d"

# 查看实时日志
ssh hk "docker logs -f openclaw"

# 进入容器
ssh hk "docker exec -it openclaw bash"
```

### 配置更新

```bash
# 1. 修改本地配置文件
vim config/openclaw.json

# 2. 重新上传到 HK 节点
scp config/openclaw.json hk:/opt/openclaw/config/

# 3. 重启容器
ssh hk "cd /opt/openclaw && docker-compose restart"
```

## 远程访问

### 方式 1: 直接访问

```bash
# HTTP 请求
curl -X POST http://103.59.103.85:18789/api/v1/chat \
  -H "Authorization: Bearer VqCkbaVWUtIQv5A-AYKSXTegmNWy2V2X8Y06KcZGA30" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

### 方式 2: SSH 隧道

```bash
# 建立隧道
ssh -L 18789:localhost:18789 hk

# 本地访问
curl http://localhost:18789/health
```

### 方式 3: OpenClaw CLI

```bash
# 配置远程网关
openclaw config set gateway.url http://103.59.103.85:18789
openclaw config set gateway.token VqCkbaVWUtIQv5A-AYKSXTegmNWy2V2X8Y06KcZGA30

# 连接到远程网关
openclaw connect
```

## 网络配置

### 防火墙规则

HK 节点已开放端口 18789:

```bash
# 查看规则
ssh hk "ufw status | grep 18789"

# 如需手动开放
ssh hk "ufw allow 18789/tcp comment 'OpenClaw Gateway'"
```

### Nginx 反向代理 (可选)

如需通过域名访问，可在 HK 节点的 nginx-gateway 中添加配置:

```nginx
location /openclaw/ {
    proxy_pass http://localhost:18789/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## 故障排查

### 问题 1: 容器无法启动

```bash
# 查看详细日志
ssh hk "docker logs openclaw"

# 检查配置文件
ssh hk "cat /opt/openclaw/config/openclaw.json"

# 重新构建
ssh hk "cd /opt/openclaw && docker-compose down && docker-compose up -d --force-recreate"
```

### 问题 2: API 调用失败

```bash
# 测试 GLM API 连通性
curl -X POST https://open.bigmodel.cn/api/paas/v4/chat/completions \
  -H "Authorization: Bearer ed79dfb6bd5d442b9818011010d6faed.ExkY3SyIQqoyDpaO" \
  -H "Content-Type: application/json" \
  -d '{"model":"glm-4-plus","messages":[{"role":"user","content":"hi"}]}'

# 检查容器网络
ssh hk "docker exec openclaw ping -c 3 open.bigmodel.cn"
```

### 问题 3: 网关无法访问

```bash
# 检查端口监听
ssh hk "netstat -tlnp | grep 18789"

# 检查防火墙
ssh hk "ufw status | grep 18789"

# 测试本地连接
ssh hk "curl http://localhost:18789/health"
```

## 安全建议

1. **更改默认令牌**: 生产环境应使用强随机令牌
2. **限制访问来源**: 配置防火墙白名单
3. **启用 HTTPS**: 通过 Nginx 配置 SSL 证书
4. **定期更新**: 保持 OpenClaw 和依赖包最新版本

## 成本估算

**HK 节点资源占用:**
- 内存: ~500MB (Node.js 运行时)
- 磁盘: ~500MB (应用 + 数据)
- 网络: 取决于 API 调用频率

**GLM API 调用成本:**
- 按 Token 计费，参考智谱官方价格表
- 建议设置预算上限

## 相关链接

- OpenClaw: https://openclaw.dev
- 智谱 AI: https://open.bigmodel.cn
- GLM-4 文档: https://open.bigmodel.cn/dev/api

---

**维护者**: kjonekong
**最后更新**: 2026-03-12
