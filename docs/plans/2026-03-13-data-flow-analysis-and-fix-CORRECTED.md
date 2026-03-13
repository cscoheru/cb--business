# CB-Business 数据流程断裂分析与修复计划 (修正版)

## Context (问题背景)

CB-Business是一个跨境电商智能信息SaaS平台，用户反馈"数据流程逻辑没有跑通"。通过深入调查，发现了**代码版本不一致**导致的多个断裂点。

**调查发现**:
- **本地代码**: 最新版本，包含 `get_amazon_bestsellers()` 方法
- **HK服务器代码**: 过旧版本，缺少关键方法
- **前端代码**: API端点错误
- **数据库连接**: crawler-sync 无法连接到 PostgreSQL

---

## 核心问题 (按优先级)

### 🔴 P0 - 代码版本不一致 (CRITICAL)

**问题**: HK服务器运行的代码版本过旧

| 组件 | 本地版本 | HK服务器版本 |
|------|---------|-------------|
| OxylabsClient | 有 `get_amazon_bestsellers()` | ❌ 缺失 |
| 数据源架构 | 已实现但未激活 | ❌ 未激活 |

**影响**:
- Products API 抛出 `'OxylabsClient' object has no attribute 'get_amazon_bestsellers'`
- Cards API 正常工作 (使用 `search_amazon()`)
- 前端 Products 页面无法显示数据

**修复**: 部署最新代码到HK服务器

### 🔴 P0 - 前端API端点错误

**问题**: `home-content.tsx` 调用错误的API

```typescript
// 当前 (错误)
const response = await fetch('https://api.zenconsult.top/api/v1/crawler/articles?per_page=50');

// 应该是
const response = await fetch('https://api.zenconsult.top/api/v1/crawler-sync/articles?per_page=50');
```

**影响**: 首页文章流显示"加载中..."

### 🟠 P1 - crawler-sync 数据库连接问题

**问题**: crawler-sync API 无法连接到 PostgreSQL

```bash
curl 'https://api.zenconsult.top/api/v1/crawler-sync/articles?per_page=1'
# 返回: "could not translate host name \"postgres\" to address"
```

**根本原因**: Docker 服务名配置问题
- `DATABASE_URL` 中使用 `postgres` 作为主机名
- 但 docker-compose 中服务名是 `cb-business-postgres`

### 🟡 P2 - Products API 数据源问题

**问题**: Products API 应该从 cards 表读取，而不是每次调用 Oxylabs

**当前流程** (错误):
```
前端请求 → Products API → Oxylabs API (每次调用)
```

**应该的流程**:
```
前端请求 → Products API → cards 表 (已有 amazon_data)
                              ↓
                          缓存未命中 → Oxylabs API
```

---

## 修复方案 (按优先级)

### Phase 1: 代码同步 (30分钟) - **必须先完成**

#### Step 1.1: 部署最新后端代码到HK

```bash
# SSH到HK服务器
ssh hk-jump

# 拉取最新代码
cd /root/cb-business/backend
git pull origin main

# 重新构建镜像
docker build -t cb-business-api:latest .

# 停止并删除旧容器
docker stop cb-business-api-fixed
docker rm cb-business-api-fixed

# 启动新容器 (确保连接到 cb-network)
docker run -d \
  --name cb-business-api-fixed \
  --network cb-network \
  -p 8000:8000 \
  -e DATABASE_URL='postgresql://cbuser:cbuser123_2026@cb-business-postgres:5432/cbdb' \
  cb-business-api:latest

# 验证
docker logs cb-business-api-fixed
```

#### Step 1.2: 修复前端API端点

```typescript
// frontend/components/home/home-content.tsx
// 第20行
- const response = await fetch('https://api.zenconsult.top/api/v1/crawler/articles?per_page=50');
+ const response = await fetch('https://api.zenconsult.top/api/v1/crawler-sync/articles?per_page=50');
```

```bash
# 部署前端
cd /Users/kjonekong/Documents/cb-Business/frontend
npx vercel --prod
```

#### Step 1.3: 修复数据库连接配置

```python
# backend/.env.prod 或 docker-compose.yml
# 确保 DATABASE_URL 使用正确的服务名
DATABASE_URL=postgresql://cbuser:cbuser123_2026@cb-business-postgres:5432/cbdb
```

---

### Phase 2: 数据源优化 (2小时)

#### Step 2.1: 修改 Products API 从 cards 表读取

