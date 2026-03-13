# services/data_source_init.py
"""数据源初始化和注册

在应用启动时调用，注册所有可用的数据源到全局registry
"""

import logging
from services.data_source_registry import data_source_registry
from services.data_sources import (
    OxylabsDataSource,
    GoogleTrendsDataSource
)

logger = logging.getLogger(__name__)


async def initialize_data_sources():
    """初始化并注册所有数据源"""

    # 1. Oxylabs - 主要电商数据源
    oxylabs_source = OxylabsDataSource(enabled=True)
    data_source_registry.register("oxylabs", oxylabs_source)

    # 2. Google Trends - 搜索趋势数据
    google_trends_source = GoogleTrendsDataSource(enabled=True)
    data_source_registry.register("google_trends", google_trends_source)

    # TODO: 未来可添加更多数据源
    # 3. Reddit Trends - 社交媒体趋势
    # from services.data_sources.reddit_trends_source import RedditTrendsDataSource
    # reddit_source = RedditTrendsDataSource(enabled=False)  # 默认禁用
    # data_source_registry.register("reddit_trends", reddit_source)

    # 4. RSS News Sources - 行业新闻
    # from services.data_sources.rss_news_source import RSSNewsDataSource
    # rss_source = RSSNewsDataSource(enabled=False)
    # data_source_registry.register("rss_news", rss_source)

    # 5. Shopee Trending - 东南亚电商数据
    # from services.data_sources.shopee_source import ShopeeDataSource
    # shopee_source = ShopeeDataSource(enabled=False)
    # data_source_registry.register("shopee", shopee_source)

    # 打印注册结果
    sources = data_source_registry.list_sources()
    logger.info(f"✅ 已注册 {len(sources)} 个数据源:")
    for source_meta in sources:
        status = "✅ 启用" if source_meta.status.value == "active" else "❌ 禁用"
        logger.info(f"   - {source_meta.name}: {status} (可靠性: {source_meta.reliability})")

    return data_source_registry


def get_enabled_data_sources_count() -> int:
    """获取启用的数据源数量"""
    return len(data_source_registry.list_enabled_sources())
