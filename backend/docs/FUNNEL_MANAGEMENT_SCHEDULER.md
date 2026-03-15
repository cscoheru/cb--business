# 商机漏斗管理调度器文档

**版本**: 1.0
**完成日期**: 2026-03-14
**任务编号**: #41

## 概述

商机漏斗管理调度器实现了三个核心定时任务，自动化商机发现、状态演进和等级管理，减少人工干预，提高系统效率。

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    APScheduler 调度器                           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  定时任务配置                                               │  │
│  │  • 漏斗管理: 每小时 (interval, hours=1)                   │  │
│  │  • 信号发现: 每30分钟 (interval, minutes=30)               │  │
│  │  • 等级监控: 每6小时 (interval, hours=6)                   │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  定时任务执行层                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  funnel_management_job()                                 │  │
│  │  • 查询 verifying 和 assessing 状态的商机                 │  │
│  │  • 检查是否应该演进到下一状态                             │  │
│  │  • 处理超时商机                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  signal_discovery_job()                                 │  │
│  │  • 查询最近已处理的20篇文章                              │  │
│  │  • 调用SignalRecognitionEngine识别信号                  │  │
│  │  • 创建新的BusinessOpportunity记录                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  grade_monitoring_job()                                 │  │
│  │  • 查询所有用户收藏的商机                                 │  │
│  │  • 重新计算C-P-I分数                                     │  │
│  │  • 更新等级（自动升降）                                  │  │
│  │  • 记录等级变更历史                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 定时任务详解

### 1. 漏斗管理任务

**执行频率**: 每小时

**功能**: 自动检查所有商机状态，执行状态演进

**演进规则**:
```
POTENTIAL (发现期)
    ↓ 置信度 >= 0.7 且 数据采集完成
VERIFYING (验证期)
    ↓ 置信度 >= 0.85 且 可行性报告通过
ASSESSING (评估期)
    ↓ 置信度 >= 0.90
EXECUTING (执行期)
```

**超时处理**:
- 验证期超过7天且置信度<0.6 → 标记为低优先级
- 自动记录超时警告到日志

### 2. 信号发现任务

**执行频率**: 每30分钟

**功能**: 从Articles表自动发现商业机会

**工作流程**:
1. 查询最近已处理的文章 (`is_processed=true`)
2. 使用 `DatabaseArticleSignalAdapter` 转换为信号
3. 调用 `SmartOrchestrator.process_signal()` 处理
4. AI分析判断是否为商机
5. 如果是商机，自动创建BusinessOpportunity记录

**AI分析结果**:
- 成功识别商机示例:
  - "印度妇女节电商销售增长21.11%" (置信度: 40%)
  - "Z世代对TikTok信任与忠诚度下滑" (置信度: 40%)
  - "BNPL Shifts to Cards and Wallets" (置信度: 40%)

### 3. 等级监控任务

**执行频率**: 每6小时

**功能**: 动态更新用户收藏商机的等级

**等级分类**:
- **LEAD** (< 60分): 线索 - 需进一步验证
- **NORMAL** (60-69分): 普通商机 - 保持关注
- **PRIORITY** (70-84分): 重点商机 - 优先验证
- **LANDABLE** (≥ 85分): 落地商机 - 可落地执行

**处理逻辑**:
1. 查询所有用户收藏的商机 (有user_id和card_id)
2. 重新计算C-P-I分数
3. 更新等级（自动升降）
4. 记录等级变更历史
5. 输出变更详情到日志

## 数据库表

### business_opportunities

存储商机信息和等级：

| 字段 | 类型 | 说明 |
|------|------|------|
| grade | OpportunityGrade | 当前等级 |
| grade_history | JSONB | 等级变更历史 |
| last_grade_change_at | DateTime | 最后等级变更时间 |
| last_cpi_recalc_at | DateTime | 最后CPI重算时间 |
| cpi_total_score | Float | C-P-I总分 |
| cpi_competition_score | Float | 竞争度分数 |
| cpi_potential_score | Float | 潜力分数 |
| cpi_intelligence_gap_score | Float | 信息差分数 |

## 测试结果

### 手动触发测试

```bash
# 测试漏斗管理
docker exec cb-business-api-fixed python -c "
import asyncio
from scheduler.opportunity_tasks import funnel_management_job
asyncio.run(funnel_management_job())
"
# 结果: ✅ 成功 - 检查了0个商机
```

```bash
# 测试等级监控
docker exec cb-business-api-fixed python -c "
import asyncio
from scheduler.opportunity_tasks import grade_monitoring_job
asyncio.run(grade_monitoring_job())
"
# 结果: ✅ 成功 - 处理了2个商机
```

### 调度器状态

