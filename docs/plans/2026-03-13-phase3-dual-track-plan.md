# Phase 3: 双轨运行测试计划

**日期**: 2026-03-13
**预计时长**: 2-3天
**状态**: 准备中

---

## 目标

验证OpenClaw数据采集系统与现有APScheduler系统的数据质量和一致性，为逐步迁移做准备。

## 架构对比

```
┌─────────────────────────────────────────────────────────────────┐
│                     双轨运行架构                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐         ┌──────────────────────┐     │
│  │   APScheduler        │         │    OpenClaw          │     │
│  │   (生产系统)         │   VS    │    (影子模式)        │     │
│  └──────────────────────┘         └──────────────────────┘     │
│           │                              │                      │
│           ▼                              ▼                      │
│  ┌──────────────────────┐         ┌──────────────────────┐     │
│  │   Python爬虫         │         │   JavaScript Channels│     │
│  │   - 45 RSS源         │         │   - RSS Crawler      │     │
│  │   - Oxylabs搜索      │         │   - Oxylabs Monitor  │     │
│  │   - 定时任务         │         │   - Bright Data     │     │
│  └──────────────────────┘         └──────────────────────┘     │
│           │                              │                      │
│           ▼                              ▼                      │
│  ┌──────────────────────┐         ┌──────────────────────┐     │
│  │   PostgreSQL         │         │   FastAPI Batch API  │     │
│  │   - articles表       │◄────────┤   - 批量写入         │     │
│  │   - cards表          │         │   - 统一格式         │     │
│  └──────────────────────┘         └──────────────────────┘     │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              数据对比监控服务                             │  │
│  │  - 数据质量对比                                           │  │
│  │  - 一致性验证                                             │  │
│  │  - 性能指标收集                                           │  │
│  │  - 异常告警                                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 测试范围

### 1. 数据采集对比

| 数据类型 | APScheduler | OpenClaw | 对比指标 |
|---------|-------------|----------|---------|
| 文章采集 | 48个数据源 | 45个RSS源 | 数量、完整性、时效性 |
| 产品搜索 | Oxylabs搜索API | Oxylabs/Bright Data | 字段完整度、准确率 |
| AI分类 | 智谱API | GLM-4 Plus | 分类一致性、速度 |
| 卡片生成 | 本地统计 | AI分析 | 评分分布、商业价值 |

### 2. 性能指标对比

| 指标 | APScheduler | OpenClaw | 目标 |
|------|-------------|----------|------|
| 执行频率 | 每30分钟 | 可配置 | ±5% |
| 响应时间 | 2-5秒 | 3-10秒 | <2x |
| 成功率 | >95% | >95% | 相当 |
| 资源使用 | CPU/MEM | CPU/MEM | <1.5x |

### 3. 数据质量验证

```sql
-- 对比查询示例
SELECT
    'APScheduler' as source,
    COUNT(*) as article_count,
    COUNT(CASE WHEN is_processed THEN 1 END) as processed_count,
    AVG(opportunity_score) as avg_score,
    MAX(crawled_at) as latest_update
FROM articles WHERE source LIKE 'rss-%'

UNION ALL

SELECT
    'OpenClaw' as source,
    COUNT(*) as article_count,
    COUNT(CASE WHEN is_processed THEN 1 END) as processed_count,
    AVG(opportunity_score) as avg_score,
    MAX(crawled_at) as latest_update
FROM articles WHERE source = 'openclaw-rss';
```

## 实施步骤

### Step 1: 环境准备 (30分钟)

**1.1 创建数据标记**
```sql
-- 为现有数据添加来源标记
UPDATE articles SET source = 'apscheduler-' || source
WHERE source NOT LIKE 'openclaw-%';
```

**1.2 创建对比表**
```sql
CREATE TABLE IF NOT EXISTS data_comparison_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP DEFAULT NOW(),
    comparison_type VARCHAR(50),

    -- APScheduler指标
    aps_count INTEGER,
    aps_avg_score FLOAT,
    aps_success_rate FLOAT,

    -- OpenClaw指标
    oc_count INTEGER,
    oc_avg_score FLOAT,
    oc_success_rate FLOAT,

    -- 对比结果
    count_diff INTEGER,
    count_diff_pct FLOAT,
    score_diff FLOAT,
    consistency_score FLOAT,

    -- 状态
    status VARCHAR(20),
    notes TEXT
);

