# CB-Business 数据流程断裂分析与修复计划

## Context (问题背景)

CB-Business是一个跨境电商智能信息SaaS平台，用户反馈"数据流程逻辑没有跑通"。通过3轮深入调查，发现了系统中的多个断裂点和架构问题。

**问题表现**：
- 首页文章流显示"加载中..."
- 产品页面品牌显示"N/A"，图片为空白
- 数据重复获取，无统一数据源
- AI分析能力未充分利用

**调查范围**：
1. 数据源集成和数据库存储逻辑
2. 前端展现和缓存机制
3. AI分析、定时任务和数据同步机制

---

## 调查总结

### 发现的核心问题：多套独立数据流程，互不相通

#### 问题1: 数据源架构脱节

**规划架构** (DATA_SOURCE_ARCHITECTURE.md):
```
DataSourceRegistry → OxylabsDataSource + GoogleTrendsDataSource
     ↓
多源聚合 → AI分析 → 卡片生成
```

**实际实现**:
```
CardGenerator → OxylabsClient (直接调用)
     ↓
单一数据源 → 本地统计 → 卡片生成
```

**断裂点**:
- `data_source_init.py` 从未被调用
- `DataSourceRegistry` 已实现但未使用
- `OxylabsDataSource` 适配器已创建但CardGenerator不使用

#### 问题2: Cards系统和Products系统数据流断裂

```
流程A (Cards系统):
  OxylabsClient.search_amazon()
    ↓
  存入 cards.amazon_data (327条记录)
    ↓
  /api/v1/cards/daily → 前端展示 ✅

流程B (Products系统):
  OxylabsClient.get_amazon_bestsellers()
    ↓
  直接返回 (无存储)
    ↓
  /api/v1/products/categories/{id}/trending → 前端展示 ⚠️
```

**问题**:
- 两套独立流程，数据不共享
- Products表为空，products API每次都重新调用Oxylabs
- 分类系统不一致 (Cards用具体类别，Products用大类)

#### 问题3: 前端API调用错误

| 组件 | 调用的API | 实际API | 状态 |
|------|-----------|----------|------|
| 首页文章流 | `/api/v1/crawler/articles` | `/api/v1/crawler-sync/articles` | ❌ 错误 |
| 产品页面 | `/api/v1/products/categories/{id}/trending` | - | ⚠️ HK代码过旧 |
| 商机卡片 | `/api/v1/cards/daily` | - | ✅ 正常 |

#### 问题4: 产品数据字段缺失

| 字段 | Cards数据 | Products API返回 | 根本原因 |
|------|----------|-----------------|---------|
| Brand | ❌ 无 | "N/A" | `amazon_search` API不返回 |
| Image | ❌ 无 | null | `amazon_search` API不返回 |
| ASIN | ✅ 有 | ✅ 有 | - |
| Title | ✅ 有 | ✅ 有 | - |
| Price | ✅ 有 | ✅ 有 | - |

#### 问题5: AI能力未充分利用

**实际情况**:
- Card评分: 本地统计计算 (不是真实AI)
- 文章AI分析: 使用智谱AI (真实AI，但结果未在前端展示)

**价值浪费**:
- AI分析结果 (content_theme, risk_level, opportunity_score) 存在数据库但前端不使用
- 爬虫系统获取的286篇文章数据未与Card生成融合

---

## 完整修复方案

### 方案概述

**目标**: 建立统一的数据管道，让数据流"跑通"

```
统一数据流程:
  爬虫系统 → articles (286条) + AI分析结果
     ↓
  Card生成 → cards (327条) + amazon_data
     ↓
  Products API → 从cards表读取 (避免重复调用)
     ↓
  前端展示 → 统一、完整的数据
```

### 实施步骤

#### Step 1: 快速修复 (1-2小时) - 恢复基本功能

**1.1 修复前端API端点**
```typescript
// frontend/components/home/home-content.tsx
// 修改前: 'https://api.zenconsult.top/api/v1/crawler/articles?per_page=50'
// 修改后:
const url = 'https://api.zenconsult.top/api/v1/crawler-sync/articles?per_page=50';
```

