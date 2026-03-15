# CB-Business 前后端功能设计总体现状备忘录

**日期**: 2026-03-15
**文档类型**: 系统架构全景备忘录
**目标受众**: 开发者、架构师、新加入项目的技术人员

---

## 文档导航

- [1. 系统架构概览](#1-系统架构概览)
- [2. 数据流设计](#2-数据流设计)
- [3. 算法结构](#3-算法结构)
- [4. API端点布置](#4-api端点布置)
- [5. 前后端连接](#5-前后端连接)
- [6. 服务器部署](#6-服务器部署)
- [7. 数据库设计](#7-数据库设计)
- [8. 缓存策略](#8-缓存策略)
- [9. 认证授权](#9-认证授权)
- [10. 支付集成](#10-支付集成)

---

## 1. 系统架构概览

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              客户端层                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │  Web Browser     │  │  Mobile Browser  │  │  API Clients     │      │
│  │  (Next.js Vercel)│  │  (Responsive)    │  │  (Third-party)   │      │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘      │
└───────────┼────────────────────┼───────────────────────┼───────────────┘
            │                    │                       │
            ▼                    ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            CDN层 (Vercel)                                │
│                       https://www.zenconsult.top                          │
│                    • Static Asset Hosting                              │
│                    • Edge Caching                                       │
│                    • Automatic HTTPS                                    │
└─────────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          反向代理层 (Nginx)                              │
│                       api.zenconsult.top:443                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  nginx-gateway (172.22.0.5)                                         │  │
│  │  • SSL Termination (Let's Encrypt)                                 │  │
│  │  • Request Routing                                                 │  │
│  │  • Gzip Compression                                                │  │
│  │  • Rate Limiting (WAF)                                             │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            应用层 (FastAPI)                             │
│                   172.22.0.4:8000 (cb-business-api-fixed)              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  FastAPI Application                                              │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │  CORSMiddleware                                              │  │   │
│  │  │  • Origins: www.zenconsult.top, admin.zenconsult.top        │  │   │
│  │  │  • Credentials: true                                         │  │   │
│  │  │  • Methods: *                                                │  │   │
│  │  │  • Headers: *                                                │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │  API Routes                                                  │  │   │
│  │  │  • /api/v1/auth/*      - 认证相关                            │  │   │
│  │  │  • /api/v1/users/*     - 用户管理                            │  │   │
│  │  │  • /api/v1/cards/*     - 卡片和商机                          │  │   │
│  │  │  • /api/v1/favorites/* - 收藏管理                            │  │   │
│  │  │  • /api/v1/payments/*  - 支付集成                            │  │   │
│  │  │  • /api/v1/subscriptions/* - 订阅管理                       │  │   │
│  │  │  • /api/v1/crawler-sync/* - 爬虫数据                         │  │   │
│  │  │  • /api/v1/opportunities/* - 商机跟踪                        │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  │  ┌─────────────────────────────────────────────────────────────┐  │   │
│  │  │  Business Services                                           │  │   │
│  │  │  • CardGenerator      - 卡片生成引擎                         │  │   │
│  │  │  • OpportunityScorer  - C-P-I算法引擎                        │  │   │
│  │  │  • SmartOrchestrator  - AI编排服务                          │  │   │
│  │  │  • CacheService       - Redis缓存管理                        │  │   │
│  │  │  • AirwallexService   - 支付网关集成                         │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────┬─────────────────────────────┬───────────────────────┘
                      │                             │
                      ▼                             ▼
┌───────────────────────────────────┐  ┌───────────────────────────────────┐
│      PostgreSQL (数据持久化)       │  │         Redis (缓存层)            │
│    172.22.0.2:5432                 │  │      172.22.0.3:6379             │
│  ┌─────────────────────────────┐  │  │  ┌─────────────────────────────┐  │
│  │  Database: cbdb              │  │  │  │  • Cards Cache (30min)      │  │
│  │  • 17 tables                 │  │  │  │  • User Session Data       │  │
│  │  • Indexed for performance   │  │  │  │  • API Response Cache      │  │
│  │  • FK constraints enforced   │  │  │  │  • Rate Limiting Counters   │  │
│  └─────────────────────────────┘  │  │  │  • Job Queue (TODO)         │  │
│                                   │  │  └─────────────────────────────┘  │
│  Tables:                          │  │                                   │
│  • users, subscriptions, payments │  │                                   │
│  • cards, favorites, opportunities │  │                                   │
│  • articles, keywords, trends     │  │                                   │
│  • user_interactions, funnel_events│  │                                   │
└───────────────────────────────────┘  └───────────────────────────────────┘
```

### 1.2 技术栈总览

#### 前端技术栈
```
框架: Next.js 13+ (App Router)
语言: TypeScript 5+
样式: Tailwind CSS + shadcn/ui
状态管理: React Context API
HTTP: fetch API + axios
构建: Turbopack (开发), webpack (生产)
部署: Vercel (自动化CI/CD)
测试: Playwright (E2E)

主要依赖:
- @radix-ui/*: UI组件基础
- lucide-react: 图标库
- recharts: 图表库
- date-fns: 日期处理
- zustand: 轻量状态管理
```

#### 后端技术栈
```
框架: FastAPI 0.100+
语言: Python 3.10+
ORM: SQLAlchemy 2.0 (async)
数据库: PostgreSQL 15
缓存: Redis 7
任务调度: APScheduler (内置)
数据采集: Oxylabs SDK, OpenClaw RSS
支付: Airwallex SDK
部署: Docker + Docker Compose

主要依赖:
- pydantic: 数据验证
- asyncpg: 异步PostgreSQL驱动
- redis-py: Redis客户端
- httpx: 异步HTTP客户端
- python-jose: JWT处理
- passlib: 密码哈希
```

---

## 2. 数据流设计

### 2.1 用户认证数据流

```
┌──────────────┐
│  用户输入     │
│  email/pwd   │
└──────┬───────┘
       │
       ▼
┌───────────────────────────────────────────────────────────────┐
│                     前端 (Next.js)                            │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  /login页面 → lib/api.ts → authApi.login()              │  │
│  │  POST https://api.zenconsult.top/api/v1/auth/login      │  │
│  │  Body: { email, password }                               │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                     Nginx (反向代理)                          │
│  • SSL终止                                                   │
│  • 转发到 172.22.0.4:8000                                    │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                  FastAPI (后端应用)                            │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  POST /api/v1/auth/login                                 │  │
│  │                                                          │  │
│  │  1. 验证请求: UserLoginSchema                           │  │
│  │  2. 查询用户: SELECT * FROM users WHERE email = ?       │  │
│  │  3. 验证密码: verify_password(hashed_password, password)│  │
│  │  4. 生成JWT: create_access_token(user_id)               │  │
│  │  5. 更新登录时间: UPDATE users SET last_login_at = NOW  │  │
│  │  6. 返回响应: { access_token, user }                    │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  响应返回        │
                    │  {              │
                    │    token,       │
                    │    user: {      │
                    │      id,        │
                    │      email,     │
                    │      name,      │
                    │      plan_tier, │
                    │      ...        │
                    │    }            │
                    │  }              │
                    └─────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                  前端存储Token (localStorage)                  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  localStorage.setItem('auth_token', token)              │  │
│  │  localStorage.setItem('user', JSON.stringify(user))     │  │
│  │  AuthContext更新状态 → 触发页面重渲染                    │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### 2.2 卡片生成数据流

```
┌──────────────────────────────────────────────────────────────┐
│                     数据采集阶段                              │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  OxylabsClient.search_amazon(category, query)           │  │
│  │  ↓                                                       │  │
│  │  Amazon产品数据 (50 items)                              │  │
│  │  • ASIN, Title, Price, Rating, Reviews                 │  │
│  │  • 搜索结果 (Brand, Image缺失)                          │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                     数据处理阶段                              │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  CardGenerator.fetch_category_data(category)            │  │
│  │  ↓                                                       │  │
│  │  1. 本地统计计算:                                         │  │
│  │     • 价格分布 (min, max, avg, std)                      │  │
│  │     • 评分分布 (avg rating分布)                          │  │
│  │     • 竞争度 (基于结果数量)                              │  │
│  │  ↓                                                       │  │
│  │  2. 生成卡片的AI评分 (本地算法，非真实AI):               │  │
│  │     • opportunity_score = f(价格, 评分, 竞争度)          │  │
│  │     • 注意: 当前未调用OpenAI API                         │  │
│  │  ↓                                                       │  │
│  │  3. 构造Card对象:                                       │  │
│  │     {                                                   │  │
│  │       category, title, description,                      │  │
│  │       opportunity_score, amazon_data,                   │  │
│  │       insights: {价格分析, 评分分析, ...}               │  │
│  │     }                                                   │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                     数据持久化阶段                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL: cards表                                     │  │
│  │  • 插入新卡片 (或更新已存在的)                           │  │
│  │  • amazon_data作为JSONB存储                              │  │
│  │  • created_at自动更新                                    │  │
│  └─────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Redis: 缓存层                                          │  │
│  │  • Key: cards:daily:{category}                          │  │
│  │  • TTL: 1800秒 (30分钟)                                 │  │
│  │  • Value: 序列化的Card对象                              │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                     API响应阶段                                │
│  GET /api/v1/cards/daily                                     │
│  ↓                                                             │
│  1. 检查Redis缓存                                            │
│     • 缓存命中 → 直接返回                                   │
│     • 缓存未命中 → 继续步骤2-4                               │
│  2. 按opportunity_score排序，取Top 3                         │
│  3. 转换为API响应格式 (Card.to_dict())                        │
│  4. 写入Redis缓存                                           │
│  5. 返回JSON: { cards: [...], total: 3 }                    │
└───────────────────────────────────────────────────────────────┘
```

### 2.3 收藏功能数据流

```
┌──────────────────────┐
│  用户点击"收藏"按钮   │
│  (未登录状态)        │
└─────────┬────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────┐
│                     前端检查认证状态                           │
│  const { isAuthenticated } = useAuth()                       │
│  if (!isAuthenticated) {                                     │
│    // 1. 保存到本地localStorage (临时)                       │
│    localStorage.setItem('zen_favorites', JSON.stringify([...]))│
│    // 2. 显示登录提示                                        │
│    router.push('/login?redirect=/opportunities')             │
│  }                                                            │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              ▼ (已登录状态)
┌───────────────────────────────────────────────────────────────┐
│                     发送收藏请求                               │
│  POST /api/v1/favorites                                      │
│  Body: { card_id: "uuid" }                                   │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                  后端处理收藏请求                              │
│  1. 验证JWT token → 获取user_id                              │
│  2. 检查是否已收藏:                                          │
│     SELECT * FROM favorites WHERE user_id = ? AND card_id = ?│
│  3. 如果已存在 → 返回409 Conflict                            │
│  4. 如果不存在 → 创建收藏:                                   │
│     INSERT INTO favorites (user_id, card_id, created_at)      │
│  5. 同步本地收藏到服务器 (如果存在)                          │
│  6. 返回201 Created                                          │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                  创建/更新商机记录                            │
│  当收藏卡片时:                                               │
│  1. 调用OpportunityScorer.calculate_cpi(card)               │
│  2. 创建BusinessOpportunity记录:                             │
│     INSERT INTO business_opportunities (                     │
│       title, status='POTENTIAL', card_id, user_id,           │
│       cpi_total_score, grade, ...                           │
│     )                                                         │
│  3. 商机进入监控漏斗，开始C-P-I评分                           │
└───────────────────────────────────────────────────────────────┘
```

### 2.4 AI编排数据流 (SmartOrchestrator)

```
┌───────────────────────────────────────────────────────────────┐
│              OpenClaw回调 → 新文章到达                        │
│  POST /api/v1/openclaw/callback/articles                     │
│  Body: { articles: [...] }                                   │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│              AI分析编排 (SmartOrchestrator)                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  1. 批量AI分类 (GLM-4 Plus)                              │  │
│  │     • 调用智谱AI API                                     │  │
│  │     • 分析content_theme (opportunity/risk/policy/guide)│  │
│  │     • 识别region (north_america/southeast_asia/...)     │  │
│  │     • 提取keywords (5-10个标签)                          │  │
│  │     • 计算opportunity_score (0-1)                       │  │
│  │  ↓                                                       │  │
│  │  2. 信号识别 (SignalRecognition)                        │  │
│  │     • 分析文章中的市场趋势                                │  │
│  │     • 识别新兴关键词                                      │  │
│  │     • 检测异常变化                                        │  │
│  │  ↓                                                       │  │
│  │  3. 任务生成 (TaskGeneration)                          │  │
│  │     • 根据AI分析生成数据采集任务                          │  │
│  │     • 调度Oxylabs深度扫描                                 │  │
│  │     • 触发卡片生成流程                                    │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬─────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│              商机跟踪系统更新                                │
│  1. 文章AI分析结果存储到articles表                           │
│  2. 高opportunity_score文章触发卡片生成                      │
│  3. 更新keywords表 (趋势图)                                  │
│  4. 用户收藏的商机重新计算C-P-I分数                          │
│  5. 商机等级自动升降 (lead → normal → priority → landable)  │
└───────────────────────────────────────────────────────────────┘
```

---

## 3. 算法结构

### 3.1 C-P-I机会评分算法

```python
# backend/services/opportunity_algorithm.py

class OpportunityScorer:
    """
    C-P-I算法: 竞争度-潜力-信息差 三维评分模型

    总分 = 竞争度(40%) × 潜力(35%) × 信息差(25%)
    分数范围: 0-100
    """

    async def calculate_opportunity_score(
        self,
        card: Card,
        db: AsyncSession
    ) -> Dict[str, float]:
        """
        计算商机的综合机会评分

        返回: {
            'competition_score': 0-100,      # 竞争度 (越低越好)
            'potential_score': 0-100,         # 潜力 (越高越好)
            'intelligence_gap_score': 0-100,  # 信息差 (越高越好)
            'total_score': 0-100              # 总分
        }
        """

        # 1. 竞争度评分 (Competition Score)
        #    基于产品数量、价格竞争、评分竞争
        competition_score = await self._calculate_competition(
            card.amazon_data
        )

        # 2. 潜力评分 (Potential Score)
        #    基于市场规模、增长趋势、利润空间
        potential_score = await self._calculate_potential(
            card.category,
            db
        )

        # 3. 信息差评分 (Intelligence Gap Score)
        #    基于数据稀缺性、分析难度、时间敏感度
        intelligence_gap_score = await self._calculate_intelligence_gap(
            card,
            db
        )

        # 4. 加权总分
        total_score = (
            competition_score * 0.40 +
            potential_score * 0.35 +
            intelligence_gap_score * 0.25
        )

        return {
            'competition_score': competition_score,
            'potential_score': potential_score,
            'intelligence_gap_score': intelligence_gap_score,
            'total_score': total_score
        }
```

#### C-P-I三维度详解

**竞争度 (Competition) - 权重40%**
```python
def _calculate_competition(self, amazon_data: dict) -> float:
    """
    竞争度越低，机会越大

    指标:
    - search_result_count: 搜索结果数量 (越多→竞争越大)
    - price_std_dev: 价格标准差 (越大→价格战越激烈)
    - avg_rating: 平均评分 (越高→质量要求越高)
    - brand_diversity: 品牌多样性 (越低→垄断程度越高)
    """
    n_products = len(amazon_data.get('products', []))
    if n_products == 0:
        return 50  # 默认中等竞争

    # 搜索结果密度 (0-40分)
    result_density = min(n_products / 50 * 40, 40)

    # 价格竞争 (0-30分)
    prices = [p['price'] for p in amazon_data['products'] if p.get('price')]
    price_std = statistics.stdev(prices) if len(prices) > 1 else 0
    price_competition = min(price_std / 10 * 30, 30)

    # 评分竞争 (0-20分)
    avg_rating = sum(p['rating'] for p in amazon_data['products'] if p.get('rating')) / n_products
    rating_competition = avg_rating / 5 * 20

    # 品牌多样性 (0-10分，反向)
    unique_brands = len(set(p.get('brand') for p in amazon_data['products'] if p.get('brand')))
    brand_score = 10 - min(unique_brands / n_products * 10, 10)

    return result_density + price_competition + rating_competition + brand_score
```

**潜力 (Potential) - 权重35%**
```python
def _calculate_potential(self, category: str, db: AsyncSession) -> float:
    """
    潜力越大，机会越大

    指标:
    - market_size: 市场规模 (基于历史数据)
    - growth_rate: 增长率 (基于趋势数据)
    - profit_margin: 利润空间 (基于价格分析)
    """
    # 从历史数据计算市场规模 (0-40分)
    market_size = await self._get_market_size(category, db)

    # 从趋势数据计算增长率 (0-35分)
    growth_rate = await self._get_growth_rate(category, db)

    # 从价格分布计算利润空间 (0-25分)
    profit_margin = self._calculate_profit_margin(category)

    return market_size + growth_rate + profit_margin
```

**信息差 (Intelligence Gap) - 权重25%**
```python
def _calculate_intelligence_gap(self, card: Card, db: AsyncSession) -> float:
    """
    信息差越大，机会越大

    指标:
    - data_rarity: 数据稀缺性 (该类别的卡片数量)
    - analysis_complexity: 分析难度 (产品属性复杂度)
    - time_sensitivity: 时间敏感度 (新机会还是已成熟)
    """
    # 数据稀缺性 (0-40分) - 卡片越少，信息差越大
    card_count = await self._count_cards_in_category(card.category, db)
    data_rarity = max(40 - card_count / 10, 0)

    # 分析难度 (0-30分) - 产品种类越多，分析越难
    product_variety = len(card.amazon_data.get('products', [])) / 50 * 30

    # 时间敏感度 (0-30分) - 新品获得更高分
    days_since_creation = (datetime.now() - card.created_at).days
    time_sensitivity = max(30 - days_since_creation, 0)

    return data_rarity + product_variety + time_sensitivity
```

### 3.2 商机等级系统

```python
# backend/models/business_opportunity.py

class OpportunityGrade(str, enum.Enum):
    """商机等级 - 基于C-P-I分数的动态等级"""
    LEAD = "lead"              # 线索: < 60分，需进一步验证
    NORMAL = "normal"          # 普通商机: 60-69分，保持关注
    PRIORITY = "priority"      # 重点商机: 70-84分，优先验证
    LANDABLE = "landable"      # 落地商机: ≥ 85分，可落地执行

class GradeCalculator:
    THRESHOLDS = {
        'lead_max': 60,
        'normal_min': 60,
        'priority_min': 70,
        'landable_min': 85
    }

    @staticmethod
    def calculate_grade(cpi_total_score: float) -> OpportunityGrade:
        if cpi_total_score < 60:
            return OpportunityGrade.LEAD
        elif cpi_total_score < 70:
            return OpportunityGrade.NORMAL
        elif cpi_total_score < 85:
            return OpportunityGrade.PRIORITY
        else:
            return OpportunityGrade.LANDABLE
```

**等级监控调度器**:
```python
# backend/scheduler/opportunity_tasks.py

@scheduler.scheduled_job('interval', hours=6)
async def grade_monitoring_job():
    """
    商机等级监控定时任务 - 每6小时执行

    功能:
    1. 查询用户收藏的商机
    2. 重新计算C-P-I分数
    3. 更新等级（自动升降）
    4. 记录等级变更历史
    """
    # 查询活跃商机
    opportunities = await db.execute(
        select(BusinessOpportunity)
        .where(BusinessOpportunity.status.in_([
            OpportunityStatus.POTENTIAL,
            OpportunityStatus.VERIFYING,
            OpportunityStatus.APPROVED
        ]))
    )

    for opp in opportunities:
        # 重新计算C-P-I分数
        new_scores = await opportunity_scorer.calculate_opportunity_score(
            opp.card, db
        )

        # 计算新等级
        new_grade = GradeCalculator.calculate_grade(
            new_scores['total_score']
        )

        # 如果等级变化，记录历史
        if new_grade != opp.grade:
            opp.grade = new_grade
            opp.grade_history.append({
                'from': opp.grade,
                'to': new_grade,
                'at': datetime.now().isoformat(),
                'cpi_score': new_scores['total_score']
            })
            opp.last_grade_change_at = datetime.now()
```

### 3.3 漏斗管理调度器

```python
# backend/scheduler/opportunity_tasks.py

# 三个定时任务自动运行

# 任务1: 漏斗状态检查 (每30分钟)
@scheduler.scheduled_job('interval', minutes=30)
async def funnel_status_check():
    """
    检查商机漏斗中的状态变化
    - POTENTIAL → VERIFYING (C-P-I分数>70)
    - VERIFYING → APPROVED (人工验证通过)
    - APPROVED → IMPLEMENTING (开始执行)
    - IMPLEMENTING → COMPLETED (完成落地)
    """
    pass

# 任务2: 数据刷新 (每6小时)
@scheduler.scheduled_job('interval', hours=6)
async def data_refresh_job():
    """
    刷新商机数据
    - 重新计算C-P-I分数
    - 更新市场数据
    - 同步产品价格
    """
    pass

# 任务3: 自动降级 (每天)
@scheduler.scheduled_job('cron', hour=3)
async def auto_downgrade():
    """
    自动降级低价值商机
    - 7天无进展的PRIORITY降为NORMAL
    - 14天无进展的NORMAL降为LEAD
    - 30天无进展的LEAD标记为ARCHIVED
    """
    pass
```

---

## 4. API端点布置

### 4.1 API路由总览

```
/api/v1/
├── auth/
│   ├── POST   /register           # 用户注册 (trial/free)
│   ├── POST   /login              # 用户登录
│   ├── POST   /logout             # 用户登出
│   └── GET    /me                 # 获取当前用户信息
│
├── users/
│   ├── GET    /me                 # 获取当前用户 (同auth/me)
│   ├── PUT    /me                 # 更新用户信息
│   └── POST   /me/refresh         # 刷新用户状态
│
├── cards/
│   ├── GET    /daily              # Top 3精选卡片 (带缓存)
│   ├── GET    /history            # 全部12张卡片
│   ├── GET    /latest             # 最新生成的卡片
│   ├── GET    /{id}               # 单张卡片详情
│   └── POST   /refresh            # 手动刷新卡片缓存
│
├── favorites/
│   ├── GET    /                   # 用户收藏列表
│   ├── POST   /                   # 添加收藏
│   ├── DELETE /card/{card_id}     # 取消收藏
│   └── GET    /check/{card_id}    # 检查收藏状态
│
├── opportunities/
│   ├── GET    /                   # 商机列表 (用户收藏的)
│   ├── GET    /{id}               # 商机详情
│   ├── POST   /{id}/track         # 开始跟踪商机
│   ├── POST   /{id}/ignore        # 忽略商机
│   └── POST   /{id}/convert       # 转化为商机
│
├── payments/
│   ├── POST   /create             # 创建支付订单
│   ├── GET    /{order_no}         # 查询支付状态
│   ├── POST   /webhooks/airwallex # Airwallex回调
│   └── GET    /methods            # 支付方式列表
│
├── subscriptions/
│   ├── GET    /me                 # 我的订阅
│   ├── GET    /plans              # 订阅计划列表
│   ├── POST   /upgrade            # 升级订阅
│   └── POST   /cancel             # 取消订阅
│
├── crawler-sync/
│   ├── GET    /articles           # 文章列表 (带分页)
│   ├── GET    /article/{id}       # 文章详情
│   └── GET    /sources            # 数据源列表
│
├── keywords/
│   ├── GET    /trending           # 热门关键词
│   └── GET    /{keyword}/related  # 相关关键词
│
├── trends/
│   ├── GET    /categories         # 品类趋势
│   └── GET    /regions            # 地区趋势
│
├── admin/
│   ├── GET    /stats              # 统计数据
│   ├── GET    /users              # 用户列表
│   ├── GET    /subscriptions      # 订阅列表
│   └── POST   //{resource}/{id}/action # 管理操作
│
├── openclaw/
│   ├── POST   /callback/articles  # OpenClaw文章回调
│   ├── POST   /callback/opportunities # OpenClaw商机回调
│   └── GET    /status             # OpenClaw状态
│
└── health
    └── GET    /                   # 健康检查
```

### 4.2 核心API详解

#### 4.2.1 认证API

**POST /api/v1/auth/register**
```yaml
请求体:
  email: string (required, email格式)
  password: string (required, >=6位)
  name: string (required, >=2字符)
  plan_choice: 'trial' | 'free' (default: 'trial')

响应 (201 Created):
  access_token: string (JWT)
  token_type: 'bearer'
  user:
    id: uuid
    email: string
    name: string
    plan_tier: 'trial' | 'free' | 'pro'
    plan_status: 'active' | 'expired' | 'locked'
    created_at: iso8601
```

**POST /api/v1/auth/login**
```yaml
请求体:
  email: string
  password: string

响应 (200 OK):
  access_token: string
  user: {...}

错误 (401 Unauthorized):
  detail: "邮箱或密码错误"
```

#### 4.2.2 卡片API

**GET /api/v1/cards/daily**
```yaml
查询参数:
  limit: number (default: 3, max: 10)

响应 (200 OK):
  cards:
    - id: uuid
      category: string
      title: string
      description: string
      opportunity_score: number (0-100)
      amazon_data:
        products:
          - asin: string
            title: string
            price: number
            rating: number
            url: string
      insights:
        price_analysis: string
        competition_analysis: string
        recommendation: string
      created_at: iso8601
  total: number
```

#### 4.2.3 收藏API

**POST /api/v1/favorites**
```yaml
请求头:
  Authorization: Bearer {token}

请求体:
  card_id: uuid (可选)
  opportunity_id: uuid (可选)
  至少提供一个

响应 (201 Created):
  id: uuid
  user_id: uuid
  card_id: uuid | null
  opportunity_id: uuid | null
  created_at: iso8601

错误 (409 Conflict):
  detail: "已收藏该项目"

错误 (401 Unauthorized):
  detail: "请先登录"
```

#### 4.2.4 支付API

**POST /api/v1/payments/create**
```yaml
请求头:
  Authorization: Bearer {token}

请求体:
  plan_tier: 'pro' (required)
  billing_cycle: 'monthly' | 'yearly' (required)
  payment_method: object
    type: 'card' | 'alipay' | 'wechat'
    ...

响应 (200 OK):
  order_no: string
  amount: number
  currency: 'USD' | 'CNY'
  payment_url: string (Airwallex checkout URL)
  expires_at: iso8601

错误 (402 Payment Required):
  detail: "用户已有激活订阅"
```

---

## 5. 前后端连接

### 5.1 前端API客户端

```typescript
// frontend/lib/api.ts

import type { User, Card, Favorite } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.zenconsult.top';

// 认证API
export const authApi = {
  async register(email: string, password: string, name: string, plan_choice: 'trial' | 'free') {
    const response = await fetch(`${API_BASE}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name, plan_choice })
    });
    if (!response.ok) throw new Error('注册失败');
    return response.json();
  },

  async login(email: string, password: string) {
    const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!response.ok) throw new Error('登录失败');
    return response.json();
  }
};

// 卡片API
export const cardsApi = {
  async getDaily(limit: number = 3): Promise<{ cards: Card[], total: number }> {
    const response = await fetch(`${API_BASE}/api/v1/cards/daily?limit=${limit}`);
    if (!response.ok) throw new Error('获取卡片失败');
    return response.json();
  },

  async getHistory(): Promise<Card[]> {
    const response = await fetch(`${API_BASE}/api/v1/cards/history`);
    if (!response.ok) throw new Error('获取历史卡片失败');
    return response.json();
  }
};

// 收藏API (需要认证)
export const favoritesApi = {
  async getFavorites(token: string): Promise<Favorite[]> {
    const response = await fetch(`${API_BASE}/api/v1/favorites`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('获取收藏失败');
    return response.json();
  },

  async addFavorite(cardId: string, token: string): Promise<Favorite> {
    const response = await fetch(`${API_BASE}/api/v1/favorites`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ card_id: cardId })
    });
    if (!response.ok) throw new Error('添加收藏失败');
    return response.json();
  },

  async removeFavorite(cardId: string, token: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/v1/favorites/card/${cardId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('取消收藏失败');
  }
};
```

### 5.2 认证上下文

```typescript
// frontend/lib/auth-context.tsx

'use client';

import { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authApi, usersApi } from './api';
import type { User } from './types';

const TOKEN_KEY = 'auth_token';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string, plan?: 'trial' | 'free') => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<User | void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // 应用启动时验证token
  useEffect(() => {
    const verifyToken = async () => {
      const savedToken = localStorage.getItem(TOKEN_KEY);
      const savedUser = localStorage.getItem('user');

      if (!savedToken) {
        setIsLoading(false);
        return;
      }

      try {
        // 验证token有效性
        const userData = await usersApi.getMe(savedToken);
        setUser(userData);
        setToken(savedToken);
      } catch (error) {
        // Token无效，清除本地存储
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem('user');
        setUser(null);
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    };

    verifyToken();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await authApi.login(email, password);

    setToken(response.access_token);
    setUser(response.user);

    // 持久化到localStorage
    localStorage.setItem(TOKEN_KEY, response.access_token);
    localStorage.setItem('user', JSON.stringify(response.user));

    // 跳转到仪表盘
    router.push('/dashboard');
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem('user');
    router.push('/');
  };

  const refreshUser = async () => {
    if (!token) return;

    try {
      const userData = await usersApi.getMe(token);
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
      return userData;
    } catch (error) {
      logout();
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout, refreshUser, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
```

### 5.3 收藏上下文

```typescript
// frontend/lib/contexts/favorites-context.tsx

'use client';

import { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from '../auth-context';
import { favoritesApi } from '../api';

interface FavoritesContextType {
  favoriteItems: Favorite[];
  isLoading: boolean;
  error: string | null;
  favoriteCount: number;
  addFavorite: (cardId: string) => Promise<void>;
  removeFavorite: (cardId: string) => Promise<void>;
  checkFavorite: (cardId: string) => boolean;
  refreshFavorites: () => Promise<void>;
}

const FavoritesContext = createContext<FavoritesContextType | undefined>(undefined);

export function FavoritesProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, token } = useAuth();
  const [favoriteItems, setFavoriteItems] = useState<Favorite[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 加载收藏列表
  useEffect(() => {
    if (!isAuthenticated || !token) {
      setFavoriteItems([]);
      return;
    }

    const loadFavorites = async () => {
      setIsLoading(true);
      try {
        const items = await favoritesApi.getFavorites(token);
        setFavoriteItems(items);
        setError(null);
      } catch (err) {
        setError('加载收藏失败');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    loadFavorites();
  }, [isAuthenticated, token]);

  const addFavorite = async (cardId: string) => {
    if (!token) {
      // 未登录，保存到本地
      const local = JSON.parse(localStorage.getItem('zen_favorites') || '[]');
      if (!local.includes(cardId)) {
        local.push(cardId);
        localStorage.setItem('zen_favorites', JSON.stringify(local));
      }
      return;
    }

    try {
      const newFavorite = await favoritesApi.addFavorite(cardId, token);
      setFavoriteItems(prev => [...prev, newFavorite]);

      // 同步本地收藏
      const local = JSON.parse(localStorage.getItem('zen_favorites') || '[]');
      const updated = local.filter((id: string) => id !== cardId);
      localStorage.setItem('zen_favorites', JSON.stringify(updated));
    } catch (err) {
      setError('添加收藏失败');
      throw err;
    }
  };

  const removeFavorite = async (cardId: string) => {
    if (!token) return;

    try {
      await favoritesApi.removeFavorite(cardId, token);
      setFavoriteItems(prev => prev.filter(item => item.card_id !== cardId));
    } catch (err) {
      setError('取消收藏失败');
      throw err;
    }
  };

  const checkFavorite = (cardId: string): boolean => {
    return favoriteItems.some(item => item.card_id === cardId);
  };

  const favoriteCount = favoriteItems.length;

  return (
    <FavoritesContext.Provider value={{
      favoriteItems,
      isLoading,
      error,
      favoriteCount,
      addFavorite,
      removeFavorite,
      checkFavorite,
      refreshFavorites: () => loadFavorites()
    }}>
      {children}
    </FavoritesContext.Provider>
  );
}

export function useFavorites() {
  const context = useContext(FavoritesContext);
  if (!context) throw new Error('useFavorites must be used within FavoritesProvider');
  return context;
}
```

### 5.4 前端页面连接

```typescript
// frontend/app/page.tsx (首页)

export default function HomePage() {
  const { user } = useAuth();
  const { favoriteItems, addFavorite, removeFavorite, checkFavorite } = useFavorites();
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 加载Top 3卡片
    cardsApi.getDaily(3).then(data => {
      setCards(data.cards);
      setLoading(false);
    });
  }, []);

  return (
    <div>
      <DailyCardsHero cards={cards} loading={loading} />
      <KeywordCloud />
      <HomeContent />
    </div>
  );
}

// frontend/components/cards/card.tsx (卡片组件)

export function InfoCard({ card }: { card: Card }) {
  const { isAuthenticated } = useAuth();
  const { addFavorite, removeFavorite, checkFavorite } = useFavorites();
  const [isFavorited, setIsFavorited] = useState(false);

  useEffect(() => {
    setIsFavorited(checkFavorite(card.id));
  }, [card.id, checkFavorite]);

  const handleFavoriteClick = async () => {
    if (!isAuthenticated) {
      // 跳转到登录页
      router.push('/login?redirect=/opportunities');
      return;
    }

    if (isFavorited) {
      await removeFavorite(card.id);
      setIsFavorited(false);
    } else {
      await addFavorite(card.id);
      setIsFavorited(true);
    }
  };

  return (
    <div className="card">
      <h3>{card.title}</h3>
      <p>{card.description}</p>
      <button onClick={handleFavoriteClick}>
        {isFavorited ? '❤️ 已收藏' : '🤍 收藏'}
      </button>
    </div>
  );
}
```

---

## 6. 服务器部署

### 6.1 部署架构图

```
┌───────────────────────────────────────────────────────────────┐
│                         阿里云ECS                             │
│                    (Jump Server: 139.224.42.111)             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  SSH跳转机                                               │  │
│  │  • 安全组限制: 仅允许本地IP访问                        │  │
│  │  • SSH密钥认证                                          │  │
│  │  • 用户: hkjump                                          │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬─────────────────────────────────┘
                              │ SSH Tunnel
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                    HK服务器 (103.59.103.85)                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Docker Network: cb-network (172.22.0.0/16)            │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  容器1: nginx-gateway                            │  │  │
│  │  │  Image: nginx:alpine                             │  │  │
│  │  │  IP: 172.22.0.5                                  │  │  │
│  │  │  Ports: 80, 443                                  │  │  │
│  │  │  Volumes:                                        │  │  │
│  │  │    - /opt/docker/nginx/conf.d:/etc/nginx/conf.d   │  │  │
│  │  │    - /opt/docker/nginx/ssl:/etc/nginx/ssl         │  │  │
│  │  │  Config: zenconsult.conf                          │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  容器2: cb-business-api-fixed                    │  │  │
│  │  │  Image: cb-business-api:latest                  │  │  │
│  │  │  IP: 172.22.0.4                                  │  │  │
│  │  │  Ports: 8000                                     │  │  │
│  │  │  Environment:                                    │  │  │
│  │  │    DATABASE_URL=postgresql+asyncpg://...         │  │  │
│  │  │    REDIS_URL=redis://172.22.0.3:6379             │  │  │
│  │  │    SECRET_KEY=${SECRET_KEY}                       │  │  │
│  │  │    OXYLABS_CREDENTIALS=...                         │  │  │
│  │  │    AIRWALLEX_API_KEY=...                          │  │  │
│  │  │  Command: uvicorn api:app --host 0.0.0.0 --port 8000│  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  容器3: cb-business-postgres                      │  │  │
│  │  │  Image: postgres:15-alpine                       │  │  │
│  │  │  IP: 172.22.0.2                                  │  │  │
│  │  │  Ports: 5432                                     │  │  │
│  │  │  Environment:                                    │  │  │
│  │  │    POSTGRES_DB=cbdb                              │  │  │
│  │  │    POSTGRES_USER=cbuser                          │  │  │
│  │  │    POSTGRES_PASSWORD=${DB_PASSWORD}              │  │  │
│  │  │  Volumes:                                        │  │  │
│  │  │    - postgres_data:/var/lib/postgresql/data       │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  容器4: cb-business-redis                         │  │  │
│  │  │  Image: redis:7-alpine                            │  │  │
│  │  │  IP: 172.22.0.3                                  │  │  │
│  │  │  Ports: 6379                                     │  │  │
│  │  │  Command: redis-server --appendonly yes           │  │  │
│  │  │  Volumes:                                        │  │  │
│  │  │    - redis_data:/data                             │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### 6.2 Docker Compose配置

```yaml
# docker-compose.yml

version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: cb-business-postgres
    networks:
      - cb-network
    environment:
      POSTGRES_DB: cbdb
      POSTGRES_USER: cbuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: cb-business-redis
    networks:
      - cb-network
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

  api:
    image: cb-business-api:latest
    container_name: cb-business-api-fixed
    networks:
      - cb-network
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql+asyncpg://cbuser:${DB_PASSWORD}@172.22.0.2:5432/cbdb
      REDIS_URL: redis://172.22.0.3:6379
      SECRET_KEY: ${SECRET_KEY}
      OXYLABS_CREDENTIALS: ${OXYLABS_CREDENTIALS}
      AIRWALLEX_API_KEY: ${AIRWALLEX_API_KEY}
    ports:
      - "8000:8000"
    restart: unless-stopped

networks:
  cb-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.22.0.0/16

volumes:
  postgres_data:
  redis_data:
```

### 6.3 Nginx配置

```nginx
# /opt/docker/nginx/conf.d/zenconsult.conf

# API upstream配置
upstream cb_business_api {
    server 172.22.0.4:8000;
    keepalive 32;
}

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name api.zenconsult.top;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS主配置
server {
    listen 443 ssl http2;
    server_name api.zenconsult.top;

    # SSL证书
    ssl_certificate /etc/nginx/ssl/api.zenconsult.top.crt;
    ssl_certificate_key /etc/nginx/ssl/api.zenconsult.top.key;

    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # 代理超时
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    # 主location - 代理所有请求到FastAPI
    location / {
        proxy_pass http://cb_business_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /health {
        proxy_pass http://cb_business_api/health;
        access_log off;
    }
}
```

### 6.4 常用运维命令

```bash
# SSH登录 (本地→阿里云→HK)
ssh hk-jump

# 查看容器状态
docker ps --filter 'network=cb-network'

# 查看容器日志
docker logs -f cb-business-api-fixed

# 重启API容器
docker restart cb-business-api-fixed

# 进入API容器
docker exec -it cb-business-api-fixed bash

# 查看Redis缓存
docker exec cb-business-redis redis-cli KEYS 'cards:*'

# 清除特定缓存
docker exec cb-business-redis redis-cli DEL 'cards:daily:wireless_earbuds'

# 数据库备份
docker exec cb-business-postgres pg_dump -U cbuser cbdb > backup.sql

# 数据库连接
docker exec -it cb-business-postgres psql -U cbuser -d cbdb

# Nginx配置重载
docker exec nginx-gateway nginx -s reload

# 查看容器资源使用
docker stats cb-business-api-fixed

# 查看容器网络
docker network inspect cb-network
```

### 6.5 SSL证书管理

```bash
# 证书位置
/opt/docker/nginx/ssl/
├── api.zenconsult.top.crt
├── api.zenconsult.top.key
└── Let's Encrypt (使用certbot自动续期)

# 证书续期
certbot renew --nginx
docker exec nginx-gateway nginx -s reload
```

---

## 7. 数据库设计

### 7.1 核心表结构

#### users (用户表)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    plan_tier VARCHAR(20) NOT NULL DEFAULT 'trial',  -- trial, free, pro
    plan_status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active, expired, locked
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_email (email),
    INDEX idx_plan_tier (plan_tier)
);
```

#### cards (卡片表)
```sql
CREATE TABLE cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(100) NOT NULL,  -- wireless_earbuds, desk_lamps, etc.
    title VARCHAR(500) NOT NULL,
    description TEXT,
    opportunity_score FLOAT DEFAULT 0,  -- 0-100
    amazon_data JSONB,  -- {products: [{asin, title, price, rating, url}]}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_category (category),
    INDEX idx_opportunity_score (opportunity_score),
    INDEX idx_created_at (created_at DESC)
);
```

#### favorites (收藏表)
```sql
CREATE TABLE favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id UUID REFERENCES cards(id) ON DELETE CASCADE,
    opportunity_id UUID REFERENCES business_opportunities(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (user_id, card_id),
    UNIQUE (user_id, opportunity_id),
    INDEX idx_user_id (user_id)
);
```

#### business_opportunities (商机表)
```sql
CREATE TABLE business_opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    status VARCHAR(20) DEFAULT 'POTENTIAL',  -- POTENTIAL, VERIFYING, APPROVED, IMPLEMENTING, COMPLETED, ARCHIVED
    grade VARCHAR(20),  -- lead, normal, priority, landable
    card_id UUID REFERENCES cards(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- C-P-I评分缓存
    cpi_total_score FLOAT,
    cpi_competition_score FLOAT,
    cpi_potential_score FLOAT,
    cpi_intelligence_gap_score FLOAT,

    -- 元数据
    grade_history JSONB DEFAULT '[]',
    last_grade_change_at TIMESTAMP WITH TIME ZONE,
    last_cpi_recalc_at TIMESTAMP WITH TIME ZONE,

    -- 用户交互数据
    user_interactions JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_grade (grade),
    INDEX idx_cpi_total_score (cpi_total_score)
);
```

#### subscriptions (订阅表)
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_tier VARCHAR(20) NOT NULL,  -- free, pro
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active, cancelled, expired
    billing_cycle VARCHAR(10),  -- monthly, yearly
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,

    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);
```

#### payments (支付表)
```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_no VARCHAR(100) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    subscription_id UUID REFERENCES subscriptions(id),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'pending',  -- pending, completed, failed, refunded
    payment_method VARCHAR(50),
    gateway_transaction_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    INDEX idx_user_id (user_id),
    INDEX idx_order_no (order_no),
    INDEX idx_status (status)
);
```

#### articles (文章表)
```sql
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000) UNIQUE NOT NULL,
    source VARCHAR(100),  -- RSS source name
    content TEXT,
    published_at TIMESTAMP WITH TIME ZONE,

    -- AI分析结果
    content_theme VARCHAR(50),  -- opportunity, risk, policy, guide
    region VARCHAR(50),  -- north_america, southeast_asia, europe, etc.
    platform VARCHAR(50),  -- amazon, shopee, lazada, etc.
    keywords JSONB,  -- ["keyword1", "keyword2", ...]
    opportunity_score FLOAT,  -- 0-1

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_content_theme (content_theme),
    INDEX idx_region (region),
    INDEX idx_opportunity_score (opportunity_score DESC)
);
```

#### user_interactions (用户交互表)
```sql
CREATE TABLE user_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    opportunity_id UUID REFERENCES business_opportunities(id) ON DELETE CASCADE,
    interaction_type VARCHAR(50),  -- view, favorite, ignore, convert, etc.
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_user_id (user_id),
    INDEX idx_opportunity_id (opportunity_id),
    INDEX idx_interaction_type (interaction_type)
);
```

#### funnel_events (漏斗事件表)
```sql
CREATE TABLE funnel_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50),  -- page_view, add_favorite, start_tracking, etc.
    resource_type VARCHAR(50),  -- card, opportunity, article
    resource_id UUID,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_user_id (user_id),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
);
```

### 7.2 数据库关系图

```
users (1) ──┬── (N) subscriptions
            │
            ├── (N) payments
            │
            ├── (N) favorites ──┬── (1) cards
            │                  │
            │                  └── (1) business_opportunities
            │
            ├── (N) business_opportunities (直接创建)
            │
            └── (N) user_interactions

cards (N) ──┬── (1) favorites
            │
            └── (N) business_opportunities

articles (独立表，用于AI分析和趋势)
```

---

## 8. 缓存策略

### 8.1 Redis缓存设计

```python
# backend/services/cache.py

class CacheService:
    """Redis缓存服务"""

    def __init__(self):
        self.redis = redis.Redis(
            host='172.22.0.3',
            port=6379,
            db=0,
            decode_responses=True
        )

    # 缓存TTL配置
    CARDS_TTL = 1800          # 卡片缓存: 30分钟
    USER_TTL = 600            # 用户信息: 10分钟
    API_RESPONSE_TTL = 300    # API响应: 5分钟

    async def get_cards(self, category: str) -> Optional[List[Card]]:
        """获取卡片缓存"""
        key = f"cards:daily:{category}"
        data = await self.redis.get(key)
        if data:
            return [Card(**item) for item in json.loads(data)]
        return None

    async def set_cards(self, category: str, cards: List[Card]):
        """设置卡片缓存"""
        key = f"cards:daily:{category}"
        data = json.dumps([card.to_dict() for card in cards])
        await self.redis.setex(key, self.CARDS_TTL, data)

    async def invalidate_cards(self, category: str = None):
        """清除卡片缓存"""
        if category:
            await self.redis.delete(f"cards:daily:{category}")
        else:
            # 清除所有卡片缓存
            keys = await self.redis.keys("cards:daily:*")
            if keys:
                await self.redis.delete(*keys)

    async def get_user(self, user_id: str) -> Optional[Dict]:
        """获取用户缓存"""
        key = f"user:{user_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_user(self, user_id: str, user_data: Dict):
        """设置用户缓存"""
        key = f"user:{user_id}"
        await self.redis.setex(key, self.USER_TTL, json.dumps(user_data))
```

### 8.2 缓存失效策略

```
触发条件:
1. 时间到期 (TTL)
2. 数据更新 (主动失效)
3. 手动刷新 (用户触发)

失效策略:
• cards表更新 → 删除对应category缓存
• 用户信息更新 → 删除user:{user_id}缓存
• 订阅状态变化 → 删除用户所有缓存
• 支付成功 → 清除用户订阅、使用量相关缓存

缓存预热:
• 启动时加载Top 3卡片到缓存
• 定时任务每6小时刷新卡片缓存
• 用户登录时缓存用户信息
```

---

## 9. 认证授权

### 9.1 JWT认证流程

```python
# backend/api/auth.py

from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

def create_access_token(data: dict, expires_delta: timedelta = None):
    """生成JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """验证JWT token，返回user_id"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None

# 依赖注入: 获取当前用户
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = verify_token(token)
    if user_id is None:
        raise credentials_exception

    user = await db.get(User, user_id)
    if user is None:
        raise credentials_exception

    return user

# 依赖注入: 检查订阅状态
async def require_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """检查用户是否有有效订阅"""
    subscription = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .where(Subscription.status == 'active')
        .order_by(Subscription.expires_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not subscription or subscription.expires_at < datetime.now():
        raise HTTPException(status_code=403, detail="需要有效订阅")

    return subscription
```

### 9.2 前端认证集成

```typescript
// API请求拦截器

const API_BASE = 'https://api.zenconsult.top';

async function apiRequest(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = localStorage.getItem('auth_token');

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  // Token过期，自动刷新
  if (response.status === 401) {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
    throw new Error('Session expired');
  }

  return response;
}
```

---

## 10. 支付集成

### 10.1 Airwallex集成架构

```
用户点击"升级"按钮
        ↓
前端: /checkout页面
        ↓
后端: POST /api/v1/payments/create
        ↓
创建支付订单记录 (payments表)
        ↓
调用Airwallex API创建支付意图
        ↓
返回支付链接 (payment_url)
        ↓
前端跳转到Airwallex Checkout页面
        ↓
用户完成支付
        ↓
Airwallex发送webhook回调
        ↓
后端: POST /api/v1/payments/webhooks/airwallex
        ↓
验证webhook签名
        ↓
更新支付状态 (completed)
        ↓
创建/更新订阅记录
        ↓
用户重定向到成功页面
```

### 10.2 Airwallex配置

```python
# backend/services/airwallex_service.py

import httpx

class AirwallexService:
    BASE_URL = "https://api.airwallex.com/v1"
    API_KEY = os.getenv("AIRWALLEX_API_KEY")

    async def create_payment_intent(
        self,
        amount: int,
        currency: str,
        user_id: str,
        description: str
    ) -> dict:
        """创建支付意图"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/payment_methods",
                headers={
                    "Authorization": f"Bearer {self.API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "request_id": str(uuid.uuid4()),
                    "amount": amount,
                    "currency": currency,
                    "merchant_order_id": f"{user_id}_{int(time.time())}",
                    "return_url": f"https://www.zenconsult.top/checkout/success",
                    "description": description
                }
            )
            return response.json()

    async def verify_webhook(self, payload: dict, signature: str) -> bool:
        """验证webhook签名"""
        # TODO: 实现签名验证
        return True
```

### 10.3 支付状态机

```
支付状态转换:
pending → completed (成功)
       → failed (失败)
       → expired (超时)

订阅状态转换:
free → trial (试用注册)
     → pro_active (支付成功)
     → pro_expired (订阅到期)

订阅到期处理:
• 保留用户数据
• 降级到free tier
• 清除高级功能访问权限
• 发送续费提醒邮件
```

---

## 附录A: 环境变量配置

```bash
# backend/.env (生产环境)

# 数据库
DATABASE_URL=postgresql+asyncpg://cbuser:PASSWORD@172.22.0.2:5432/cbdb

# Redis
REDIS_URL=redis://172.22.0.3:6379

# JWT
SECRET_KEY=your-secret-key-here

# Oxylabs
OXYLABS_CREDENTIALS=user:password

# Airwallex
AIRWALLEX_API_KEY=your-airwallex-api-key
AIRWALLEX_WEBHOOK_SECRET=your-webhook-secret

# CORS
ALLOWED_ORIGINS=https://www.zenconsult.top,https://admin.zenconsult.top
```

```bash
# frontend/.env.local

NEXT_PUBLIC_API_URL=https://api.zenconsult.top
```

---

## 附录B: 端口映射

```
服务                   内网端口    外网端口    访问方式
──────────────────────────────────────────────────
Frontend (Vercel)      -          443        https://www.zenconsult.top
API Gateway (Nginx)    80/443     443        https://api.zenconsult.top
FastAPI               8000       -          内网访问
PostgreSQL             5432       -          内网访问
Redis                  6379       -          内网访问
```

---

## 附录C: 常见问题排查

### C1. CORS错误
```bash
# 症状: "No 'Access-Control-Allow-Origin' header"
# 原因: FastAPI容器未运行最新代码
# 解决:
ssh hk-jump "docker restart cb-business-api-fixed"

# 验证:
curl -I -H 'Origin: https://www.zenconsult.top' \
  https://api.zenconsult.top/api/v1/health
```

### C2. 数据库连接错误
```bash
# 症状: "connection to server at \"172.22.0.2\", port 5432 failed"
# 原因: 容器IP变化或容器未启动
# 解决:
docker ps --filter 'network=cb-network'
docker restart cb-business-postgres
```

### C3. Redis缓存未生效
```bash
# 症状: 数据更新后前端仍显示旧数据
# 原因: Redis缓存未失效
# 解决:
ssh hk-jump "docker exec cb-business-redis redis-cli KEYS 'cards:*'"
ssh hk-jump "docker exec cb-business-redis redis-cli DEL 'cards:daily:wireless_earbuds'"
```

### C4. 支付回调失败
```bash
# 症状: 支付成功但订阅未激活
# 原因: Webhook未被调用或签名验证失败
# 解决:
1. 检查Airwallex webhook URL配置
2. 查看后端日志: docker logs -f cb-business-api-fixed | grep webhook
3. 手动触发webhook测试
```

---

**文档结束**

**维护者**: Claude Code
**最后更新**: 2026-03-15
**下次更新**: 架构或部署变更时
**相关文档**:
- `PROJECT-PROGRESS-2026-03-15.md`
- `E2E-TEST-REPORT-2026-03-15.md`
- `PROJECT-CONTEXT-2026-03-15.md`
