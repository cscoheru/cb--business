# AI + OpenClaw 智能联盟 - 工作流程文档

> **版本**: 1.0
> **更新日期**: 2026-03-16
> **作者**: Claude AI

---

## 一、概述

AI + OpenClaw 智能联盟是一个自动化数据采集和分析系统，核心目标: 当商机CPI分数较低或数据不足时，自动调用OpenClaw采集补充数据，从而提升商机评估的置信度和准确性

## 二、系统架构
```
┌─────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                               │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │  AI Orchestrator │ ←→ │   MCP Client     │ ←→ │   APScheduler    │  │
│  │  (缺口识别/决策)  │    │  (HTTP Protocol) │    │  (定时任务)    │  │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘  │
│           │                      │                       │                  │
└───────────┼──────────────────────┬───────────────────────┘
            │                      │
            ▼                      ▼
    ┌─────────────────────────────────────────┐
    │              OpenClaw MCP Server                  │
    │  ┌──────────────────┐    ┌──────────────────┐    │
    │  │  deep_market_scan │    │ mock_order_analysis │    │
    │  └──────────────────┘    └──────────────────┘    │
    │  ┌──────────────────┐    ┌──────────────────┐    │
    │  │ competitor_watch │    │  (其他扩展工具)   │    │
    │  └──────────────────┘    └──────────────────┘    │
│           │                      │                        │
└───────────┼──────────────────────┬────────────────────────┘
            │                      │
            ▼                      ▼
    ┌─────────────────────────────────────────┐
    │            OpenClaw Gateway                  │
    │        (电商数据采集网关)                    │
    │  ┌──────────────────────────────────────┐  │
    │  │  Amazon / Shopee / Lazada / 1688...  │  │
    │  └──────────────────────────────────────┘  │
    └─────────────────────────────────────────┘
```

---

## 三、核心组件

### 3.1 AI Orchestrator (智能编排器)
**文件**: `services/ai_orchestrator.py`

**职责**:
- 分析商机数据完整性
- 识别数据缺口类型
- 决定需要调用的 MCP 工具
- 处理采集结果并更新 CPI

### 3.2 MCP Client (MCP 客户端)
**文件**: `config/mcp_client.py`

**协议**: HTTP (非 stdio)

**可用工具**:
| 工具名称 | 功能 | 参数 |
|---------|------|------|
| `deep_market_scan` | 深度市场扫描 | category, anomaly_detected, depth_level |
| `mock_order_analysis` | 订单分析 | category, region |
| `competitor_watch` | 竞争对手监控 | category, competitors |

### 3.3 APScheduler (定时任务)
**文件**: `scheduler/opportunity_tasks.py`

**定时任务**:
| 任务 | 频率 | 功能 |
|------|------|------|
| `data_gap_filling_job` | 每 2 小时 | AI 分析数据缺口，调用 MCP 填补 |
| `opportunity_deep_analysis_job` | 每 4 小时 | 深度分析商机 |
| `funnel_management_job` | 每 1 小时 | 漏斗状态管理 |
| `signal_discovery_job` | 每 30 分钟 | 信号发现 |
| `grade_monitoring_job` | 每 6 小时 | 等级监控 |

---

## 四、数据缺口类型

### 4.1 缺口识别规则

```python
# 商机评分 < 70 或 24 小时未更新
if opportunity.cpi_total_score < 70 or
   (now - opportunity.last_cpi_recalc_at) > 24h:
    # 需要深度分析
```

### 4.2 缺口类型与处理
| 缺口类型 | 描述 | 调用工具 |
|---------|------|----------|
| `competition_deep_scan` | 竞争数据不足 | `deep_market_scan(depth_level="deep")` |
| `potential_trend_verification` | 趋势数据待验证 | `deep_market_scan(anomaly_detected=True)` |
| `insufficient_product_data` | 产品数据不足 | `deep_market_scan(depth_level="intensive")` |

---

## 五、工作流程实例

### 5.1 触发方式

**方式一: 定时自动触发**
```
数据缺口分析: 每 2 小时
商机深度分析: 每 4 小时
漏斗管理: 每 1 小时
信号发现: 每 30 分钟
等级监控: 每 6 小时
```

**方式二: 手动触发 (API)**
```bash
# 触发数据缺口填补
curl -X POST "https://api.zenconsult.top/api/v1/ai-alliance/trigger/data-gap-filling"

# 触发深度分析
curl -X POST "https://api.zenconsult.top/api/v1/ai-alliance/trigger/deep-analysis"
```

### 5.2 实际执行日志 (2026-03-16)

