# OpenClaw MCP服务器部署指南 (HK服务器)

## 部署架构

```
HK服务器 (103.59.103.85)
├── OpenClaw Core (18789端口)
│   └── 现有的爬虫调度系统
├── OpenClaw MCP Server (新建)
│   ├── Python MCP封装
│   ├── 3个核心Skills
│   └── 通过stdio与FastAPI通信
└── FastAPI (Docker容器)
    └── 通过MCP客户端调用OpenClaw
```

---

## Step 1: 准备环境

### SSH到HK服务器
```bash
ssh hk-jump  # 本机 → 阿里云 → HK
```

### 检查现有OpenClaw
```bash
# 检查OpenClaw是否运行
curl http://localhost:18789/health

# 检查OpenClaw版本
openclaw --version
```

---

## Step 2: 创建MCP服务器目录

```bash
# 创建项目目录
mkdir -p ~/openclaw-mcp
cd ~/openclaw-mcp

# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 升级pip
pip install --upgrade pip
```

---

## Step 3: 安装依赖

```bash
# 安装MCP SDK和相关依赖
pip install mcp httpx playwright pydantic

# 安装Playwright浏览器 (用于mock_order_analysis)
playwright install chromium
```

---

## Step 4: 部署MCP服务器代码

### 方案A: 直接上传代码 (推荐)

**在本地执行**:
```bash
# 打包代码
cd /Users/kjonekong/Documents/cb-Business/mcp-server/openclaw-mcp
tar -czf openclaw-mcp.tar.gz .

# 上传到HK服务器
scp openclaw-mcp.tar.gz hk-jump:~/
```

**在HK服务器执行**:
```bash
# 解压
cd ~
tar -xzf openclaw-mcp.tar.gz -C ~/openclaw-mcp

# 查看文件
cd ~/openclaw-mcp
ls -la
```

### 方案B: 直接在服务器创建

```bash
# 在HK服务器上创建目录结构
cd ~/openclaw-mcp
mkdir -p openclaw_mcp

# 创建main.py (复制mcp-server/openclaw-mcp/openclaw_mcp/main.py的内容)
cat > openclaw_mcp/main.py << 'EOF'
# (粘贴main.py的完整内容)
EOF
```

---

## Step 5: 配置OpenClaw集成

### 创建OpenClaw Skills配置