```python
# backend/api/products_real.py
async def get_category_trending(category_id: str, limit: int = Query(10, ge=1, le=50)):
    """获取指定类别的热门产品 (优先从 cards 表读取)"""

    if category_id not in AMAZON_CATEGORIES:
        return {"error": "Invalid category", "products": []}

    cat_info = AMAZON_CATEGORIES[category_id]
    mapped_category = cat_info["amazon_path"]

    # 1. 先尝试从 cards 表读取
    try:
        from models.card import Card
        result = await db.execute(
            select(Card)
            .where(Card.category == mapped_category)
            .where(Card.amazon_data.isnot(None))
            .order_by(Card.created_at.desc())
            .first()
        )
        card = result.scalar_one_or_none()

        if card and card.amazon_data:
            products = card.amazon_data.get('products', [])[:limit]
            logger.info(f"返回 cards 表数据: {len(products)} 个产品")
            return {
                "category": category_id,
                "products": products,
                "count": len(products),
                "source": "cards_cache"
            }
    except Exception as e:
        logger.warning(f"从 cards 表读取失败: {e}")

    # 2. Fallback: 调用 Oxylabs
    try:
        client = OxylabsClient()
        products = await client.get_amazon_bestsellers(
            category=cat_info["amazon_path"],
            domain="com",
            limit=limit
        )
        logger.info(f"从 Oxylabs 获取: {len(products)} 个产品")
        return {
            "category": category_id,
            "products": products,
            "count": len(products),
            "source": "oxylabs_api"
        }
    except Exception as e:
        logger.error(f"Oxylabs 调用失败: {e}")
        return {"error": str(e), "products": []}
```

#### Step 2.2: 激活数据源架构

```python
# backend/api/__init__.py
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info(f"{settings.APP_NAME} starting up...")

    # 激活数据源注册
    try:
        from services.data_source_init import initialize_data_sources
        await initialize_data_sources()
        logger.info("✅ 数据源已注册")
    except Exception as e:
        logger.warning(f"数据源注册失败: {e}")

    # 启动爬虫调度器
    try:
        from scheduler.scheduler import start_scheduler
        await start_scheduler()
        logger.info("🚀 爬虫调度器已启动")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
```

---

### Phase 3: 数据完整性 (4小时，可选)

#### Step 3.1: 两步数据获取 (补充缺失字段)

```python
# backend/services/product_data_service.py (新建)
class ProductDataService:
    """产品数据服务 - 两步获取完整数据"""

    async def enrich_products(self, products: List[Dict]) -> List[Dict]:
        """
        为产品列表补充缺失字段 (brand, image, etc.)

        第1步: 从 cards 获取 ASIN 列表
        第2步: 批量调用 get_amazon_product 获取详情
        """
        enriched = []

        for product in products[:12]:  # 只补充前12个
            asin = product.get("asin")
            if not asin:
                enriched.append(product)
                continue

            try:
                detail = await self.client.get_amazon_product(asin)
                enriched.append({
                    **product,
                    "brand": detail.get("brand") or detail.get("manufacturer") or "N/A",
                    "image": self._extract_image(detail),
                    "rating": detail.get("rating"),
                    "reviews_count": detail.get("reviews_count", 0)
                })
            except Exception as e:
                logger.warning(f"无法获取 {asin} 详情: {e}")
                enriched.append(product)

        return enriched + products[12:]  # 剩余产品保持原样
```

---

## 验证清单

### 部署后立即验证

```bash
# 1. 测试 OxylabsClient 方法是否存在
ssh hk-jump "docker exec cb-business-api-fixed python -c 'from crawler.products.oxylabs_client import OxylabsClient; print([m for m in dir(OxylabsClient) if not m.startswith(\"_\")])'"

# 2. 测试 Products API
curl -s 'https://api.zenconsult.top/api/v1/products/categories/electronics/trending?limit=3' | jq

# 3. 测试 Articles API
curl -s 'https://api.zenconsult.top/api/v1/crawler-sync/articles?per_page=1' | jq

# 4. 测试 Cards API
curl -s 'https://api.zenconsult.top/api/v1/cards/daily' | jq '.cards | length'
```

### 前端验证

- [ ] 首页文章流能正常显示
- [ ] Products 页面有数据 (不再显示 "N/A")
- [ ] 点击关键词能跳转到产品页面
- [ ] 刷新页面数据一致

---

## 关键差异对比

| 原报告问题 | 实际情况 | 修正建议 |
|-----------|---------|---------|
| Products API 直接调用 Oxylabs | HK代码版本过旧，方法不存在 | **先部署最新代码** |
| 数据源架构未使用 | 确实未激活 | Phase 2.2 激活 |
| 前端API端点错误 | 确认错误 | Phase 1.2 修复 |
| crawler-sync 无数据 | 数据库连接问题 | Phase 1.3 修复配置 |

---

## 优先级总结

```
立即执行 (30分钟):
  ☑️ 1. 部署最新后端代码到HK
  ☑️ 2. 修复前端API端点
  ☑️ 3. 修复数据库连接配置

今天完成 (2小时):
  ☑️ 4. Products API 改用 cards 表
  ☑️ 5. 激活数据源架构

本周完成 (可选):
  ☐ 6. 实现两步数据获取
  ☐ 7. 添加缓存策略
```

---

**文档版本**: 2.1 (修正版)
**修正日期**: 2026-03-13
**关键修正**: 发现代码版本不一致是根本原因，必须先部署最新代码
