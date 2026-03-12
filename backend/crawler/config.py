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

    # ===== 新增：东南亚科技媒体（扩展） =====
    "dealstreet_asia": {
        "name": "DealStreetAsia",
        "type": "rss",
        "url": "https://www.dealstreetasia.com/feed/",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "krasia": {
        "name": "KrASIA",
        "type": "rss",
        "url": "https://kr-asia.com/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "techinasia_forum": {
        "name": "Tech in Asia Community",
        "type": "rss",
        "url": "https://www.techinasia.com/feed/",  # 已有tech_in_asia，保留原配置
        "update_interval": 1800,
        "enabled": False,  # 避免重复
        "language": "en",
    },

    # ===== 新增：东南亚本地媒体 =====
    "vietnam_news": {
        "name": "Vietnam News",
        "type": "rss",
        "url": "https://vietnamnews.vn/economy/rss",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "bangkok_post_business": {
        "name": "Bangkok Post Business",
        "type": "rss",
        "url": "https://www.bangkokpost.com/rss/data/business.xml",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "kompas_ekonomi": {
        "name": "Kompas Ekonomi",
        "type": "rss",
        "url": "https://ecomedia.kompas.com/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "id",
    },
    "philstar_business": {
        "name": "Philippine Star Business",
        "type": "rss",
        "url": "https://www.philstar.com/business/rss",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "manila_bulletin_business": {
        "name": "Manila Bulletin Business",
        "type": "rss",
        "url": "https://mb.com.ph/feed/category/business/",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "straitstimes_business": {
        "name": "Straits Times Business",
        "type": "rss",
        "url": "https://www.straitstimes.com/news/business/rss.xml",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "the_star_business": {
        "name": "The Star Business (Malaysia)",
        "type": "rss",
        "url": "https://www.thestar.com.my/business/rss/",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },

    # ===== 新增：拉美市场扩展 =====
    "neobiz": {
        "name": "Neobiz",
        "type": "rss",
        "url": "https://neobiz.com.br/blog/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "pt",
    },
    "ecommerce_brasil": {
        "name": "E-commerce Brasil",
        "type": "rss",
        "url": "https://ecommercebrasil.com.br/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "pt",
    },
    "webcapitalista": {
        "name": "Webcapitalista",
        "type": "rss",
        "url": "https://webcapitalista.com/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "es",
    },
    "ecommerce_news_latam": {
        "name": "Ecommerce News Latin America",
        "type": "rss",
        "url": "https://ecommercenews.com/feed/",
        "update_interval": 1800,
        "enabled": True,
        "language": "es",
    },

    # ===== 新增：平台官方博客（扩展） =====
    "tiktok_seller_blog": {
        "name": "TikTok Shop Blog",
        "type": "rss",
        "url": "https://sellertik.tiktok.com/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "shopify_blog_en": {
        "name": "Shopify Blog (Enabled)",
        "type": "rss",
        "url": "https://www.shopify.com/blog.xml",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "bigcommerce_blog": {
        "name": "BigCommerce Blog",
        "type": "rss",
        "url": "https://www.bigcommerce.com/blog/rss.xml",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "wix_blog": {
        "name": "Wix Ecommerce Blog",
        "type": "rss",
        "url": "https://www.wix.com/blog/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },

    # ===== 新增：电商研究机构 =====
    "internet_retailing": {
        "name": "Internet Retailing",
        "type": "rss",
        "url": "https://www.internetretailing.com/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "retail_touchpoints": {
        "name": "Retail TouchPoints",
        "type": "rss",
        "url": "https://retailtouchpoints.com/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "practicale_commerce": {
        "name": "Practical Ecommerce",
        "type": "rss",
        "url": "https://www.practicalecommerce.com/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "ecommerce_times": {
        "name": "Ecommerce Times",
        "type": "rss",
        "url": "https://www.ecommerces times.com/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "digital_commerce_news": {
        "name": "Digital Commerce News",
        "type": "rss",
        "url": "https://www.digitalcommerce360.com/feed/",  # 已有digital_commerce_360
        "update_interval": 1800,
        "enabled": False,  # 避免重复
        "language": "en",
    },

    # ===== 新增：支付与金融科技 =====
    "stripe_blog_rss": {
        "name": "Stripe Blog (RSS)",
        "type": "rss",
        "url": "https://stripe.com/blog/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "braintree_blog": {
        "name": "Braintree Blog",
        "type": "rss",
        "url": "https://www.braintreepayments.com/blog/rss.xml",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "adyen_blog": {
        "name": "Adyen Blog",
        "type": "rss",
        "url": "https://www.adyen.com/blog/rss.xml",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },

    # ===== 新增：物流与供应链 =====
    "dhl_logistics": {
        "name": "DHL Logistics Insights",
        "type": "rss",
        "url": "https://www.dhl.com/en/about-us/logistics-insights.html",
        "update_interval": 3600,
        "enabled": True,
        "language": "en",
    },
    "flexport_blog": {
        "name": "Flexport Blog",
        "type": "rss",
        "url": "https://www.flexport.com/blog/feed",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },

    # ===== 新增：中国跨境电商媒体（扩展） =====
    "cifnews_en": {
        "name": "Cifnews English",
        "type": "rss",
        "url": "https://en.cifnews.com/",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "cross_border_mag": {
        "name": "Cross Border Magazine",
        "type": "rss",
        "url": "https://www.crossborder-mag.com/feed/",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },

    # ===== 新增：移动电商 =====
    "appannie_blog": {
        "name": "App Annie Blog",
        "type": "rss",
        "url": "https://www.appannie.com/en/blog/",
        "update_interval": 1800,
        "enabled": True,
        "language": "en",
    },
    "sensortower": {
        "name": "Sensor Tower Blog",
        "type": "rss",
        "url": "https://sensortower.com/blog/",
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
