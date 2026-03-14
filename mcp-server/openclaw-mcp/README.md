# OpenClaw MCP Server - AI驱动的智能体联盟

## 架构转变

### 从前 (定时爬虫)
```
Cron → OpenClaw Channel → 固定URL → 固定频率 → 存入数据库
```

### 到后 (AI驱动)
```
AI分析 → 发现数据缺口 → MCP调用 → OpenClaw Skill → 智能采集 → 回填数据
```

---

## 核心Skills定义

### Skill 1: Deep_Market_Scan
**能力**: 深度市场扫描，根据AI发现的异常趋势自动调整爬取深度

```python
@skill
async def deep_market_scan(
    category: str,
    anomaly_detected: bool = False,
    depth_level: str = "standard"
) -> MarketScanResult:
    """
    深度市场扫描

    Args:
        category: 产品品类
        anomaly_detected: AI是否检测到异常趋势
        depth_level: 扫描深度 (standard/deep/intensive)

    Returns:
        MarketScanResult: 包含趋势数据、竞争分析、价格分布
    """
    if anomaly_detected:
        depth_level = "intensive"  # 自动升级扫描深度

    # 调用OpenClaw执行采集
    return await openclaw_client.execute_scan(category, depth_level)
```

**AI触发场景**:
- 分析Card时发现某品类搜索量突然上升
- 竞品数量异常波动
- 价格战迹象

---

### Skill 2: Mock_Order_Analysis
**能力**: 使用Playwright模拟真实下单流，提取运费、税费及库存限制

```python
@skill
async def mock_order_analysis(
    asin: str,
    quantity: int = 1,
    shipping_address: Dict = None
) -> OrderAnalysisResult:
    """
    模拟下单分析

    提取真实成本构成: 产品价格 + 运费 + 税费 + 履约费

    Args:
        asin: Amazon产品ASIN
        quantity: 购买数量
        shipping_address: 配送地址 (默认为美国仓库地址)

    Returns:
        OrderAnalysisResult: 真实成本构成分析
    """
    # 使用Playwright自动化下单流程
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 导航到产品页面
        await page.goto(f"https://www.amazon.com/dp/{asin}")

        # 添加到购物车
        await page.click("#add-to-cart-button")

        # 进入结账流程 (但不实际付款)
        await page.goto("https://www.amazon.com/gp/cart/view.html")

        # 提取运费、税费信息
        shipping_cost = await page.extract_shipping_cost()
        tax_estimate = await page.extract_tax_estimate()

        await browser.close()

        return OrderAnalysisResult(
            asin=asin,
            shipping_cost=shipping_cost,
            tax_estimate=tax_estimate,
            fulfillment_fee=await calculate_fba_fee(asin),
            total_landed_cost=shipping_cost + tax_estimate
        )
```

**AI触发场景**:
- 计算真实利润率时需要准确成本
- 验证供应商声称的价格
- 发现隐藏费用

---

### Skill 3: Competitor_Dynamic_Watch
**能力**: 实时监控竞品页面DOM变动

```python
@skill
async def competitor_dynamic_watch(
    asins: List[str],
    watch_duration: int = 3600,
    trigger_events: List[str] = ["price_change", "inventory_change"]
) -> CompetitorUpdateResult:
    """
    竞品动态监控

    实时监控竞品页面，捕获价格、库存、评价等关键变化

    Args:
        asins: 要监控的ASIN列表
        watch_duration: 监控时长 (秒)
        trigger_events: 触发事件类型

    Returns:
        CompetitorUpdateResult: 变化记录和预警
    """
    watcher = DOMWatcher(asins)

    async for event in watcher.watch(duration=watch_duration):
        if event.type in trigger_events:
            # AI分析事件影响
            impact = await ai.analyze_competitor_change(event)

            if impact.severity > 0.7:
                # 立即预警
                await alert_manager.send_alert(event, impact)

    return watcher.get_summary()
```

**AI触发场景**:
- 关键竞品突然降价
- 库存紧张/缺货
- 新品上架抢占市场

---

## MCP封装实现