**1.2 部署最新代码到HK服务器**
```bash
# 在HK服务器上
cd /root/cb--business/backend
git pull origin main
docker build -t cb-business-api:latest .
docker stop cb-business-api-fixed && docker rm cb-business-api-fixed
docker run -d --name cb-business-api-fixed --network cb-network -p 8000:8000 ...
```

**1.3 统一Products API数据源**
```python
# backend/api/products_real.py
# 修改前: 直接调用Oxylabs
# 修改后: 从cards表读取数据
async def get_category_trending(category_id: str, limit: int = 24):
    # 从cards表读取已有数据
    result = await db.execute(
        select(Card)
        .where(Card.category == mapped_category)
        .where(Card.amazon_data.isnot(None))
        .order_by(Card.created_at.desc())
        .limit(1)
    )
    card = result.scalar_one_or_none()
    if card and card.amazon_data:
        return {
            "category": category_id,
            "products": card.amazon_data['products'][:limit],
            "count": min(len(card.amazon_data['products']), limit)
        }
    # Fallback: 调用Oxylabs获取
    ...
```

#### Step 2: 数据完整性修复 (2-3小时) - 获取完整字段

**2.1 实现两步数据获取**
```python
# backend/services/product_data_service.py (新建)
class ProductDataService:
    async def get_products_with_details(
        self,
        category: str,
        limit: int = 24
    ) -> List[Dict]:
        # 第1步: 从cards获取ASIN列表
        asin_list = await self._get_asin_list(category, limit)

        # 第2步: 批量获取产品详情
        products = []
        for asin in asin_list[:limit]:
            detail = await self.client.get_amazon_product(asin)
            products.append({
                "asin": asin,
                "title": detail.get("title"),
                "brand": detail.get("brand") or detail.get("manufacturer") or "N/A",
                "price": detail.get("price"),
                "rating": detail.get("rating"),
                "reviews_count": detail.get("reviews_count", 0),
                "image": self._extract_image(detail),
                "url": f"https://www.amazon.com/dp/{asin}"
            })
        return products

    def _extract_image(self, product_data: Dict) -> str:
        images = product_data.get("images", [])
        if images and isinstance(images[0], dict):
            return images[0].get("url")
        return None
```

**2.2 添加分类映射表**
```python
# backend/config/category_mapping.py (新建)
CATEGORY_MAPPING = {
    "electronics": ["wireless_earbuds", "bluetooth_speakers", "phone_chargers"],
    "home": ["desk_lamps", "smart_plugs", "coffee_makers"],
    "sports": ["fitness_trackers", "yoga_mats"],
    # ...
}
```

#### Step 3: 系统优化 (4-6小时) - 提升数据价值

**3.1 激活数据源架构**
```python
# backend/api/__init__.py
@app.on_event("startup")
async def startup_event():
    # 激活数据源注册
    from services.data_source_init import initialize_data_sources
    await initialize_data_sources()
    logger.info("✅ 数据源已注册")
```

**3.2 重构CardGenerator使用DataSourceRegistry**
```python
# backend/services/card_generator_v2.py (新建)
class CardGeneratorV2:
    async def fetch_category_data(self, category: str):
        # 使用统一的数据源注册中心
        data = await data_source_registry.fetch_all(
            category=category,
            query=CATEGORIES[category]['search_query'],
            limit=20
        )
        # 聚合多源数据
        return self._aggregate_data(data)
```

**3.3 优化缓存策略**
```python
# backend/services/cache.py
# 统一缓存时间为30分钟
DEFAULT_TTL = 1800  # 30分钟

# 实现缓存失效机制
async def invalidate_category(category: str):
    await cache_service.delete("products", category)
    await cache_service.delete("cards", category)
```

---

## 详细实施计划

### Phase 1: 快速修复 (Week 1)

**目标**: 恢复基本功能，让系统能正常使用

| 任务 | 文件 | 时间 | 负责人 |
|------|------|------|-------|
| 修复前端API端点 | `frontend/components/home/home-content.tsx` | 5分钟 | - |
| 部署后端代码 | HK服务器 | 15分钟 | - |
| 统一Products API数据源 | `backend/api/products_real.py` | 30分钟 | - |
| 测试验证 | - | 15分钟 | - |

