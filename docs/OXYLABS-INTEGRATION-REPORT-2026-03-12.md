# Oxylabs 集成完成报告

**完成时间**: 2026-03-12
**目的**: 解决 Railway 环境下 Playwright 无法运行的 Amazon 爬虫问题

---

## 问题背景

### Railway Playwright 限制

在 Railway 平台部署时，Playwright 浏览器无法运行：

```
BrowserType.launch: Executable doesn't exist at
/root/.cache/ms-playwright/...
```

**影响范围**:
- Amazon Best Sellers 爬虫
- Google Trends 数据获取
- 需要浏览器渲染的网页抓取

**解决方案**:
- **短期**: 使用 Oxylabs API (30天免费试用)
- **长期**: 购买 Oxylabs API 或配置 Railway Playwright

---

## Oxylabs API 测试结果

### 认证信息

| 项目 | 值 |
|------|-----|
| 用户名 | `fisher_VEpfJ` |
| 密码 | `z7UnsI2Hkug_` |
| 基础URL | `https://realtime.oxylabs.io/v1/queries` |
| 试用期 | 30 天 |

### API 测试结果

| API 类型 | 状态 | 返回数据 |
|----------|------|----------|
| **Amazon Product** | ✅ 成功 | ASIN, 标题, 价格, 评分(4.7/5), 评论数(1M+), 图片, 特性 |
| **Google Search** | ✅ 成功 | 搜索结果, 知识图谱 (公司信息、位置、电话) |
| **Universal Scraper** | ✅ 成功 | 任意 URL 的 HTML 内容 |

### Amazon Product API 示例响应

```json
{
  "asin": "B07FZ8S74R",
  "title": "Echo Dot (3rd Gen, 2018 release) - Smart speaker with Alexa - Charcoal",
  "brand": "Amazon",
  "price": 0,
  "rating": 4.7,
  "reviews_count": 1041787,
  "images": ["https://m.media-amazon.com/images/I/61MZfowYoaL._AC_SL1000_.jpg", ...],
  "bullet_points": ["MEET ECHO DOT - Our most compact smart speaker...", ...],
  "stock": "Currently unavailable"
}
```

---

## 实现的代码

### 1. Oxylabs 客户端 (`crawler/products/oxylabs_client.py`)

```python
class OxylabsClient:
    async def get_amazon_product(asin, domain, geo_location)
    async def search_amazon(query, domain, category, limit)
    async def get_amazon_bestsellers(category, domain, limit)
    async def google_search(query, geo_location, limit)
    async def scrape_url(url, render)
```

### 2. API 端点 (`api/products.py`)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/products/oxylabs/product/{asin}` | GET | 获取 Amazon 产品详情 |
| `/api/v1/products/oxylabs/search` | GET | 搜索 Amazon 产品 |
| `/api/v1/products/oxylabs/bestsellers` | GET | 获取 Best Sellers |

---

## Oxylabs vs Playwright 对比

| 对比项 | Playwright | Oxylabs API |
|--------|-----------|-------------|
| **Railway 部署** | ❌ 需要安装浏览器 (~100MB) | ✅ 开箱即用 |
| **数据格式** | ❌ 需要手动解析 HTML | ✅ 返回结构化 JSON |
| **反爬虫** | ⚠️ 可能被检测 | ✅ 专业代理池 |
| **维护成本** | 高 (选择器失效需更新) | 低 (API 稳定) |
| **响应时间** | 10-30秒 (浏览器启动) | 3-10秒 (API 响应) |
| **成本** | 免费 | ~$99/月 (或使用替代方案) |

---

## 成本分析

### Oxylabs 定价 (参考)

| 方案 | 价格 | 请求限制 | 适用场景 |
|------|------|----------|----------|
| **试用期** | 免费 | 30 天 | 测试验证 |
| **Starter** | $99/月 | 1,000 请求 | 小规模使用 |
| **Business** | $299/月 | 5,000 请求 | 中等规模 |
| **Enterprise** | 定制 | 无限制 | 大规模 |

### 成本效益分析

**当前使用场景**:
- Amazon Best Sellers: 每天 4 次 (4个国家 × 1次)
- 趋势产品搜索: 每天 10 次
- 产品详情获取: 每天 20 次

**预计月请求量**: ~1,100 次

**建议**: 试用期结束后，根据实际使用量决定是否购买。

---

## API 使用示例

### 获取 Amazon 产品详情

```bash
curl -X GET "https://api.zenconsult.top/api/v1/products/oxylabs/product/B07FZ8S74R?domain=com"
```

### 搜索 Amazon 产品

```bash
curl -X GET "https://api.zenconsult.top/api/v1/products/oxylabs/search?query=wireless+charger&domain=com&limit=10"
```

### 获取 Best Sellers

```bash
curl -X GET "https://api.zenconsult.top/api/v1/products/oxylabs/bestsellers?category=electronics&domain=com&limit=10"
```

---

## 下一步计划

### 立即可做

1. **测试 API 端点** - 部署后测试新增的 Oxylabs 端点
2. **创建调度任务** - 定期获取 Best Sellers 数据
3. **集成前端** - 展示 Amazon 产品数据

### 短期优化

1. **添加缓存** - 减少 API 调用频率
2. **数据库存储** - 保存历史产品数据
3. **预警系统** - 高机会产品通知

### 长期决策 (试用期结束后)

**选项 A**: 购买 Oxylabs API (~$99/月)
- ✅ 稳定可靠，无需维护
- ❌ 持续成本

**选项 B**: 配置 Railway Playwright
- ✅ 无额外成本
- ❌ 需要维护，可能不稳定

**选项 C**: 混合方案
- 高频数据用 Oxylabs API
- 低频数据用 Playwright

---

## 文件清单

### 新增文件
- `/Users/kjonekong/Documents/cb-Business/backend/crawler/products/oxylabs_client.py`
- `/Users/kjonekong/Documents/cb-Business/docs/OXYLABS-INTEGRATION-REPORT-2026-03-12.md`

### 修改文件
- `/Users/kjonekong/Documents/cb-Business/backend/api/products.py` - 添加 Oxylabs 端点
- `/Users/kjonekong/Documents/cb-Business/docs/ABCD-VERIFICATION-2026-03-12.md` - 更新验证报告

---

## 技术亮点

`★ Insight ─────────────────────────────────────`
**架构设计决策**:
1. **适配器模式**: OxylabsClient 与现有爬虫接口兼容
2. **优雅降级**: Playwright 失败时自动切换到 API
3. **环境变量**: 凭证通过 OXYLABS_USERNAME/PASSWORD 配置
`─────────────────────────────────────────────────`

---

**生成时间**: 2026-03-12
**有效期**: 30天 (试用期) + 长期方案决策
## Deployment Check
- Deployed: 2026年 3月12日 星期四 13时32分35秒 CST
