# OpenClaw爬虫集成方案

## 目标

让OpenClaw完全接管网站内容更新，替代FastAPI中的APScheduler调度器。

## 架构设计

```
OpenClaw Gateway (18789)
    ├── Channels (爬虫channels)
    │    ├── rss-crawler-channel
    │    ├── products-channel
    │    └── trends-channel
    ├── Scheduler (OpenClaw内置)
    └── 数据写入 → PostgreSQL
```

## 实施步骤

### 步骤1：创建OpenClaw Channel - RSS爬虫

**文件位置**：HK服务器 `/root/.openclaw/channels/rss-crawler.js`

```javascript
const { spawn } = require('child_process');
const path = require('path');

// RSS源配置（从crawler/config.py迁移）
const RSS_SOURCES = [
    { name: 'Retail Dive', url: 'https://www.retaildive.com/feeds/news/', language: 'en' },
    { name: 'TechCrunch', url: 'https://techcrunch.com/feed/', language: 'en' },
    { name: '雨果网', url: 'https://www.ennews.com/rss.xml', language: 'zh' },
    { name: 'Digital Commerce 360', url: 'https://www.digitalcommerce360.com/feed/', language: 'en' },
    { name: 'PYMNTS', url: 'https://www.pymnts.com/feed/', language: 'en' },
    { name: 'EcommerceBytes', url: 'https://www.ecommercebytes.com/feed/', language: 'en' },
    { name: 'Tech in Asia', url: 'https://www.techinasia.com/feed', language: 'en' },
    { name: 'Mercopress', url: 'https://en.mercopress.com/rss/', language: 'en' },
    { name: 'Amazon Seller News', url: 'https://sell.amazonpress.com/feed/', language: 'en' },
    { name: 'eBay Seller News', url: 'https://www.ebayinc.com/stories/feed/', language: 'en' },
    // ... 添加更多源
];

module.exports = async function(context) {
    const results = {
        success: 0,
        failed: 0,
        sources: RSS_SOURCES.length,
        articles: [],
        errors: []
    };

    // 遍历所有RSS源
    for (const source of RSS_SOURCES) {
        try {
            context.log(`🔄 开始爬取: ${source.name}`);

            // 调用Python爬虫脚本
            const pythonScript = '/opt/cb-business-repo/backend/scripts/run_crawler.py';
            const args = [
                '--source', source.name,
                '--url', source.url,
                '--language', source.language
            ];

            const result = await spawnPython(pythonScript, args);

            results.success++;
            results.articles.push(...result.articles);

            context.log(`✅ ${source.name}: 获取 ${result.articles.length} 篇文章`);

        } catch (error) {
            results.failed++;
            results.errors.push({
                source: source.name,
                error: error.message
            });
            context.error(`❌ ${source.name}: ${error.message}`);
        }
    }

    // 存储到数据库（通过FastAPI）
    try {
        await context.http.post({
            url: 'http://localhost:8000/api/v1/crawler/articles/batch',
            headers: { 'Content-Type': 'application/json' },
            json: { articles: results.articles },
            timeout: 30000
        });

        context.log(`✅ 已保存 ${results.articles.length} 篇文章到数据库`);
    } catch (error) {
        context.error(`❌ 保存到数据库失败: ${error.message}`);
        throw error;
    }

    return {
        total_sources: results.sources,
        successful: results.success,
        failed: results.failed,
        articles_saved: results.articles.length,
        summary: `${results.success}/${results.sources} 源成功，${results.articles.length} 篇文章已保存`
    };
};

// 辅助函数：调用Python脚本
function spawnPython(script, args) {
    return new Promise((resolve, reject) => {
        const python = spawn('python3', [script, ...args], {
            cwd: '/opt/cb-business-repo/backend',
            env: {
                ...process.env,
                PYTHONPATH: '/opt/cb-business-repo/backend'
            }
        });

        let stdout = '';
        let stderr = '';

        python.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        python.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        python.on('close', (code) => {
            if (code === 0) {
                try {
                    const result = JSON.parse(stdout);
                    resolve(result);
                } catch (e) {
                    // 如果不是JSON输出，返回原始数据
                    resolve({ articles: [], raw: stdout });
                }
            } else {
                reject(new Error(`Python脚本失败 (code ${code}): ${stderr}`));
            }
        });

        // 超时处理
        setTimeout(() => {
            python.kill();
            reject(new Error('Python脚本执行超时'));
        }, 60000); // 60秒超时
    });
}
```