```bash
# 创建OpenClaw技能目录
mkdir -p ~/.openclaw/skills

# 创建deep_market_scan技能
cat > ~/.openclaw/skills/deep_market_scan.js << 'EOF'
module.exports = async function(context) {
    const { OxylabsClient } = require('oxylabs-client');
    const client = new OxylabsClient();

    const { category, depth = 50, analyze_brands = true } = context.params;

    // 搜索Amazon产品
    const products = await client.searchAmazon({
        query: CATEGORIES[category]?.query || category,
        page: 1,
        size: depth
    });

    // 分析品牌分布
    const brandCounts = {};
    products.forEach(p => {
        const brand = p.brand || 'Unknown';
        brandCounts[brand] = (brandCounts[brand] || 0) + 1;
    });

    const sortedBrands = Object.entries(brandCounts)
        .sort((a, b) => b[1] - a[1]);

    const brandConcentration = sortedBrands.slice(0, 10)
        .reduce((sum, [, count]) => sum + count, 0) / products.length;

    return {
        success: true,
        data: {
            category: category,
            product_count: products.length,
            brand_concentration: brandConcentration,
            top_brands: sortedBrands.slice(0, 10),
            price_range: {
                min: Math.min(...products.map(p => p.price || 0)),
                max: Math.max(...products.map(p => p.price || 0)),
                avg: products.reduce((sum, p) => sum + (p.price || 0), 0) / products.length
            },
            new_product_count: products.filter(p => {
                const daysOnMarket = (Date.now() - new Date(p.date_first_available)) / (1000 * 60 * 60 * 24);
                return daysOnMarket <= 30;
            }).length
        },
        executed_at: new Date().toISOString()
    };
};
EOF

# 创建mock_order技能
cat > ~/.openclaw/skills/mock_order.js << 'EOF'
module.exports = async function(context) {
    const { asin, quantity = 1, country = 'US' } = context.params;

    // 这里使用Playwright自动化真实下单流程
    // 简化版本返回估算数据

    // 获取产品价格
    const product = await getProductByASIN(asin);

    // 估算FBA费用
    const fbaFee = calculateFBAFee(product.size_tier, product.category);

    // 估算运费
    const shippingCost = estimateShippingCost(asin, quantity, country);

    // 估算税费
    const tax = product.price * 0.08; // 假设8%税率

    return {
        success: true,
        data: {
            asin: asin,
            quantity: quantity,
            product_price: product.price,
            shipping_cost: shippingCost,
            fba_fee: fbaFee,
            tax: tax,
            total_landed_cost: product.price * quantity + shippingCost + fbaFee + tax
        },
        executed_at: new Date().toISOString()
    };
};
EOF

# 创建competitor_watch技能
cat > ~/.openclaw/skills/competitor_watch.js << 'EOF'
module.exports = async function(context) {
    const { asins, duration = 3600, events = ['price_change', 'inventory_change'] } = context.params;

    // 这里应该实现真正的实时监控
    // 简化版本返回当前状态

    const results = [];
    for (const asin of asins) {
        const product = await getProductByASIN(asin);
        results.push({
            asin: asin,
            current_price: product.price,
            stock_status: product.in_stock ? 'in_stock' : 'out_of_stock',
            rating: product.rating,
            reviews_count: product.reviews_count,
            last_updated: new Date().toISOString()
        });
    }

    return {
        success: true,
        data: {
            monitored_asins: asins,
            watch_duration: duration,
            results: results,
            changes_detected: []
        },
        executed_at: new Date().toISOString()
    };
};
EOF
```

---

## Step 6: 配置OpenClaw API路由

```bash
# 配置OpenClaw支持技能执行
cat > ~/.openclaw/config/skills.json << 'EOF'
{
  "skills": {
    "deep_market_scan": {
      "file": "~/.openclaw/skills/deep_market_scan.js",
      "timeout": 60000,
      "description": "深度市场扫描技能"
    },
    "mock_order": {
      "file": "~/.openclaw/skills/mock_order.js",
      "timeout": 120000,
      "description": "模拟下单分析技能"
    },
    "competitor_watch": {
      "file": "~/.openclaw/skills/competitor_watch.js",
      "timeout": 30000,
      "description": "竞品监控技能"
    }
  }
}
EOF
```

---

## Step 7: 启动MCP服务器

### 测试模式 (前台运行)
```bash
cd ~/openclaw-mcp
source venv/bin/activate
python -m openclaw_mcp.main
```

### 生产模式 (后台运行)
```bash
# 创建启动脚本
cat > ~/start-openclaw-mcp.sh << 'EOF'
#!/bin/bash
cd ~/openclaw-mcp
source venv/bin/activate

# 停止旧的MCP进程
pkill -f "python -m openclaw_mcp.main"

# 启动新的MCP进程
nohup python -m openclaw_mcp.main > mcp.log 2>&1 &

echo "OpenClaw MCP Server started, PID: $!"
EOF

chmod +x ~/start-openclaw-mcp.sh

# 执行启动脚本
~/start-openclaw-mcp.sh

# 查看日志
tail -f ~/openclaw-mcp/mcp.log
```

---

## Step 8: 配置FastAPI连接MCP

### 更新backend依赖
```bash
# 在本地更新依赖
cd /Users/kjonekong/Documents/cb-Business/backend

# 添加MCP到requirements.txt
echo "mcp>=0.1.0" >> requirements.txt

# 提交并部署
git add requirements.txt config/mcp_client.py services/ai_orchestrator.py
git commit -m "feat: add OpenClaw MCP integration"
git push origin main
```

