# 数据源架构说明

## 当前架构（V1）vs 新架构（V2）

### V1 架构 - 单一数据源
```
CardGenerator
    └─> OxylabsClient (硬编码)
         └─> Amazon产品数据
              └─> AI分析（仅基于Amazon数据）
```

**问题：**
- AI分析只基于单一数据源（Oxylabs Amazon）
- 无法轻松替换/新增数据源
- 缺少Google Trends、Reddit等重要信息
- 代码耦合严重

### V2 架构 - 多数据源聚合
```
CardGenerator
    └─> DataSourceRegistry (数据源注册中心)
         ├─> OxylabsDataSource (Amazon产品/价格/评分)
         ├─> GoogleTrendsDataSource (搜索趋势)
         ├─> RedditTrendsDataSource (社交讨论) [TODO]
         └─> RSSNewsDataSource (行业新闻) [TODO]
              └─> 并行聚合所有数据
                   └─> AI综合分析（基于所有数据源）
```

**优势：**
- ✅ AI分析基于多源数据，更全面
- ✅ 每个数据源可独立启用/禁用
- ✅ 单个数据源失败不影响整体
- ✅ 易于添加新数据源（实现DataSourceProtocol）
- ✅ 可监控每个数据源的性能

## 核心组件

### 1. DataSourceProtocol（接口协议）

所有数据源必须实现此协议：

```python
class DataSourceProtocol(Protocol):
    async def fetch_market_data(
        self, category: str, query: str, limit: int
    ) -> Dict[str, Any]:
        """返回标准化格式"""
        return {
            "source": "数据源名称",
            "products": [...],   # 产品数据
            "trends": [...],     # 趋势数据
            "sentiments": [...], # 情感数据
            "metadata": {...}    # 元数据
        }

    def get_metadata(self) -> DataSourceMetadata:
        """返回数据源元数据"""

    async def health_check(self) -> bool:
        """健康检查"""

    def is_enabled(self) -> bool:
        """是否启用"""
```

### 2. DataSourceRegistry（注册中心）

负责管理所有数据源：

```python
registry = DataSourceRegistry()

# 注册数据源
registry.register("oxylabs", OxylabsDataSource())
registry.register("google_trends", GoogleTrendsDataSource())

# 并行获取所有数据
result = await registry.fetch_all(
    category="wireless_earbuds",
    query="wireless earbuds",
    limit=20
)

# 结果包含：
# - 所有数据源的原始数据
# - 聚合后的数据
# - 成功/失败统计
```

### 3. 数据源适配器

每个数据源都有对应的适配器类：

- `OxylabsDataSource` - 包装OxylabsClient
- `GoogleTrendsDataSource` - 包装GoogleTrendsClient
- 未来可添加：RedditTrendsDataSource, RSSNewsDataSource等

## 使用方法

### 启用/禁用数据源

```python
# 禁用某个数据源
data_source_registry.get_source("google_trends").disable()

# 启用某个数据源
data_source_registry.get_source("oxylabs").enable()
```

### 查看数据源状态

```python
# 列出所有数据源
sources = data_source_registry.list_sources()

# 查看统计信息
stats = data_source_registry.get_stats()

# 只获取启用的数据源
enabled = data_source_registry.list_enabled_sources()
```

### 添加新数据源

```python
# 1. 创建数据源适配器
class MyDataSource:
    async def fetch_market_data(self, category, query, limit):
        # 实现数据获取逻辑
        return {...}

    def get_metadata(self):
        return DataSourceMetadata(...)

    async def health_check(self):
        return True

    def is_enabled(self):
        return True

# 2. 注册到registry
data_source_registry.register("my_source", MyDataSource())
```

## 数据流

```
用户访问 /api/v1/cards/daily
    ↓
CardGenerator.get_cards_for_user()
    ↓
fetch_category_data(category)
    ↓
data_source_registry.fetch_all()  [并行调用所有数据源]
    ├─> OxylabsDataSource.fetch_market_data()
    ├─> GoogleTrendsDataSource.fetch_market_data()
    └─> (其他数据源...)
    ↓
聚合结果
    ├─> products: [...]
    ├─> trends: [...]
    └─> sentiments: [...]
    ↓
analyze_with_ai(aggregated_data)  [AI综合分析]
    ├─> 价格分析（来自products）
    ├─> 趋势分析（来自trends）
    ├─> 情感分析（来自sentiments）
    └─> 综合评分（考虑所有因素）
    ↓
生成Card → 缓存 → 返回用户
```

## 迁移指南

### 从V1迁移到V2

1. **更新依赖**
```python
# 旧版本
from services.card_generator import CardGenerator

# 新版本
from services.card_generator_v2 import CardGenerator
```

2. **API兼容性**
新版本保持了相同的API接口，无需修改调用代码：
- `get_cards_for_user()` - 获取卡片
- `generate_daily_cards_task()` - 定时任务

3. **渐进式迁移**
可以先只启用Oxylabs数据源，逐步添加其他数据源：

```python
# data_source_init.py
oxylabs_source = OxylabsDataSource(enabled=True)
data_source_registry.register("oxylabs", oxylabs_source)

# 逐步添加
# google_trends_source = GoogleTrendsDataSource(enabled=True)
# data_source_registry.register("google_trends", google_trends_source)
```

## 性能优化

### 并行调用
所有数据源并行调用，总耗时 = max(单个数据源耗时)

### 超时控制
每个数据源有独立的超时时间（默认30秒）

### 缓存策略
- 聚合结果缓存30分钟
- 单个数据源可独立配置缓存

### 降级策略
- 某个数据源失败时，使用其他数据源的数据
- 所有数据源失败时，返回过期缓存

## 监控指标

每个数据源跟踪：
- 总调用次数
- 成功/失败次数
- 平均响应时间
- 最后成功时间
- 当前状态

```python
stats = data_source_registry.get_stats()
# {
#     "oxylabs": {
#         "total_calls": 100,
#         "success_calls": 95,
#         "failed_calls": 5,
#         "avg_latency_ms": 3000
#     },
#     ...
# }
```

## 未来扩展

### 计划添加的数据源

1. **Reddit Trends** - 社交媒体讨论趋势
2. **RSS News** - 行业新闻和资讯
3. **Shopee** - 东南亚电商平台数据
4. **Lazada** - 东南亚电商平台数据
5. **TikTok Shop** - 社交电商数据

### AI能力增强

1. **多模态分析** - 整合文本、图像、视频数据
2. **时序分析** - 追踪趋势变化
3. **预测模型** - 基于历史数据预测市场趋势
4. **情感分析** - 深度理解用户讨论情感

### 优化方向

1. **智能缓存** - 根据数据更新频率动态调整缓存时间
2. **增量更新** - 只获取变化的数据，减少API调用
3. **分布式处理** - 使用消息队列异步处理数据获取
4. **边缘计算** - 在多个地区部署数据获取节点
