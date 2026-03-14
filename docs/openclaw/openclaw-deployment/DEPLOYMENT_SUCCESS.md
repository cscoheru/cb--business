# OpenClaw HK 节点部署成功

## 部署摘要

**日期**: 2026-03-12
**节点**: HK (103.59.103.85)
**OpenClaw 版本**: 2026.3.11
**模型**: GLM-4 Plus

## 访问信息

| 项目 | 值 |
|------|-----|
| **Web UI** | http://103.59.103.85:18789 |
| **WebSocket** | ws://103.59.103.85:18789 |
| **认证令牌** | `VqCkbaVWUtIQv5A-AYKSXTegmNWy2V2X8Y06KcZGA30` |
| **控制面板** | http://103.59.103.85:18791 (仅限本地) |

## GLM-4.7 配置

- **API Endpoint**: https://open.bigmodel.cn/api/paas/v4
- **模型**: glm-4-plus
- **上下文窗口**: 128K tokens

## 管理命令

```bash
# 查看服务状态
ssh hk "systemctl status openclaw"

# 查看日志
ssh hk "journalctl -u openclaw -f"

# 重启服务
ssh hk "systemctl restart openclaw"

# 停止服务
ssh hk "systemctl stop openclaw"

# 查看 OpenClaw 版本
ssh hk "openclaw --version"
```

## 配置文件位置

- **配置**: `/root/.openclaw/openclaw.json`
- **日志**: `/tmp/openclaw/`
- **Systemd**: `/etc/systemd/system/openclaw.service`

## 防火墙

端口 18789 已开放。

## 下一步

1. 访问 http://103.59.103.85:18789 打开 Web UI
2. 配置 channels 和 skills
3. 设置 API 访问权限
4. 配置监控告警

## 故障排查

```bash
# 检查端口监听
ssh hk "ss -tlnp | grep 18789"

# 查看详细日志
ssh hk "journalctl -u openclaw -n 100"

# 手动测试网关
ssh hk "openclaw gateway --bind lan --port 18789 --dev"
```

---

**部署完成时间**: 2026-03-12 16:21 (UTC+8)
