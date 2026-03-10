# crawler/config.py
from typing import Dict, Any

CRAWLER_SOURCES: Dict[str, Dict[str, Any]] = {
    "retail_dive": {
        "name": "Retail Dive",
        "type": "rss",
        "url": "https://retaildive.com/feed/",
        "update_interval": 3600,  # 1小时
        "enabled": True,
        "language": "en",
    },
    "shopify_blog": {
        "name": "Shopify Blog",
        "type": "rss",
        "url": "https://www.shopify.com/blog.xml",
        "update_interval": 3600,
        "enabled": True,
        "language": "en",
    },
    "cifnews": {
        "name": "雨果网",
        "type": "http",
        "base_url": "https://www.cifnews.com",
        "list_url": "/Category/1-1.html",  # 跨境电商栏目
        "update_interval": 7200,  # 2小时
        "enabled": True,
        "language": "zh",
    },
    "tech_crunch": {
        "name": "TechCrunch",
        "type": "rss",
        "url": "https://techcrunch.com/feed/",
        "update_interval": 3600,
        "enabled": False,  # 默认关闭，可通过环境变量启用
        "language": "en",
    },
}

# 内容分类映射
CONTENT_CATEGORIES = {
    "opportunity": "商机发现",
    "risk": "风险预警",
    "policy": "政策变化",
    "guide": "实操指南",
    "market": "市场趋势",
    "platform": "平台动态",
}

# 地区映射
REGIONS = {
    "southeast_asia": "东南亚",
    "north_america": "北美",
    "europe": "欧洲",
    "latin_america": "拉美",
    "global": "全球",
}

# 平台映射
PLATFORMS = {
    "amazon": "亚马逊",
    "shopee": "Shopee",
    "lazada": "Lazada",
    "shopify": "Shopify",
    "woocommerce": "WooCommerce",
    "tiktok": "TikTok",
    "other": "其他",
}


def get_enabled_sources() -> Dict[str, Dict[str, Any]]:
    """获取已启用的数据源"""
    return {
        k: v for k, v in CRAWLER_SOURCES.items()
        if v.get("enabled", False)
    }


def get_source_config(source_name: str) -> Dict[str, Any]:
    """获取数据源配置"""
    return CRAWLER_SOURCES.get(source_name, {})