### 步骤2：创建Python爬虫包装脚本

**文件位置**：HK服务器 `/opt/cb-business-repo/backend/scripts/run_crawler.py`

```python
#!/usr/bin/env python3
"""
OpenClaw调用的爬虫包装脚本
"""
import asyncio
import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from crawler.crawlers.rss_crawler import RSSCrawler
from crawler.processors.article_processor import ArticleProcessor
from config.database import AsyncSessionLocal


async def run_crawler(source_name: str, url: str, language: str):
    """运行单个RSS源的爬虫"""

    # 配置爬虫
    source_config = {
        "name": source_name,
        "url": url,
        "language": language,
        "max_articles": 20
    }

    crawler = RSSCrawler(source_config)
    articles = await crawler.fetch()

    # 处理文章（如果需要）
    processor = ArticleProcessor()
    processed_articles = []

    for article in articles:
        processed = await processor.process(article)
        if processed:
            processed_articles.append(processed)

    # 返回JSON结果
    result = {
        "success": True,
        "source": source_name,
        "articles_count": len(processed_articles),
        "articles": processed_articles
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="运行RSS爬虫")
    parser.add_argument("--source", required=True, help="数据源名称")
    parser.add_argument("--url", required=True, help="RSS URL")
    parser.add_argument("--language", default="en", help="语言")

    args = parser.parse_args()

    try:
        asyncio.run(run_crawler(args.source, args.url, args.language))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }), file=sys.stderr)
        sys.exit(1)
```

### 步骤3：创建OpenClaw Channel配置

**文件位置**：HK服务器 `/root/.openclaw/channels.json`

```json
{
  "version": 1,
  "channels": [
    {
      "id": "rss-crawler-daily",
      "name": "RSS文章爬虫（每日）",
      "module": "./channels/rss-crawler.js",
      "enabled": true,
      "schedule": "0 */2 * * *",
      "timezone": "Asia/Shanghai",
      "description": "每2小时爬取一次RSS文章",
      "timeout": 300000,
      "retries": 3,
      "config": {
        "batch_size": 5,
        "max_articles_per_source": 20
      }
    },
    {
      "id": "rss-crawler-nightly",
      "name": "RSS文章爬虫（夜间深度爬取）",
      "module": "./channels/rss-crawler.js",
      "enabled": true,
      "schedule": "0 2 * * *",
      "timezone": "Asia/Shanghai",
      "description": "每天凌晨2点深度爬取所有源",
      "timeout": 600000,
      "config": {
        "batch_size": 10,
        "max_articles_per_source": 50
      }
    }
  ]
}
```

### 步骤4：修改FastAPI - 移除调度器

**文件位置**：HK服务器 `/opt/cb-business-repo/backend/main.py`

**修改前**：
```python
from scheduler.scheduler import start_scheduler, stop_scheduler

async def main():
    await start_scheduler()
    # ... API服务器启动
```

**修改后**：
```python
# 移除调度器导入
# from scheduler.scheduler import start_scheduler, stop_scheduler

async def main():
    # 不再启动调度器
    # await start_scheduler()

    # 只启动API服务器
    # ... API服务器启动
```

### 步骤5：更新HEARTBEAT.md

**文件位置**：HK服务器 `/root/.openclaw/workspace/HEARTBEAT.md`

