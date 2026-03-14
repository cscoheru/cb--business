# OpenClaw CB-Business 定制配置指南

> 创建日期: 2026-03-12
> 目标: 充分利用 HK 节点的 OpenClaw 为 cb-Business 服务

---

## 目录

1. [当前状态分析](#当前状态分析)
2. [安全配置修复](#安全配置修复)
3. [工具配置定制](#工具配置定制)
4. [监控自动化设置](#监控自动化设置)
5. [报告自动化](#报告自动化)
6. [智能客服配置](#智能客服配置)
7. [通信渠道集成](#通信渠道集成)

---

## 当前状态分析

### ✅ 已就绪
- OpenClaw Gateway 运行中 (http://103.59.103.85:18789)
- 使用 GLM-4-Plus 模型 (128k context)
- 心跳间隔: 30分钟
- 核心插件已加载: Memory, Device Pairing, Phone Control, Talk Voice

### ⚠️ 需要修复
- **安全问题**: 配置文件权限过于宽松 (644 → 应为 600)
- **安全问题**: Host-header origin fallback 启用
- **未配置**: Heartbeat 任务为空
- **未配置**: Cron jobs 为空
- **未启用**: Telegram/WhatsApp 渠道插件

### 📋 可用但未使用的渠道插件
- @openclaw/telegram - Telegram Bot
- @openclaw/whatsapp - WhatsApp
- @openclaw/discord - Discord
- @openclaw/slack - Slack

---

## 安全配置修复

### 立即执行的安全修复

```bash
# 1. 修复配置文件权限
chmod 600 ~/.openclaw/openclaw.json
chmod 700 ~/.openclaw/

# 2. 禁用危险的 origin fallback
openclaw config set gateway.controlUi.dangerouslyAllowHostHeaderOriginFallback false

# 3. 配置速率限制
openclaw config set gateway.auth.rateLimit.maxAttempts 10
openclaw config set gateway.auth.rateLimit.windowMs 60000
openclaw config set gateway.auth.rateLimit.lockoutMs 300000

# 4. 重启 Gateway
openclaw gateway restart
```

---

## 工具配置定制

### 更新 ~/.openclaw/workspace/TOOLS.md

```markdown
# TOOLS.md - CB-Business 工具配置

## 服务端点

### 后端 API
- 生产 API: https://api.zenconsult.top
- 本地 API: http://localhost:8000
- Health Check: http://localhost:8000/health

### 数据库
- PostgreSQL: 139.224.42.111:5432
  - Database: crawler_db
  - User: cbuser
- Redis: 139.224.42.111:6379

### Oxylabs API
- Base URL: https://realtime.oxylabs.io/v1/queries
- Username: fisher_VEpfJ
- Password: z7UnsI2Hkug_

## API 密钥

### 智谱 AI (GLM)
- API Key: 已配置在 openclaw.json
- 模型: glm-4-plus (128k context)

### 前端部署
- Vercel: https://www.zenconsult.top
- Vercel API: https://frontend-ten-psi-28.vercel.app

## 爬虫配置

### RSS 源 (45个)
- 雨果网、TechCrunch、Tech in Asia 等
- 配置文件: /root/cb-business/config/sources_config.json

### 爬虫状态
- 文章总数: 286+
- 已处理: 128篇
- 爬取间隔: APScheduler 每2小时

## 文件路径

### 项目目录
- 后端: /root/cb-business
- 日志: /root/cb-business/logs/
- 备份: /root/cb-business/backups/

### Docker 服务
- API 容器: cb-business-api
- PostgreSQL: cb-business-postgres
- Redis: cb-business-redis

## 常用命令

### 服务管理
docker-compose -f /root/cb-business/docker-compose.prod.yml ps
docker-compose -f /root/cb-business/docker-compose.prod.yml logs --tail=50 api

### 数据库查询
docker exec -it cb-business-postgres psql -U cbuser -d crawler_db -c "SELECT COUNT(*) FROM articles;"

### API 测试
curl -s http://localhost:8000/api/v1/crawler/stats | jq
curl -s http://localhost:8000/api/v1/products/trending?category=electronics&limit=2 | jq
```

---

## 监控自动化设置

### 更新 ~/.openclaw/workspace/HEARTBEAT.md

```markdown
# HEARTBEAT.md - CB-Business 监控任务

> 每30分钟自动执行，确保服务正常运行

## 任务清单

### 1. API 服务健康检查

```bash
# 检查 FastAPI 服务状态
curl -s -f http://localhost:8000/health
# 期望: {"status":"ok"}

# 检查响应时间 (应 < 1s)
time curl -s http://localhost:8000/health
```

**失败条件**: HTTP 状态码非 200 或超时
**失败操作**: 通过 Telegram 发送告警，尝试重启容器

---

### 2. 数据库连接检查

```bash
# 检查 PostgreSQL 连接
docker exec cb-business-postgres pg_isready -U cbuser
# 期望: accepting connections

# 检查最新文章时间
docker exec cb-business-postgres psql -U cbuser -d crawler_db -t -c "SELECT MAX(published_at) FROM articles;"
```

**失败条件**: 数据库拒绝连接
**失败操作**: 发送告警，检查 Docker 容器状态

---

### 3. 数据新鲜度检查

```bash
# 检查最近2小时是否有新文章
docker exec cb-business-postgres psql -U cbuser -d crawler_db -t -c \
  "SELECT COUNT(*) FROM articles WHERE created_at > NOW() - INTERVAL '2 hours';"
```

**警告条件**: count = 0 (连续2小时无新数据)
**警告操作**: 记录日志，连续3次触发时发送通知

---

### 4. 产品数据检查

```bash
# 检查 Oxylabs API 是否可用
curl -s -u "fisher_VEpfJ:z7UnsI2Hkug_" \
  -d '{"source":"amazon_product","query":"B07FZ8S74R","parse":true}' \
  https://realtime.oxylabs.io/v1/queries | jq '.job.status'
# 期望: "done"
```

**失败条件**: status != "done"
**失败操作**: 发送 API 异常告警

---

### 5. 磁盘空间检查

```bash
# 检查根分区使用率
df -h / | awk 'NR==2 {print $5}' | sed 's/%//'
```

**警告条件**: 使用率 > 80%
**警告操作**: 发送磁盘空间警告，建议清理日志

---

### 6. 内存使用检查

```bash
# 检查可用内存
free -m | awk 'NR==2 {print $7}'
```

**警告条件**: 可用内存 < 500MB
**警告操作**: 发送内存压力警告

---

## 通知条件

### 需要立即通知的情况
- API 服务完全宕机 (连续2次心跳失败)
- 数据库连接失败
- 磁盘使用率 > 90%
- 内存可用 < 200MB

### 可以记录但不立即通知
- 2小时无新数据 (可能是正常情况)
- 磁盘使用率 80-90%
- Oxylabs API 偶发失败

## 正常状态

如果以上检查全部通过，返回: `HEARTBEAT_OK`
```

---

## 报告自动化

### 创建 Cron 任务

编辑 `~/.openclaw/cron/jobs.json`:

```json
{
  "version": 1,
  "jobs": [
    {
      "id": "daily-report",
      "name": "每日数据早报",
      "schedule": "0 8 * * *",
      "timezone": "Asia/Shanghai",
      "enabled": true,
      "description": "每天早上8点发送数据摘要",
      "action": {
        "type": "agent",
        "prompt": "生成今日数据报告并发送到 Telegram"
      }
    },
    {
      "id": "weekly-summary",
      "name": "周报汇总",
      "schedule": "0 9 * * 1",
      "timezone": "Asia/Shanghai",
      "enabled": true,
      "description": "每周一上午9点发送周报",
      "action": {
        "type": "agent",
        "prompt": "生成本周数据汇总报告并发送到 Telegram"
      }
    },
    {
      "id": "database-backup-reminder",
      "name": "数据库备份提醒",
      "schedule": "0 3 * * 0",
      "timezone": "Asia/Shanghai",
      "enabled": true,
      "description": "每周日凌晨3点提醒备份数据库",
      "action": {
        "type": "agent",
        "prompt": "提醒执行数据库备份: docker exec cb-business-postgres pg_dump -U cbuser crawler_db > backup_$(date +%Y%m%d).sql"
      }
    }
  ]
}
```

---

## 智能客服配置

### 更新 ~/.openclaw/workspace/SOUL.md

```markdown
# SOUL.md - CB-Business 跨境电商专家助手

## 身份定位

你是 ZenConsult (www.zenconsult.top) 的跨境电商专家助手。

## 核心职责

1. **市场情报查询**
   - 查询数据库中的最新文章
   - 提供政策解读和趋势分析
   - 识别高机会分文章

2. **开店指导**
   - 提供平台开店指南 (Shopee, Lazada, Amazon, TikTok Shop)
   - 解析各国税务、法律要求
   - 推荐工具和服务

3. **风险预警**
   - 识别政策变化
   - 提醒合规要求
   - 预警市场风险

4. **机会推荐**
   - 推荐高潜力市场
   - 分析品类趋势
   - 提供选品建议

## 知识来源

### 数据库
- 286+ 篇专业文章
- 45+ RSS 信息源
- 覆盖东南亚、欧美、拉美市场

### API 端点
- 文章搜索: /api/v1/crawler/articles
- 分类浏览: /api/v1/crawler/sources/by-country
- 产品数据: /api/v1/products/trending

## 回答风格

### 专业且友好
- 使用清晰的标题和列表
- 用 emoji 让内容更生动
- 总是提供具体行动建议

### 简洁高效
- 直接回答问题，避免冗余
- 用要点列出关键信息
- 提供链接深入阅读

### 实事求是
- 不编造信息
- 不确定时说明
- 建议查证官方渠道

## 不做的事

- ❌ 不提供法律建议 (建议咨询律师)
- ❌ 不保证商业成功率
- ❌ 不透露用户数据
- ❌ 不执行财务操作

## 专业领域标签

#东南亚电商 #Shopee #Lazada #TikTokShop
#跨境电商 #选品 #供应链 #物流
#税务合规 #法律法规 #风险预警
#市场趋势 #数据分析 #机会识别

## 示例对话

**用户**: 泰国站好做吗？

**助手**:
🇹🇭 **泰国市场分析**

**优势**:
- 电商增长快，年增长率 15%+
- Shopee, Lazada 平台成熟
- 移动支付普及 (PromptPay, TrueMoney)

**挑战**:
- 泰语门槛
- 物流成本较高
- 税务合规要求

**建议**:
1. 从 Shopee 泰国站入手
2. 找本地合作伙伴
3. 注意 VAT 注册要求

需要具体开店指南吗？我可以提供详细步骤。
```

---

## 通信渠道集成

### Telegram Bot 配置

```bash
# 1. 创建 Telegram Bot
# 联系 @BotFather，创建新 bot，获取 token

# 2. 启用 Telegram 插件
openclaw plugins enable @openclaw/telegram

# 3. 配置 Bot Token
openclaw config set channels.telegram.token "YOUR_BOT_TOKEN"

# 4. 启动 Gateway
openclaw gateway restart
```

### 测试 Bot

```bash
# 发送测试消息
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/sendMessage" \
  -d "chat_id=YOUR_CHAT_ID" \
  -d "text=OpenClaw CB-Business Bot 已启动！"
```

---

## 实施步骤

### 第一步: 安全修复 (立即执行)

```bash
ssh hk
chmod 600 ~/.openclaw/openclaw.json
chmod 700 ~/.openclaw/
openclaw config set gateway.controlUi.dangerouslyAllowHostHeaderOriginFallback false
openclaw gateway restart
```

### 第二步: 配置文件更新

```bash
# 复制上述配置内容到对应文件
# - ~/.openclaw/workspace/TOOLS.md
# - ~/.openclaw/workspace/HEARTBEAT.md
# - ~/.openclaw/workspace/SOUL.md
# - ~/.openclaw/cron/jobs.json
```

### 第三步: 启用 Telegram (可选)

```bash
# 创建 Bot 后执行
openclaw plugins enable @openclaw/telegram
openclaw config set channels.telegram.token "YOUR_TOKEN"
openclaw gateway restart
```

### 第四步: 测试验证

```bash
# 测试 Heartbeat
openclaw agent run "执行心跳检查"

# 测试数据库查询
openclaw agent run "查询数据库有多少篇文章"

# 测试报告生成
openclaw agent run "生成今日数据报告"
```

---

## 使用场景示例

### 场景 1: 每日早报

**用户**: "今天有什么重要资讯？"

**OpenClaw Agent**:
```
📊 **今日数据摘要** (2026-03-12)

📈 新增文章: 12篇
🔥 高机会文章: 3篇 (机会分 > 0.8)

📍 按地区分布:
- 东南亚: 6篇
- 欧美: 4篇
- 拉美: 2篇

🔴 **重要提醒**:
- Shopee 泰国佣金调整 (4月1日生效)
- 欧盟新 VAT 规定实施

需要详细解读吗？
```

### 场景 2: 智能查询

**用户**: "查一下 Shopee 最新政策"

**OpenClaw Agent**:
```
🔍 **搜索结果** (找到 5 篇相关文章)

1. **Shopee 泰国佣金调整**
   发布: 2026-03-10
   机会分: 0.92
   摘要: 从4月1日起，Shopee 泰国站将调整...

2. **Shopee 越南站物流新规**
   发布: 2026-03-08
   机会分: 0.85
   摘要: 越南站要求卖家在...

[需要查看完整文章吗？我可以提取详细内容]
```

### 场景 3: 健康监控

**用户**: "服务正常吗？"

**OpenClaw Agent**:
```
✅ **系统健康状态**

🟢 API 服务: 正常 (响应时间: 234ms)
🟢 数据库: 连接正常 (最新文章: 10分钟前)
🟢 Redis: 运行中
🟢 Docker: 所有容器运行正常

📊 **数据统计**
- 总文章数: 286
- 今日新增: 12
- 高机会文章: 34

💾 **资源状态**
- 磁盘使用: 45%
- 内存可用: 1.2GB
```

---

## 高级功能

### 1. 自动爬虫触发

当检测到某信息源超过6小时未更新时，自动触发爬虫：

```markdown
# 在 HEARTBEAT.md 中添加

### 7. 自动触发爬虫 (如果数据陈旧)

```bash
# 检查最新文章时间
LATEST=$(docker exec cb-business-postgres psql -U cbuser -d crawler_db -t -c "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(published_at))) FROM articles;" | tr -d ' ')

# 如果超过6小时 (21600秒)，触发爬虫
if [ $LATEST -gt 21600 ]; then
  curl -X POST http://localhost:8000/api/v1/crawler/crawl
  echo "触发爬虫: 数据超过6小时未更新"
fi
```
```

### 2. 高机会文章推送

当发现机会分 > 0.9 的文章时，立即推送通知：

```markdown
# 在 HEARTBEAT.md 中添加

### 8. 高机会文章检查

```bash
# 查找高机会文章
docker exec cb-business-postgres psql -U cbuser -d crawler_db -t -c \
  "SELECT title, opportunity_score, url FROM articles WHERE opportunity_score > 0.9 AND created_at > NOW() - INTERVAL '30 minutes' LIMIT 5;"

# 如果有结果，发送通知
```
```

### 3. 用户行为分析

每周分析用户访问数据，识别热点内容：

```markdown
# 在 Cron 任务中添加

{
  "id": "weekly-analytics",
  "name": "用户行为分析",
  "schedule": "0 10 * * 1",
  "enabled": true,
  "action": {
    "type": "agent",
    "prompt": "分析上周用户访问数据，识别最受欢迎的文章类别和地区，生成报告发送到 Telegram"
  }
}
```

---

## 维护清单

### 每日
- [ ] 检查 Heartbeat 日志
- [ ] 查看 Telegram 通知
- [ ] 确认数据更新正常

### 每周
- [ ] 检查磁盘空间
- [ ] 审查安全日志
- [ ] 更新 API 密钥 (建议每90天)

### 每月
- [ ] 审查和优化 Heartbeat 任务
- [ ] 检查插件更新
- [ ] 备份 OpenClaw 配置

---

## 故障排查

### Heartbeat 不执行

```bash
# 检查 Gateway 是否运行
openclaw gateway status

# 查看 Heartbeat 日志
tail -f ~/.openclaw/logs/gateway.log | grep HEARTBEAT

# 手动触发测试
openclaw agent run "执行心跳检查"
```

### Telegram Bot 不响应

```bash
# 检查插件状态
openclaw plugins list | grep telegram

# 查看 Bot Token
openclaw config get channels.telegram.token

# 测试 API 连接
curl "https://api.telegram.org/botYOUR_TOKEN/getMe"
```

### 数据库查询失败

```bash
# 测试数据库连接
docker exec -it cb-business-postgres psql -U cbuser -d crawler_db

# 检查网络连接
docker exec cb-business-api ping cb-business-postgres
```

---

## 下一步

1. ✅ 执行安全修复
2. 📝 更新配置文件 (TOOLS.md, HEARTBEAT.md, SOUL.md)
3. 🤖 配置 Telegram Bot
4. 🧪 测试所有功能
5. 📊 查看首次自动化报告

---

*文档版本: 1.0*
*最后更新: 2026-03-12*