### 在HK服务器重启FastAPI
```bash
# 拉取最新代码
ssh hk-jump "cd /root/cb-business-repo/backend && git pull"

# 重启容器
ssh hk-jump "docker restart cb-business-api-fixed"

# 查看日志
ssh hk-jump "docker logs -f cb-business-api-fixed"
```

---

## Step 9: 测试MCP集成

### 测试1: 直接测试MCP服务器
```bash
# 在HK服务器上
cd ~/openclaw-mcp
source venv/bin/activate

# 测试Python导入
python -c "from openclaw_mcp.main import list_tools; print('✅ MCP模块导入成功')"
```

### 测试2: 测试OpenClaw技能
```bash
# 测试deep_market_scan技能
curl -X POST http://localhost:18789/api/skills/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill": "deep_market_scan",
    "params": {
      "category": "wireless_earbuds",
      "depth": 50
    }
  }'
```

### 测试3: 测试FastAPI → MCP → OpenClaw
```bash
# 测试商机生成API
curl -X POST "https://api.zenconsult.top/api/v1/opportunities/generate-from-cards?limit=1" \
  -H "Content-Type: application/json"
```

---

## Step 10: 配置定时任务 (可选)

如果需要保留定时扫描能力：

```bash
# 配置OpenClaw定时任务
cat > ~/.openclaw/schedule.yml << 'EOF'
schedule:
  # 每4小时扫描市场
  - name: market-scan
    cron: "0 */4 * * *"
    channel: deep_market_scan
    params:
      depth: standard

  # 每天分析竞品
  - name: competitor-analysis
    cron: "0 8 * * *"
    channel: competitor_watch
    params:
      duration: 3600
EOF

# 应用配置
openclaw schedule:apply ~/.openclaw/schedule.yml
```

---

## 监控与维护

### 查看MCP日志
```bash
tail -f ~/openclaw-mcp/mcp.log
```

### 查看OpenClaw日志
```bash
openclaw logs
```

### 重启MCP服务
```bash
~/start-openclaw-mcp.sh
```

### 检查连接状态
```bash
# 检查OpenClaw
curl http://localhost:18789/health

# 检查MCP进程
ps aux | grep "openclaw_mcp"
```

---

## 故障排查

### 问题1: MCP导入失败
```bash
# 症状: ImportError: No module named 'mcp'
# 解决: 重新安装依赖
cd ~/openclaw-mcp
source venv/bin/activate
pip install mcp httpx playwright
```

### 问题2: OpenClaw技能无法执行
```bash
# 症状: 404 Not Found /api/skills/execute
# 解决: 检查OpenClaw配置
openclaw config:list
# 确保skills.json存在且格式正确
```

### 问题3: FastAPI无法连接MCP
```bash
# 症状: Connection refused
# 解决: 检查MCP进程是否运行
ps aux | grep openclaw_mcp
# 重启MCP
~/start-openclaw-mcp.sh
```

---

## 成功标志

部署成功的标志：
- ✅ OpenClaw MCP进程运行中 (`ps aux | grep openclaw_mcp`)
- ✅ OpenClaw健康检查通过 (`curl http://localhost:18789/health`)
- ✅ MCP工具列表可获取 (`python -c "from config.mcp_client import get_mcp_client; ..."`)
- ✅ FastAPI能生成商机并调用MCP补齐数据
- ✅ C-P-I分数动态更新

---

**部署检查清单**:
- [ ] MCP服务器代码已部署
- [ ] OpenClaw技能配置已创建
- [ ] MCP服务器进程运行中
- [ ] FastAPI代码已更新
- [ ] FastAPI容器已重启
- [ ] 端到端测试通过

**文档版本**: 1.0
**创建日期**: 2026-03-14
