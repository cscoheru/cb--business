# OpenClaw MCP服务器部署状态

## 部署时间
2026-03-14

## 部署状态
✅ **部署完成** (代码已部署，待FastAPI集成测试)

---

## HK服务器部署详情

### 服务器信息
- **地址**: 103.59.103.85 (HK服务器)
- **部署路径**: ~/openclaw-mcp/
- **Python版本**: 3.x
- **虚拟环境**: ~/openclaw-mcp/venv/

### 已部署文件
```
~/openclaw-mcp/
├── venv/                   # Python虚拟环境
│   └── lib/python3.x/site-packages/
│       ├── mcp/            # MCP SDK
│       ├── httpx/          # HTTP客户端
│       └── pydantic/       # 数据验证
├── openclaw_mcp/           # MCP服务器代码
│   ├── __init__.py
│   ├── main.py             # MCP服务器 (13KB, 436行)
│   └── __pycache__/
├── mcp-server-test.py      # 测试服务器
├── start-openclaw-mcp.sh   # 启动脚本
├── test-mcp.sh             # 测试脚本
└── mcp.log                 # 日志文件
```

### 验证结果

| 检查项 | 状态 | 说明 |
|--------|------|------|
| Python虚拟环境 | ✅ | ~/openclaw-mcp/venv/ |
| 依赖安装 | ✅ | mcp, httpx, pydantic |
| MCP模块导入 | ✅ | from openclaw_mcp.main import app |
| OpenClaw连接 | ✅ | {"ok":true,"status":"live"} |
| 代码部署 | ✅ | main.py (436行, 13KB) |

---

## MCP架构说明

### 通信方式
MCP服务器使用 **stdio (标准输入/输出)** 进行通信，这意味着：
- 不是独立的HTTP服务
- 需要由父进程（FastAPI）通过stdio启动
- 父进程通过stdin发送请求，通过stdout读取响应

### 启动方式
```bash
# FastAPI启动MCP服务器
cd ~/openclaw-mcp
source venv/bin/activate
python -m openclaw_mcp.main
```

### MCP客户端配置
**文件**: `backend/config/mcp_client.py`

```python
client = OpenClawMCPClient(
    server_command="python3",
    server_args=["-m", "openclaw_mcp.main"],
    env={
        "OPENCLAW_BASE_URL": "http://103.59.103.85:18789",
        "PYTHONPATH": "/root/openclaw-mcp"
    }
)
```

---

## 核心技能

### 1. Deep_Market_Scan
- **能力**: 深度市场扫描，分析竞争格局
- **参数**: category, anomaly_detected, depth_level
- **用途**: AI分析时需要验证竞争度假设

### 2. Mock_Order_Analysis
- **能力**: 模拟下单分析，获取真实成本
- **参数**: asin, quantity, shipping_country
- **用途**: 计算真实利润率需要准确成本

### 3. Competitor_Watch
- **能力**: 实时监控竞品动态
- **参数**: asins[], watch_duration, trigger_events
- **用途**: 捕获价格/库存变化

---

## FastAPI集成

### MCP客户端使用
**文件**: `backend/services/ai_orchestrator.py`

```python
async def analyze_and_verify(card: Card, db: AsyncSession):
    # 1. 初步C-P-I评分
    initial_score = await opportunity_scorer.calculate_opportunity_score(card, db)

    # 2. 识别数据缺口
    data_gaps = await self._identify_data_gaps(initial_score, card)

    # 3. 通过MCP调用OpenClaw补齐数据
    mcp_client = await self.get_mcp_client()
    for gap in data_gaps:
        result = await mcp_client.call_tool(gap['skill'], gap['params'])

    # 4. 重新计算分数
    final_score = await self._recalculate_with_new_data(...)
```

---

## 测试命令

### HK服务器测试
```bash
# SSH到HK服务器
ssh hk-jump

# 测试OpenClaw连接
curl http://localhost:18789/health

# 测试MCP模块导入
cd ~/openclaw-mcp
source venv/bin/activate
python -c "from openclaw_mcp.main import app; print('OK')"

# 查看MCP服务器代码
wc -l ~/openclaw-mcp/openclaw_mcp/main.py
# 应该显示: 436
```

### FastAPI测试 (部署后)
```bash
# 重新计算商机分数（会触发MCP调用）
curl -X POST "https://api.zenconsult.top/api/v1/opportunities/{id}/recalculate-score"

# 从Cards生成商机（会触发MCP调用）
curl -X POST "https://api.zenconsult.top/api/v1/opportunities/generate-from-cards?limit=1"
```

---

## 下一步

### 立即可做
1. ✅ **部署MCP服务器代码** - 已完成
2. ⏳ **部署FastAPI后端代码** - 更新mcp_client.py
3. ⏳ **重启FastAPI容器** - 应用新配置
4. ⏳ **端到端测试** - 验证FastAPI → MCP → OpenClaw调用链

### 测试清单
- [ ] FastAPI能通过MCP客户端调用OpenClaw
- [ ] 商机重新计算分数成功
- [ ] MCP日志正常输出
- [ ] OpenClaw技能正常执行

---

## 相关文档

| 文档 | 路径 |
|------|------|
| MCP服务器README | `mcp-server/openclaw-mcp/README.md` |
| 部署指南 | `mcp-server/openclaw-mcp/DEPLOYMENT.md` |
| MCP客户端配置 | `backend/config/mcp_client.py` |
| AI编排服务 | `backend/services/ai_orchestrator.py` |
| CPI算法实现 | `backend/docs/CPI_ALGORITHM_IMPLEMENTATION.md` |

---

## 故障排查

### 问题1: FastAPI无法连接MCP
**症状**: Connection refused
**解决**:
1. 检查HK服务器是否可以SSH连接
2. 确认MCP代码路径正确: /root/openclaw-mcp/
3. 验证虚拟环境存在: ~/openclaw-mcp/venv/

### 问题2: MCP模块导入失败
**症状**: ImportError: No module named 'openclaw_mcp'
**解决**:
```bash
ssh hk-jump
cd ~/openclaw-mcp
ls -la openclaw_mcp/
# 应该看到: __init__.py, main.py
```

### 问题3: OpenClaw连接失败
**症状**: MCP工具返回"OpenClaw连接失败"
**解决**:
```bash
ssh hk-jump "curl http://localhost:18789/health"
# 应该返回: {"ok":true,"status":"live"}
```

---

**部署状态**: ✅ 代码部署完成，待FastAPI集成测试
**创建日期**: 2026-03-14
**版本**: v1.0