```markdown
# HEARTBEAT.md - CB-Business 监控任务

## 任务清单

### 1. OpenClaw Channels检查

```bash
# 检查OpenClaw channels状态
curl -H "Authorization: Bearer VqCkbaVWUtIQv5A-AYKSXTegmNWy2V2X8Y06KcZGA30" \
  http://localhost:18789/api/channels
```

### 2. 数据新鲜度检查

```bash
# 检查最新文章时间（应该在2小时内）
LATEST_TIME=\$(docker exec cb-business-postgres psql -U cbuser -d cbdb -t -c \
  "SELECT EXTRACT(EPOCH FROM (NOW() - MAX(crawled_at))) FROM articles;" | tr -d ' ')

if [ \$LATEST_TIME -gt 7200 ]; then
    echo "⚠️ 警告：数据超过2小时未更新"
    # 触发OpenClaw channel
    curl -X POST -H "Authorization: Bearer VqCkbaVWUtIQv5A-AYKSXTegmNWy2V2X8Y06KcZGA30" \
      -H "Content-Type: application/json" \
      -d '{"channel":"rss-crawler-daily"}' \
      http://localhost:18789/api/channels/trigger
fi
```

### 3. 数据量检查

```bash
# 检查文章总数
ARTICLE_COUNT=\$(docker exec cb-business-postgres psql -U cbuser -d cbdb -t -c \
  "SELECT COUNT(*) FROM articles;" | tr -d ' ')

if [ \$ARTICLE_COUNT -lt 300 ]; then
    echo "⚠️ 警告：文章数量异常低 (\$ARTICLE_COUNT)"
fi
```

### 4. API健康检查

```bash
# 检查FastAPI是否响应
curl -f http://localhost:8000/health || echo "❌ API不响应"
```

## 正常状态

如果以上检查全部通过，返回: `HEARTBEAT_OK`
```

---

## 完整的数据流

```
1. OpenClaw定时触发（每2小时）
   ↓
2. 调用 rss-crawler channel
   ↓
3. Channel执行 run_crawler.py
   ↓
4. Python爬虫抓取RSS文章
   ↓
5. 通过FastAPI批量保存API存储到PostgreSQL
   ↓
6. 前端从FastAPI读取最新数据
   ↓
7. 用户看到更新内容
```

## 测试步骤

### 1. 手动测试Channel

```bash
# SSH到HK服务器
ssh hk-jump

# 进入OpenClaw目录
cd ~/.openclaw

# 手动运行channel
openclaw channel run rss-crawler-daily
```

### 2. 验证数据

```bash
# 检查数据库
docker exec cb-business-postgres psql -U cbuser -d cbdb -c \
  "SELECT COUNT(*), MAX(crawled_at) FROM articles;"

# 检查API
curl http://localhost:8000/api/v1/crawler/articles?per_page=5
```

### 3. 启用自动调度

```bash
# 重启OpenClaw使配置生效
systemctl restart openclaw

# 查看日志
journalctl -u openclaw -f
```

## 监控与告警

### 创建Telegram通知Channel

```javascript
// ~/.openclaw/channels/health-alert.js
module.exports = async function(context) {
    const results = await context.http.get('http://localhost:8000/health');

    if (results.status !== 'healthy') {
        // 发送Telegram告警
        await context.telegram.sendMessage({
            chat_id: 'YOUR_CHAT_ID',
            text: `⚠️ CB-Business API异常: ${JSON.stringify(results)}`
        });
    }

    return results;
};
```

## 回滚方案

如果OpenClaw接管出现问题，可以快速回滚：

```bash
# 1. 停止OpenClaw channels
cd ~/.openclaw
# 编辑channels.json，将所有enabled设为false
systemctl restart openclaw

# 2. 恢复FastAPI调度器
cd /opt/cb-business-repo/backend
git checkout main.py  # 恢复原调度器代码

# 3. 重启FastAPI
docker restart cb-business-api-fixed
```

---

**文档版本**: 1.0
**创建日期**: 2026-03-12
**状态**: 待实施