### MCP Server结构
```
mcp-server/
├── openclaw-mcp/
│   ├── __init__.py
│   ├── main.py              # MCP服务器入口
│   ├── skills/
│   │   ├── deep_market_scan.py
│   │   ├── mock_order_analysis.py
│   │   └── competitor_watch.py
│   ├── client/
│   │   └── openclaw_client.py  # OpenClaw客户端封装
│   └── config.yaml            # MCP配置
└── pyproject.toml
```

### main.py - MCP服务器入口
```python
from mcp.server import Server
from mcp.types import Tool, TextContent
import httpx

app = Server("openclaw-mcp-server")

# OpenClaw客户端
OPENCLAW_HK_URL = "http://103.59.103.85:18789"
OPENCLAW_ALIYUN_URL = "http://[阿里云IP]:18789"

async def call_openclaw(skill: str, params: dict) -> dict:
    """调用OpenClaw执行技能"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OPENCLAW_HK_URL}/api/skills/execute",
            json={"skill": skill, "params": params}
        )
        return response.json()

@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的OpenClaw技能"""
    return [
        Tool(
            name="deep_market_scan",
            description="深度市场扫描，分析产品竞争格局、价格分布、增长趋势",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "anomaly_detected": {"type": "boolean"},
                    "depth_level": {"type": "string", "enum": ["standard", "deep", "intensive"]}
                },
                "required": ["category"]
            }
        ),
        Tool(
            name="mock_order_analysis",
            description="模拟下单分析，获取真实运费、税费、履约费",
            inputSchema={
                "type": "object",
                "properties": {
                    "asin": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "shipping_country": {"type": "string"}
                },
                "required": ["asin"]
            }
        ),
        Tool(
            name="competitor_watch",
            description="实时监控竞品动态，捕获价格/库存变化",
            inputSchema={
                "type": "object",
                "properties": {
                    "asins": {"type": "array", "items": {"type": "string"}},
                    "watch_duration": {"type": "integer"},
                    "trigger_events": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["asins"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """AI调用OpenClaw技能"""
    try:
        result = await call_openclaw(name, arguments)
        return [TextContent(type="text", text=f"执行成功: {json.dumps(result, ensure_ascii=False)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"执行失败: {str(e)}")]
```

---

## AI驱动的需求闭环

### 场景1: 数据置信度不足触发补齐

```python
# backend/services/ai_opportunity_analyzer.py

class AIOpportunityAnalyzer:
    async def analyze_with_verification(
        self,
        card: Card,
        db: AsyncSession
    ) -> OpportunityAnalysis:
        # 1. 初步分析
        initial_score = await opportunity_scorer.calculate_opportunity_score(card, db)

        # 2. 检查数据完整性
        data_gaps = self._identify_data_gaps(initial_score)

        # 3. 如果有数据缺口，通过MCP调用OpenClaw补齐
        if data_gaps:
            for gap in data_gaps:
                if gap['type'] == 'competition':
                    # AI主动调用MCP
                    result = await mcp_client.call_tool(
                        "deep_market_scan",
                        {
                            "category": card.category,
                            "anomaly_detected": True,
                            "depth_level": "deep"
                        }
                    )
                    # 将结果回填到card
                    card.competition_data = result

                elif gap['type'] == 'cost_verification':
                    # 模拟下单验证成本
                    top_asin = card.amazon_data['products'][0]['asin']
                    result = await mcp_client.call_tool(
                        "mock_order_analysis",
                        {"asin": top_asin, "quantity": 10}
                    )
                    card.real_cost_data = result

            # 4. 重新计算分数
            final_score = await opportunity_scorer.calculate_opportunity_score(card, db)

            return OpportunityAnalysis(
                initial_score=initial_score,
                data_gaps_filled=data_gaps,
                final_score=final_score,
                confidence_improvement=final_score['total_score'] - initial_score['total_score']
            )

        return initial_score
```

### 场景2: 异常趋势自动触发深度扫描

