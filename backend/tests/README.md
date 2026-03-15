# Backend API 测试指南

## 概述

本目录包含 CB-Business 后端 API 的完整测试套件，覆盖核心功能和集成场景。

## 测试覆盖范围

### 核心功能测试

| 测试文件 | 覆盖端点 | 测试场景数 | 状态 |
|---------|---------|-----------|------|
| `test_cards.py` | Cards API | 15+ | ✅ |
| `test_products.py` | Products API | 10+ | ✅ |
| `test_favorites.py` | Favorites API | 12+ | ✅ |
| `test_opportunities.py` | Opportunities API | 15+ | ✅ |
| `test_auth.py` | Auth API | 已存在 | ✅ |
| `test_payments.py` | Payments API | 已存在 | ✅ |
| `test_subscriptions.py` | Subscriptions API | 已存在 | ✅ |
| `test_usage.py` | Usage API | 已存在 | ✅ |
| `test_admin.py` | Admin API | 已存在 | ✅ |
| `test_crawler.py` | Crawler API | 已存在 | ✅ |

### 新增测试验证

#### Task #64: Products API 从 Cards 表读取
- ✅ `test_products_api_reads_from_cards_not_oxylabs`
- ✅ `test_products_no_duplicate_api_calls`
- ✅ `test_products_data_consistency_with_cards`

#### Task #65: 产品字段获取
- ✅ `test_get_category_trending_with_details`

#### Task #67: 商机等级系统
- ✅ `test_cpi_score_ranges_and_grades`
- ✅ `test_opportunity_lifecycle_from_card_to_graded`

#### Task #66: 数据源架构
- ⏳ (需添加数据源相关测试)

## 运行测试

### 本地运行

```bash
# 运行所有测试
cd backend
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_cards.py -v

# 运行特定测试类
pytest tests/test_cards.py::TestCardsAPI -v

# 运行特定测试方法
pytest tests/test_cards.py::TestCardsAPI::test_get_daily_cards_success -v

# 显示详细输出
pytest tests/ -vv -s

# 生成覆盖率报告
pytest tests/ --cov=api --cov-report=html
```

### 容器内运行

```bash
# 在 HK 服务器上运行
ssh hk-jump
docker exec cb-business-api-fixed pytest tests/ -v
```

### 按优先级运行

```bash
# P0 - 核心功能测试
pytest tests/test_cards.py tests/test_products.py tests/test_favorites.py -v

# P1 - 集成测试
pytest tests/test_opportunities.py -v

# P2 - 现有测试
pytest tests/test_auth.py tests/test_payments.py tests/test_subscriptions.py -v
```

## 测试结构

### Fixtures (conftest.py)

- `db_setup` - 数据库设置
- `db_session` - 数据库会话
- `client` - HTTP 测试客户端
- `test_user` - 测试用户
- `pro_user` - Pro 用户
- `admin_user` - 管理员用户
- `auth_token` - 认证令牌
- `pro_token` - Pro 令牌
- `admin_token` - 管理员令牌

### 测试模式

```
tests/
├── conftest.py              # Pytest 配置和 fixtures
├── test_auth.py             # 认证 API 测试
├── test_cards.py            # Cards API 测试
├── test_products.py         # Products API 测试
├── test_favorites.py        # Favorites API 测试
├── test_opportunities.py    # Opportunities API 测试
├── test_payments.py         # 支付 API 测试
├── test_subscriptions.py   # 订阅 API 测试
├── test_usage.py            # 使用量 API 测试
├── test_admin.py            # 管理 API 测试
├── test_crawler.py          # 爬虫 API 测试
├── test_cpi_algorithm.py    # CPI 算法测试
├── test_utils.py            # 工具函数测试
└── test_debug_session.py    # 调试会话测试
```

## 测试命名规范

### 测试类命名
- 功能测试: `Test{Module}API`
- 集成测试: `Test{Module}Integration`

### 测试方法命名
- 成功场景: `test_{action}_success`
- 失败场景: `test_{action}_{error_type}`
- 集成场景: `test_{description}_lifecycle`

## 持续集成

### GitHub Actions (待添加)

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov httpx
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --cov=api --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 测试数据

测试使用 SQLite 内存数据库，每个测试独立运行，确保测试间相互隔离。

### Mock 数据

- Redis 客户端已 Mock
- Oxylabs API 未 Mock（集成测试需要真实响应）
- 外部服务根据需要 Mock

## 调试测试

```bash
# 打印详细输出
pytest tests/test_cards.py::test_get_daily_cards_success -vv -s

# 在第一个失败时停止
pytest tests/ -x

# 只运行失败的测试
pytest tests/ --lf

# 进入 pdb 调试器
pytest tests/test_cards.py::test_get_daily_cards_success --pdb
```

## 测试覆盖率目标

| 模块 | 目标覆盖率 | 当前状态 |
|------|-----------|---------|
| Cards API | 80% | 🟡 进行中 |
| Products API | 80% | 🟢 已覆盖 |
| Favorites API | 80% | 🟢 已覆盖 |
| Opportunities API | 75% | 🟢 已覆盖 |
| Auth API | 80% | 🟢 已覆盖 |
| 总体 | 75% | 🟡 进行中 |

## 常见问题

### 导入错误

```bash
# 确保已安装所有依赖
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov
```

### 数据库错误

```bash
# 清理测试数据库
rm -f test.db
pytest tests/ -v
```

### 异步测试失败

```bash
# 确保安装了 pytest-asyncio
pip install pytest-asyncio

# 检查 Python 版本 >= 3.8
python --version
```

## 贡献指南

### 添加新测试

1. 在对应的测试文件中添加测试类或方法
2. 遵循命名规范
3. 添加必要的 fixtures
4. 编写清晰的文档字符串
5. 运行测试确保通过

### 测试 Checklist

- [ ] 测试成功场景
- [ ] 测试失败场景
- [ ] 测试边界条件
- [ ] 测试认证/权限
- [ ] 测试数据验证
- [ ] 测试错误处理

## 更新日志

### 2026-03-14
- ✅ 添加 `test_cards.py` - Cards API 完整测试
- ✅ 添加 `test_products.py` - Products API 测试，验证 Task #64
- ✅ 添加 `test_favorites.py` - Favorites API 测试
- ✅ 添加 `test_opportunities.py` - Opportunities API 和 CPI 算法测试
- ✅ 更新测试文档和使用说明

---

**维护者**: CB-Business 开发团队
**最后更新**: 2026-03-14
**pytest 版本要求**: >= 7.0