### Phase 2: 数据完整性修复 (Week 1-2)

**目标**: 获取完整的产品数据，改善用户体验

| 任务 | 文件 | 时间 |
|------|------|------|
| 实现ProductDataService | `backend/services/product_data_service.py` | 45分钟 |
| 添加分类映射表 | `backend/config/category_mapping.py` | 20分钟 |
| 更新Products API | `backend/api/products_real.py` | 30分钟 |
| 前端测试 | `frontend/app/products/page.tsx` | 15分钟 |

### Phase 3: 系统优化 (Week 2-3)

**目标**: 提升数据价值，充分利用AI能力

| 任务 | 文件 | 时间 |
|------|------|------|
| 激活数据源架构 | `backend/api/__init__.py` | 10分钟 |
| 重构CardGenerator | `backend/services/card_generator_v2.py` | 60分钟 |
| 优化缓存策略 | `backend/services/cache.py` | 30分钟 |
| 前端展示AI分析 | `frontend/components/cards/card.tsx` | 40分钟 |

---

## 验证方案

### 测试清单

#### 功能测试
- [ ] 访问首页能正常显示文章流和商机卡片
- [ ] 点击关键词能跳转到产品页面
- [ ] 产品页面显示完整数据 (品牌、图片、价格等)
- [ ] 刷新页面数据一致性好

#### API测试
```bash
# 测试Cards API
curl https://api.zenconsult.top/api/v1/cards/daily

# 测试Products API
curl https://api.zenconsult.top/api/v1/products/categories/electronics/trending?limit=5

# 测试Articles API
curl https://api.zenconsult.top/api/v1/crawler-sync/articles?per_page=5
```

#### 性能测试
- [ ] Cards API响应时间 < 1秒
- [ ] Products API响应时间 < 2秒
- [ ] 首页加载时间 < 3秒

### 成功标准

1. **数据一致性**: Products页面和Cards页面使用相同数据源
2. **数据完整性**: 产品包含brand、image等完整字段
3. **用户体验**: 无"加载中..."、无"N/A"、无空白图片
4. **系统性能**: API响应快速，缓存策略合理

---

## 相关文件路径

### 需要修改的文件

| 优先级 | 文件路径 | 修改内容 |
|-------|---------|---------|
| P0 | `frontend/components/home/home-content.tsx` | 修复API端点 |
| P0 | HK服务器部署 | 部署最新代码 |
| P1 | `backend/api/products_real.py` | 从cards表读取数据 |
| P2 | `backend/services/product_data_service.py` | 新建，两步数据获取 |
| P2 | `backend/config/category_mapping.py` | 新建，分类映射 |
| P3 | `backend/api/__init__.py` | 激活数据源架构 |
| P3 | `backend/services/card_generator.py` | 重构使用DataSourceRegistry |

### 参考文件

| 文件路径 | 作用 |
|---------|------|
| `backend/api/cards.py` | Cards API实现，可作为Products API参考 |
| `backend/services/card_generator.py` | Card生成逻辑，了解现有实现 |
| `backend/crawler/products/oxylabs_client.py` | Oxylabs客户端，验证成功的代码 |
| `backend/models/card.py` | 数据模型，了解表结构 |
| `backend/docs/DATA_SOURCE_ARCHITECTURE.md` | 架构文档 |

---

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| HK服务器部署失败 | 高 | 提前备份，保留回滚方案 |
| Oxylabs API限流 | 中 | 使用缓存，控制请求频率 |
| 两步获取导致性能下降 | 中 | 只对前N个产品获取详情，其余用缓存数据 |
| 分类映射不完整 | 低 | 逐步添加，未映射的返回默认类别 |

---

## 后续优化方向

### 短期 (1-2个月)
- 监控数据质量，建立数据质量指标
- 添加更多产品分类
- 优化缓存命中率

### 中期 (3-6个月)
- 实现真正的多数据源聚合 (Google Trends, Reddit等)
- 展示AI分析结果
- 添加用户自定义分类功能

### 长期 (6个月+)
- 机器学习模型优化推荐
- 实时数据同步
- 用户行为分析

---

**文档版本**: 2.0
**最后更新**: 2026-03-13
**状态**: 待审批
