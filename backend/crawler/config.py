# crawler/config.py
from typing import Dict, Any

CRAWLER_SOURCES: Dict[str, Dict[str, Any]] = {
    # ===== 现有数据源 =====
    "retail_dive": {
        "name": "Retail Dive",
        "type": "rss",
        "url": "https://www.retaildive.com/feeds/news/",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "shopify_blog": {
        "name": "Shopify Blog",
        "type": "rss",
        "url": "https://www.shopify.com/blog.xml",
        "update_interval": 1800,
        "enabled": False,
        "language": "en",
    },
    "cifnews": {
        "name": "雨果网",
        "type": "http",
        "base_url": "https://www.cifnews.com",
        "list_url": "/Category/1-1.html",
        "update_interval": 1800,
        "enabled": True,
        "language": "zh",
    },
    "techcrunch": {
        "name": "TechCrunch",
        "type": "rss",
        "url": "https://techcrunch.com/feed/",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },

    # ===== 电商行业权威媒体 =====
    "digital_commerce_360": {
        "name": "Digital Commerce 360",
        "type": "rss",
        "url": "https://www.digitalcommerce360.com/feed/",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "ecommerce_bytes": {
        "name": "EcommerceBytes",
        "type": "rss",
        "url": "https://www.ecommercebytes.com/feed/",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "pymnts": {
        "name": "PYMNTS",
        "type": "rss",
        "url": "https://www.pymnts.com/feed/",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },

    # ===== 平台官方博客 =====
    "amazon_seller_news": {
        "name": "Amazon Seller News",
        "type": "rss",
        "url": "https://sell.amazonpress.com/feed/",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "ebay_seller_news": {
        "name": "eBay Seller News",
        "type": "rss",
        "url": "https://www.ebayinc.com/stories/feed/",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },

    # ===== 支付与物流 =====
    "paypal_blog": {
        "name": "PayPal Blog",
        "type": "rss",
        "url": "https://www.paypal.com/us/webapps/mpp/blog/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "stripe_blog": {
        "name": "Stripe Blog",
        "type": "rss",
        "url": "https://stripe.com/blog/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },

    # ===== 东南亚科技媒体 =====
    "tech_in_asia": {
        "name": "Tech in Asia",
        "type": "rss",
        "url": "https://www.techinasia.com/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "e27": {
        "name": "e27",
        "type": "rss",
        "url": "https://e27.co/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },

    # ===== 电商研究 =====
    "emarketer": {
        "name": "eMarketer",
        "type": "rss",
        "url": "https://www.emarketer.com/rss",
        "update_interval": 3600,
        "enabled": True,
        "language": "en",
    },

    # ===== 中国跨境电商媒体 =====
    "ennews": {
        "name": "亿恩网",
        "type": "rss",
        "url": "https://www.ennews.com/rss.xml",
        "update_interval": 1800,
        "enabled": True,
        "language": "zh",
    },

    # ===== 拉美市场 =====
    "mercopress": {
        "name": "Mercopress",
        "type": "rss",
        "url": "https://en.mercopress.com/rss/",
        "update_interval": 1800,
        "enabled": True,
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