```
INFO:scheduler.opportunity_tasks:🤖 [AI联盟] 开始数据缺口填补任务
INFO:scheduler.opportunity_tasks:🤖 [AI联盟] 分析商机: 商机: phone_cases... (当前CPI: 43.0)
INFO:services.ai_orchestrator:识别到 3 个数据缺口
INFO:config.mcp_client:调用HTTP MCP工具: deep_market_scan, 参数: {"category": "phone_cases", ...}
INFO:httpx:HTTP Request: POST http://openclaw-mcp-server:8001/tools/deep_market_scan "HTTP/1.1 200 OK"
INFO:services.ai_orchestrator:成功填补数据缺口: competition_deep_scan
INFO:services.ai_orchestrator:成功填补数据缺口: potential_trend_verification
INFO:services.ai_orchestrator:成功填补数据缺口: insufficient_product_data
INFO:scheduler.opportunity_tasks:🤖 [AI联盟] ✅ 商机更新完成: phone_cases (43.0 → 61.0, +18.0)
```

### 5.3 CPI 提升示例
```
商机: phone_cases
  - 分析前 CPI: 43.0
  - 分析后 CPI: 61.0
  - 提升幅度: +18.0 (41.9%)

商机: fitness_trackers
  - 分析前 CPI: 43.1
  - 分析后 CPI: 61.1
  - 提升幅度: +18.0 (41.8%)
```

---

## 六、API 端点

### 6.1 状态查询
```http
GET /api/v1/ai-alliance/status
```

**响应示例**:
```json
{
  "status": "active",
  "mcp": {
    "connected": true,
    "server_url": "http://openclaw-mcp-server:8001",
    "available_tools": ["deep_market_scan", "mock_order_analysis", "competitor_watch"]
  },
  "openclaw_gateway": {
    "healthy": true,
    "channels_count": 0
  },
  "stats": {
    "opportunities_analyzed": 315,
    "data_gaps_filled": 6,
    "deep_scans_completed": 6,
    "confidence_improvement_avg": 18.0
  },
  "scheduler_jobs": [...],
  "recent_logs": [...]
}
```

### 6.2 手动触发
```http
POST /api/v1/ai-alliance/trigger/data-gap-filling
POST /api/v1/ai-alliance/trigger/deep-analysis
```

### 6.3 健康检查
```http
GET /api/v1/ai-alliance/health
```

---

## 七、监控指标
| 指标 | 正常范围 | 告警阈值 |
|-----|---------|---------|
| MCP 连接状态 | connected | disconnected |
| OpenClaw 健康 | healthy | unhealthy |
| 数据缺口填补成功率 | > 90% | < 70% |
| CPI 提升均值 | > 5 | < 0 |
| 任务执行时间 | < 30s | > 60s |

---

## 八、部署信息

### 8.1 服务端点
| 服务 | URL | 端口 |
|-----|-----|-----|
| FastAPI Backend | api.zenconsult.top | 443 (HTTPS) |
| OpenClaw MCP Server | openclaw-mcp-server | 8001 (内部) |
| OpenClaw Gateway | 103.59.103.85 | 18789 |

### 8.2 Docker 容器
```bash
# 查看 API 容器状态
docker ps --filter "name=cb-business-api-fixed"

# 查看日志
docker logs cb-business-api-fixed --tail 100

# 重启服务
docker restart cb-business-api-fixed
```

---

## 九、故障排查

### 9.1 常见问题

**Q1: MCP 连接失败**
```
症状: mcp.connected = false
排查步骤:
1. 检查 openclaw-mcp-server 容器状态
2. 验证网络连通性: curl http://openclaw-mcp-server:8001/health
3. 检查 MCP Server 日志
```

**Q2: 数据缺口未被填补**
```
症状: stats.data_gaps_filled = 0
排查步骤:
1. 检查是否有商机需要分析 (cpi_total_score < 70)
2. 验证 MCP 工具是否可用
3. 查看 AI Orchestrator 日志
```

**Q3: CPI 分数未提升**
```
症状: confidence_improvement_avg = 0
排查步骤:
1. 检查数据采集结果是否有效
2. 验证 CPI 计算逻辑
3. 确认商机状态是否允许更新
```

---

## 十、总结

AI + OpenClaw 智能联盟实现了:

1. **自动化数据增强**: AI 识别缺口 → MCP 采集 → 自动更新 CPI
2. **CPI 动态优化**: 平均提升 18+ 分 (约 42%)
3. **多工具协作**: 支持深度扫描、订单分析、竞对监控
4. **灵活触发**: 支持定时自动和手动触发两种模式
5. **实时监控**: 提供完整的状态 API 和日志追踪

**核心价值**: 将静态商机数据转化为动态跟踪系统
持续优化商机评估的准确性和时效性

---

## 十一、参考文件

| 文件 | 路径 | 说明 |
|------|------|------|
| AI Orchestrator | `services/ai_orchestrator.py` | 智能编排核心逻辑 |
| MCP Client | `config/mcp_client.py` | HTTP MCP 客户端 |
| 定时任务 | `scheduler/opportunity_tasks.py` | APScheduler 任务定义 |
| AI 联盟 API | `api/ai_alliance.py` | 状态查询和触发端点 |
| 前端组件 | `components/dashboard/AIAllianceStatus.tsx` | Dashboard 状态展示 |
