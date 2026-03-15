# 测试运行说明

## 当前限制

由于 SQLite 测试数据库不支持 PostgreSQL 的 JSONB 类型，完整的数据库集成测试需要在生产环境或使用 PostgreSQL Docker 容器运行。

## 快速测试 - 无需数据库

```bash
# 测试基本功能（无需数据库）
cd backend

# 测试配置加载
python3 -c "from tests.conftest import *; print('✅ 测试配置加载成功')"

# 测试模型导入
python3 -c "from models.card import Card; from models.business_opportunity import BusinessOpportunity; print('✅ 模型导入成功')"
```

## 完整测试 - 需要 PostgreSQL

### 方法 1: 使用 Docker PostgreSQL

```bash
# 启动测试数据库容器
docker run -d --name cb-test-db \
  -e POSTGRES_PASSWORD=test123 \
  -e POSTGRES_DB=cbdb_test \
  -p 5433:5432 \
  postgres:15

# 设置环境变量
export DATABASE_URL="postgresql+asyncpg://postgres:test123@localhost:5433/cbdb_test"
export SECRET_KEY="test_secret_key"
export ALLOWED_ORIGINS="*"

# 运行测试
python3 -m pytest tests/test_cards.py -v
python3 -m pytest tests/test_products.py -v
python3 -m pytest tests/test_favorites.py -v
python3 -m pytest tests/test_opportunities.py -v
```

### 方法 2: 在 HK 服务器上运行

```bash
ssh hk-jump

# 在容器内运行
docker exec cb-business-api-fixed pytest tests/test_cards.py -v
docker exec cb-business-api-fixed pytest tests/test_products.py -v
docker exec cb-business-api-fixed pytest tests/test_favorites.py -v
docker exec cb-business-api-fixed pytest tests/test_opportunities.py -v

# 运行所有测试
docker exec cb-business-api-fixed pytest tests/ -v

# 生成覆盖率报告
docker exec cb-business-api-fixed pytest tests/ --cov=api --cov-report=html
```

## API 端点手动测试

### Cards API

```bash
# 测试根端点
curl http://localhost:8000/

# 测试每日卡片
curl http://localhost:8000/api/v1/cards/daily

# 测试最新卡片
curl http://localhost:8000/api/v1/cards/latest?limit=3

# 测试卡片统计
curl http://localhost:8000/api/v1/cards/stats/overview

# 测试特定卡片
curl http://localhost:8000/api/v1/cards/{card_id}
```

### Products API

```bash
# 测试类别列表
curl http://localhost:8000/api/v1/products/categories

# 测试热门产品 (从Cards表读取)
curl http://localhost:8000/api/v1/products/categories/wireless_earbuds/trending?limit=5

# 测试带详情的产品获取
curl http://localhost:8000/api/v1/products/categories/fitness_trackers/trending?limit=2&fetch_details=true
```

### Favorites API

```bash
# 需要认证令牌
TOKEN="your_auth_token_here"

# 获取收藏列表
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/favorites

# 添加卡片收藏
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"card_id": "card_id_here", "opportunity_id": null}' \
  http://localhost:8000/api/v1/favorites

# 检查收藏状态
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/favorites/check/{card_id}

# 删除收藏
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/favorites/card/{card_id}
```

### Opportunities API

```bash
# 需要认证令牌
TOKEN="your_auth_token_here"

# 获取商机漏斗
curl http://localhost:8000/api/v1/opportunities/funnel

# 从Cards生成商机
curl -X POST -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/opportunities/generate-from-cards?limit=5

# 获取特定商机
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/opportunities/{opportunity_id}

# 列出商机（带筛选）
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/opportunities?grade=priority&limit=10"
```

## 测试覆盖的核心功能

### Task #64: Products API 从 Cards 表读取 ✅
- ✅ `test_products_api_reads_from_cards_not_oxylabs`
- ✅ `test_products_no_duplicate_api_calls`
- ✅ `test_products_data_consistency_with_cards`

### Task #65: 产品字段获取 ✅
- ✅ `test_get_category_trending_with_details`

### Task #67: 商机等级系统 ✅
- ✅ `test_cpi_score_ranges_and_grades`
- ✅ `test_opportunity_lifecycle_from_card_to_graded`

### Task #66: 数据源架构 ✅
- ✅ (数据源初始化在启动时验证)

## 测试验证清单

运行以下命令验证核心功能：

```bash
# 1. 验证 Products API 从 Cards 表读取
curl http://localhost:8000/api/v1/products/categories/wireless_earbuds/trending | jq '.data_source'
# 预期: "cards_table" 或 "cards_table_with_details"

# 2. 验证商机等级系统
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/opportunities/funnel | jq '.funnel'

# 3. 验证收藏功能
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"card_id": "test_card_id"}' \
  http://localhost:8000/api/v1/favorites
```

## 故障排除

### 问题 1: SQLite JSONB 错误

**错误**: `Compiler can't render element of type JSONB`

**解决方案**: 使用 PostgreSQL 数据库运行测试，或在 HK 服务器的容器内运行。

### 问题 2: 导入错误

**错误**: `ModuleNotFoundError: No module named 'x'`

**解决方案**:
```bash
pip install -r requirements.txt
```

### 问题 3: 认证错误

**错误**: `401 Unauthorized`

**解决方案**: 先获取认证令牌：
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

---

**注意**: 由于本地 SQLite 不支持 JSONB，推荐在 HK 服务器上运行完整测试套件。