```python
# backend/services/trend_anomaly_detector.py

class TrendAnomalyDetector:
    async def detect_and_investigate(
        self,
        category: str,
        time_range: str = "7d"
    ):
        # 1. 获取历史趋势数据
        historical_data = await self._get_historical_trends(category, time_range)

        # 2. AI检测异常
        anomalies = await ai.detect_anomalies(historical_data)

        # 3. 如果发现异常，自动触发深度扫描
        for anomaly in anomalies:
            if anomaly.severity > 0.7:
                # 通过MCP调用OpenClaw
                scan_result = await mcp_client.call_tool(
                    "deep_market_scan",
                    {
                        "category": category,
                        "anomaly_detected": True,
                        "depth_level": "intensive"
                    }
                )

                # AI分析扫描结果
                insight = await ai.analyze_market_change(
                    anomaly,
                    scan_result
                )

                # 生成预警
                await alert_manager.send_alert(
                    title=f"🚨 {category}市场异常",
                    insight=insight,
                    action_required=True
                )
```

---

## 配置文件

### pyproject.toml
```toml
[project]
name = "openclaw-mcp"
version = "0.1.0"
dependencies = [
    "mcp>=0.1.0",
    "httpx>=0.25.0",
    "playwright>=1.40.0",
    "pydantic>=2.0.0"
]

[project.scripts]
openclaw-mcp = "openclaw_mcp.main:main"
```

### config/mcp.json
```json
{
  "mcpServers": {
    "openclaw-hk": {
      "command": "uvx",
      "args": ["openclaw-mcp"],
      "env": {
        "OPENCLAW_BASE_URL": "http://103.59.103.85:18789"
      }
    },
    "openclaw-aliyun": {
      "command": "uvx",
      "args": ["openclaw-mcp"],
      "env": {
        "OPENCLAW_BASE_URL": "http://[阿里云IP]:18789",
        "REGION": "CN"
      }
    }
  }
}
```

---

## 部署步骤

### 1. 在HK服务器创建MCP服务
```bash
# SSH到HK服务器
ssh hk-jump

# 创建MCP目录
mkdir -p ~/openclaw-mcp
cd ~/openclaw-mcp

# 初始化Python项目
python3 -m venv venv
source venv/bin/activate
pip install mcp httpx playwright

# 安装Playwright浏览器
playwright install chromium
```

### 2. 部署MCP服务器代码
```bash
# 上传代码到HK服务器
scp -r mcp-server/openclaw-mcp hk-jump:~/openclaw-mcp/

# 在HK服务器启动MCP服务
cd ~/openclaw-mcp
nohup python -m openclaw_mcp > mcp.log 2>&1 &
```

### 3. 在FastAPI配置MCP客户端
```python
# backend/config/mcp_client.py

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class OpenClawMCPClient:
    def __init__(self):
        self.session = None

    async def connect(self):
        server_params = StdioServerParameters(
            command="uvx",
            args=["openclaw-mcp"]
        )
        stdio_context = stdio_client(server_params)
        self.stdio_context = stdio_context
        self.session = await stdio_context.__aenter__()

    async def call_tool(self, name: str, arguments: dict):
        if not self.session:
            await self.connect()

        result = await self.session.call_tool(name, arguments)
        return result

# 全局单例
openclaw_mcp = OpenClawMCPClient()
```

### 4. 测试AI驱动闭环
```bash
# 在Claude Desktop或Cursor中配置MCP
# Claude Desktop: ~/.config/claude/claude_desktop_config.json
# Cursor: Settings → MCP Servers

# 测试对话:
"""
请分析一下无线耳机品类的市场机会。如果发现竞争度数据不足，
自动调用OpenClaw的deep_market_scan技能补齐数据。
"""
```

---

## 监控指标

| 指标 | 说明 | 目标值 |
|------|------|--------|
| AI触发率 | AI主动调用OpenClaw的比例 | > 60% |
| 数据补齐成功率 | MCP调用成功率 | > 95% |
| 响应时间 | 从AI决策到OpenClaw返回数据 | < 30秒 |
| 异常捕获率 | 异常趋势被及时发现的比率 | > 80% |
| 成本节省度 | 相比全量爬取节省的资源 | > 50% |

---

**文档版本**: 1.0
**创建日期**: 2026-03-14
**状态**: 设计完成，待实施