CREATE INDEX idx_comparison_timestamp ON data_comparison_log(timestamp);
CREATE INDEX idx_comparison_type ON data_comparison_log(comparison_type);
```

### Step 2: 配置OpenClaw调度 (15分钟)

**2.1 启用Channels**
```bash
# 在HK服务器上
cd ~/.openclaw

# 配置channels调度
cat > cron/channels_jobs.json << EOF
{
  "jobs": [
    {
      "id": "rss-crawler-channel",
      "name": "RSS Crawler Channel (影子模式)",
      "channel": "channels/rss-crawler.js",
      "schedule": "*/30 * * * *",
      "enabled": true,
      "mode": "shadow"
    },
    {
      "id": "content-classifier-channel",
      "name": "Content Classifier Channel (影子模式)",
      "channel": "channels/content-classifier.js",
      "schedule": "*/30 * * * *",
      "enabled": true,
      "mode": "shadow"
    }
  ]
}
EOF
```

**2.2 设置OpenClaw Cron**
```bash
# 添加到crontab
# OpenClaw Channel调度 (影子模式)
*/30 * * * * cd ~/.openclaw && node channels/rss-crawler.js >> logs/rss-shadow.log 2>&1
*/30 * * * * cd ~/.openclaw && node channels/content-classifier.js >> logs/classifier-shadow.log 2>&1
0 */6 * * * cd ~/.openclaw && node channels/trend-discovery.js >> logs/trend-shadow.log 2>&1
```

### Step 3: 创建监控脚本 (45分钟)

**文件**: `backend/scripts/dual_track_monitor.py`

```python
"""
双轨运行数据对比监控脚本
每小时执行一次，对比APScheduler和OpenClaw的数据
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from config.database import AsyncSessionLocal
from models.article import Article
from models.card import Card

logger = logging.getLogger(__name__)

class DualTrackMonitor:
    """双轨运行监控器"""

    async def compare_articles(self):
        """对比文章数据"""
        async with AsyncSessionLocal() as db:
            # APScheduler数据
            aps_result = await db.execute(
                select(
                    func.count(Article.id).label('count'),
                    func.avg(Article.opportunity_score).label('avg_score')
                ).where(
                    and_(
                        Article.source.like('apscheduler-%'),
                        Article.crawled_at > datetime.now() - timedelta(hours=2)
                    )
                )
            )
            aps_data = aps_result.first()

            # OpenClaw数据
            oc_result = await db.execute(
                select(
                    func.count(Article.id).label('count'),
                    func.avg(Article.opportunity_score).label('avg_score')
                ).where(
                    and_(
                        Article.source == 'openclaw-rss',
                        Article.crawled_at > datetime.now() - timedelta(hours=2)
                    )
                )
            )
            oc_data = oc_result.first()

            return {
                'apscheduler': {
                    'count': aps_data.count or 0,
                    'avg_score': float(aps_data.avg_score or 0)
                },
                'openclaw': {
                    'count': oc_data.count or 0,
                    'avg_score': float(oc_data.avg_score or 0)
                }
            }

    async def check_data_consistency(self):
        """检查数据一致性"""
        # 检查是否有重复数据
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(
                    Article.link,
                    func.count(Article.id).label('count')
                )
                .where(Article.crawled_at > datetime.now() - timedelta(hours=24))
                .group_by(Article.link)
                .having(func.count(Article.id) > 1)
            )
            duplicates = result.all()

            return len(duplicates)

    async def generate_report(self):
        """生成对比报告"""
        articles_comparison = await self.compare_articles()
        duplicate_count = await self.check_data_consistency()

        report = {
            'timestamp': datetime.now().isoformat(),
            'articles': articles_comparison,
            'data_quality': {
                'duplicate_articles_24h': duplicate_count,
                'consistency_score': self._calculate_consistency(articles_comparison)
            },
            'status': 'healthy' if duplicate_count < 10 else 'warning'
        }

        return report

    def _calculate_consistency(self, comparison):
        """计算一致性评分"""
        aps_count = comparison['apscheduler']['count']
        oc_count = comparison['openclaw']['count']

        if aps_count == 0 and oc_count == 0:
            return 1.0

        if aps_count == 0 or oc_count == 0:
            return 0.5

        ratio = min(aps_count, oc_count) / max(aps_count, oc_count)
        return ratio

async def main():
    """主函数"""
    monitor = DualTrackMonitor()
    report = await monitor.generate_report()

    print(f"[{report['timestamp']}] 双轨运行监控报告:")
    print(f"  文章采集:")
    print(f"    APScheduler: {report['articles']['apscheduler']['count']} 篇")
    print(f"    OpenClaw: {report['articles']['openclaw']['count']} 篇")
    print(f"  数据质量:")
    print(f"    24h重复数: {report['data_quality']['duplicate_articles_24h']}")
    print(f"    一致性评分: {report['data_quality']['consistency_score']:.2%}")
    print(f"  状态: {report['status']}")

    # 记录到数据库
    # ...

if __name__ == '__main__':
    asyncio.run(main())
```

### Step 4: 测试执行 (2-3天)

**Day 1: 基础功能测试**
- [ ] OpenClaw RSS Crawler运行正常
- [ ] OpenClaw Content Classifier运行正常
- [ ] 数据正确写入数据库
- [ ] 无重复数据产生

**Day 2: 数据质量对比**
- [ ] 文章数量对比
- [ ] 字段完整性对比
- [ ] AI分类结果对比
- [ ] 性能指标收集

**Day 3: 稳定性验证**
- [ ] 长时间运行稳定性
- [ ] 异常恢复能力
- [ ] 资源使用情况
- [ ] 数据一致性验证

## 验收标准

### 功能验收

- ✅ OpenClaw Channels能正常运行
- ✅ 数据成功写入PostgreSQL
- ✅ APScheduler未受影响
- ✅ 无数据丢失或损坏

### 数据质量验收

- ✅ OpenClaw数据完整度 ≥ APScheduler
- ✅ 数据一致性评分 > 85%
- ✅ 24小时重复数据 < 5%
- ✅ AI分类一致性 > 80%

### 性能验收

- ✅ OpenClaw执行时间 < 2x APScheduler
- ✅ 数据库连接池未耗尽
- ✅ 内存使用 < 150%
- ✅ 成功率 > 95%

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 数据库连接池耗尽 | 高 | 监控连接数，限制并发 |
| 重复数据污染 | 中 | 使用source标记，定期清理 |
| OpenClaw失败影响生产 | 低 | 影子模式，不写入关键表 |
| 资源争用 | 中 | 错峰执行，监控资源 |

## 回滚方案

如果双轨运行出现问题：

```bash
# 1. 立即停止OpenClaw
ssh hk-jump "crontab -l | grep -v openclaw | crontab -"

# 2. 清理影子数据（可选）
DELETE FROM articles WHERE source = 'openclaw-rss';

# 3. 验证APScheduler正常
curl https://api.zenconsult.top/api/v1/batch/status

# 4. 恢复监控
# APScheduler继续正常运行
```

## 成功标准

双轨运行测试通过的标准：

1. **数据质量**: OpenClaw数据质量 ≥ APScheduler
2. **稳定性**: 48小时无故障运行
3. **一致性**: 数据一致性评分 > 85%
4. **性能**: 响应时间在可接受范围内
5. **可运维**: 有完整的监控和告警机制

通过后即可进入Phase 4 - 逐步迁移。

---

**文档版本**: 1.0
**创建日期**: 2026-03-13
**状态**: 准备中