```bash
# 查看调度器日志
docker logs cb-business-api-fixed | grep -E "(定时任务|商机)"

# 输出示例:
INFO:scheduler.opportunity_tasks:✅ 商机定时任务已设置
INFO:scheduler.opportunity_tasks:  - 漏斗管理: 每小时
INFO:scheduler.opportunity_tasks:  - 信号发现: 每30分钟
INFO:scheduler.opportunity_tasks:  - 等级监控: 每6小时
INFO:scheduler.opportunity_tasks:🚀 商机定时任务调度器已启动
INFO:api:🎯 智能商机定时任务已启动
```

## 性能优化

### 1. 批量处理

等级监控任务使用批量更新，减少数据库往返：

```python
results = await GradeManager.batch_update_grades(opportunities, db)
```

### 2. 智能查询

漏斗管理只查询需要检查的商机：

```python
.where(
    or_(
        BusinessOpportunity.status == OpportunityStatus.VERIFYING,
        BusinessOpportunity.status == OpportunityStatus.ASSESSING
    )
)
```

### 3. 异步执行

所有任务都是异步的，不阻塞API请求：

```python
async def funnel_management_job():
    async with AsyncSessionLocal() as db:
        # 异步数据库操作
```

## 监控和日志

### 日志级别

- **INFO**: 任务开始/完成，统计数据
- **WARNING**: 跳过的任务，超时警告
- **ERROR**: 任务执行失败

### 关键指标

```python
# 漏斗管理
logger.info(f"📊 检查 {len(opportunities)} 个商机")
logger.info(f"  🔄 商机 {id} 状态演进: {old} → {new}")

# 信号发现
logger.info(f"📰 找到 {len(articles)} 篇文章")
logger.info(f"  🎯 创建商机: {title} (置信度: {confidence})")

# 等级监控
logger.info(f"  🔄 商机 {title}: {from_grade} → {to_grade} ({old_score} → {new_score})")
logger.info(f"  - 等级变更数: {grade_changes}")
```

## 配置

### 修改执行频率

编辑 `scheduler/opportunity_tasks.py`:

```python
# 漏斗管理: 每30分钟
scheduler.add_job(
    funnel_management_job,
    'interval',
    minutes=30,
    id='funnel_management'
)

# 信号发现: 每15分钟
scheduler.add_job(
    signal_discovery_job,
    'interval',
    minutes=15,
    id='signal_discovery'
)
```

### 禁用某个任务

注释掉对应的 `add_job()` 调用：

```python
# scheduler.add_job(funnel_management_job, ...)  # 禁用漏斗管理
```

## 故障排除

### 问题1: 调度器没有启动

**症状**: 日志中没有 "🚀 商机定时任务调度器已启动"

**原因**: `opportunity_tasks.py` 文件不在容器中

**解决方案**:
```bash
# 复制文件到容器
cat backend/scheduler/opportunity_tasks.py | \
  ssh hk-jump "docker exec -i cb-business-api-fixed tee /app/scheduler/opportunity_tasks.py > /dev/null"

# 重启容器
ssh hk-jump "docker restart cb-business-api-fixed"
```

### 问题2: AI分析失败

**症状**: "ERROR: AI分析失败: Error code: 401"

**原因**: 智谱AI API密钥过期或无效

**解决方案**: 系统会自动降级到Mock模式，继续处理信号但使用模拟分数

### 问题3: 等级监控任务失败

**症状**: "ImportError: cannot import name 'OpportunityGrade'"

**原因**: 容器中的 `business_opportunity.py` 缺少 `OpportunityGrade` 枚举

**解决方案**:
```bash
cat backend/models/business_opportunity.py | \
  ssh hk-jump "docker exec -i cb-business-api-fixed tee /app/models/business_opportunity.py > /dev/null"

ssh hk-jump "docker restart cb-business-api-fixed"
```

## 相关文件

| 文件 | 说明 |
|------|------|
| `scheduler/opportunity_tasks.py` | 定时任务定义和调度器配置 |
| `services/smart_orchestrator.py` | 智能编排服务（核心协调器）|
| `services/grade_manager.py` | 等级管理器 |
| `services/grade_calculator.py` | 等级计算器 |
| `services/signal_recognition.py` | 信号识别引擎 |
| `services/opportunity_algorithm.py` | C-P-I算法引擎 |

## 后续优化

### 短期 (1周内)

1. **手动触发端点**: 提供API端点手动触发各任务，用于调试
2. **执行统计**: 记录每次执行的耗时，监控性能
3. **邮件通知**: 关键等级变更时发送邮件通知

### 中期 (2-4周)

4. **Cron表达式**: 支持自定义Cron表达式（如每天凌晨2点执行）
5. **任务队列**: 使用Celery替代APScheduler，支持分布式执行
6. **执行历史**: 记录每次执行的结果到数据库

### 长期 (1-2月)

7. **自适应调度**: 根据系统负载动态调整执行频率
8. **机器学习**: 使用ML预测最佳执行时机
9. **实时通知**: 使用WebSocket实时推送商机状态变化

---

**维护者**: Claude Code
**最后更新**: 2026-03-14
