# models/standardized_product.py
"""标准化产品数据模型 - 多平台数据统一格式

设计目标：
1. 统一不同电商平台（Amazon, Lazada, Shopee等）的产品数据格式
2. 支持跨平台数据聚合和对比
3. 为 CPI 算法提供标准化输入
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class Platform(str, Enum):
    """支持的平台"""
    AMAZON = "amazon"
    LAZADA = "lazada"
    SHOPEE = "shopee"
    TEMU = "temu"
    EBAY = "ebay"
    WALMART = "walmart"


class Region(str, Enum):
    """支持的区域"""
    # 欧美
    US = "US"  # 美国
    UK = "UK"  # 英国
    DE = "DE"  # 德国
    JP = "JP"  # 日本
    AU = "AU"  # 澳洲

    # 东南亚
    TH = "TH"  # 泰国
    VN = "VN"  # 越南
    MY = "MY"  # 马来西亚
    SG = "SG"  # 新加坡
    ID = "ID"  # 印尼
    PH = "PH"  # 菲律宾

    # 拉美
    BR = "BR"  # 巴西
    MX = "MX"  # 墨西哥


@dataclass
class PriceInfo:
    """价格信息"""
    current: float  # 当前价格
    original: Optional[float] = None  # 原价
    currency: str = "USD"  # 货币

    @property
    def discount_rate(self) -> Optional[float]:
        """折扣率"""
        if self.original and self.original > 0:
            return 1 - (self.current / self.original)
        return None


@dataclass
class RatingInfo:
    """评分信息"""
    average: float  # 平均评分
    count: int  # 评论数

    @property
    def reliability(self) -> float:
        """评分可靠性 (基于评论数)"""
        if self.count >= 100:
            return 0.95
        elif self.count >= 50:
            return 0.85
        elif self.count >= 20:
            return 0.7
        elif self.count >= 10:
            return 0.5
        return 0.3


@dataclass
class SellerInfo:
    """卖家信息"""
    seller_id: Optional[str] = None
    seller_name: Optional[str] = None
    is_official: bool = False  # 是否官方店
    seller_count: int = 1  # 同类产品卖家数（用于竞争分析）


@dataclass
class TrendInfo:
    """趋势信息"""
    google_trends_score: Optional[float] = None  # Google Trends 分数 (0-100)
    growth_rate: Optional[float] = None  # 增长率
    trend_rank: Optional[int] = None  # 热销排名
    is_best_seller: bool = False


@dataclass
class StandardizedProduct:
    """
    标准化产品数据模型

    统一不同电商平台的产品数据格式，支持跨平台分析。
    """
    # 基本信息
    product_id: str  # 平台产品ID
    platform: Platform
    region: Region
    title: str
    url: Optional[str] = None
    image_url: Optional[str] = None

    # 分类
    category: Optional[str] = None  # 品类标识 (wireless_earbuds, etc.)
    category_name: Optional[str] = None  # 品类名称
    brand: Optional[str] = None

    # 价格
    price: PriceInfo

    # 评分
    rating: RatingInfo

    # 卖家
    seller: SellerInfo = field(default_factory=SellerInfo)

    # 趋势
    trend: TrendInfo = field(default_factory=TrendInfo)

    # 销量
    sold_count: int = 0
    stock_status: str = "in_stock"  # in_stock, low_stock, out_of_stock

    # 时间戳
    fetched_at: datetime = field(default_factory=datetime.utcnow)

    # 原始数据（用于调试）
    raw_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "product_id": self.product_id,
            "platform": self.platform.value,
            "region": self.region.value,
            "title": self.title,
            "url": self.url,
            "image_url": self.image_url,
            "category": self.category,
            "category_name": self.category_name,
            "brand": self.brand,
            "price": {
                "current": self.price.current,
                "original": self.price.original,
                "currency": self.price.currency,
                "discount_rate": self.price.discount_rate,
            },
            "rating": {
                "average": self.rating.average,
                "count": self.rating.count,
                "reliability": self.rating.reliability,
            },
            "seller": {
                "seller_id": self.seller.seller_id,
                "seller_name": self.seller.seller_name,
                "is_official": self.seller.is_official,
                "seller_count": self.seller.seller_count,
            },
            "trend": {
                "google_trends_score": self.trend.google_trends_score,
                "growth_rate": self.trend.growth_rate,
                "trend_rank": self.trend.trend_rank,
                "is_best_seller": self.trend.is_best_seller,
            },
            "sold_count": self.sold_count,
            "stock_status": self.stock_status,
            "fetched_at": self.fetched_at.isoformat(),
        }

    @classmethod
    def from_amazon(cls, data: Dict[str, Any], region: Region = Region.US) -> "StandardizedProduct":
        """从 Amazon 数据创建"""
        return cls(
            product_id=data.get("asin", ""),
            platform=Platform.AMAZON,
            region=region,
            title=data.get("title", ""),
            url=data.get("url") or f"https://www.amazon.{region.value.lower()}/dp/{data.get('asin', '')}",
            image_url=data.get("image_url"),
            category=data.get("category"),
            brand=data.get("brand"),
            price=PriceInfo(
                current=float(data.get("price", 0) or 0),
                currency="USD" if region == Region.US else "LOCAL",
            ),
            rating=RatingInfo(
                average=float(data.get("rating", 0) or 0),
                count=int(data.get("reviews_count", 0) or 0),
            ),
            seller=SellerInfo(
                seller_name=data.get("seller_name"),
            ),
            trend=TrendInfo(
                trend_rank=data.get("rank"),
                is_best_seller=data.get("is_best_seller", False),
            ),
            sold_count=int(data.get("sold_count", 0) or 0),
            raw_data=data,
        )

    @classmethod
    def from_lazada(cls, data: Dict[str, Any], region: Region = Region.TH) -> "StandardizedProduct":
        """从 Lazada 数据创建"""
        return cls(
            product_id=str(data.get("item_id", "")),
            platform=Platform.LAZADA,
            region=region,
            title=data.get("title", ""),
            url=data.get("product_url"),
            image_url=data.get("image_url"),
            category=data.get("category"),
            brand=data.get("brand"),
            price=PriceInfo(
                current=float(data.get("price", 0) or 0),
                original=data.get("original_price"),
                currency="THB" if region == Region.TH else "LOCAL",
            ),
            rating=RatingInfo(
                average=float(data.get("rating", 0) or 0),
                count=int(data.get("reviews_count", 0) or 0),
            ),
            seller=SellerInfo(
                seller_id=str(data.get("shop_id", "")),
            ),
            trend=TrendInfo(
                trend_rank=data.get("trend_rank"),
                is_best_seller=data.get("is_best_seller", False),
            ),
            sold_count=int(data.get("sold_count", 0) or 0),
            raw_data=data,
        )

    @classmethod
    def from_shopee(cls, data: Dict[str, Any], region: Region = Region.TH) -> "StandardizedProduct":
        """从 Shopee 数据创建"""
        return cls(
            product_id=str(data.get("item_id", "")),
            platform=Platform.SHOPEE,
            region=region,
            title=data.get("title", ""),
            url=data.get("product_url"),
            image_url=data.get("image_url"),
            category=data.get("category"),
            brand=data.get("brand"),
            price=PriceInfo(
                current=float(data.get("price", 0) or 0),
                original=data.get("original_price"),
                currency="THB" if region == Region.TH else "LOCAL",
            ),
            rating=RatingInfo(
                average=float(data.get("rating", 0) or 0),
                count=int(data.get("reviews_count", 0) or 0),
            ),
            seller=SellerInfo(
                seller_id=str(data.get("shop_id", "")),
            ),
            trend=TrendInfo(
                trend_rank=data.get("trend_rank"),
                is_best_seller=data.get("is_best_seller", False),
            ),
            sold_count=int(data.get("sold_count", 0) or 0),
            raw_data=data,
        )


@dataclass
class AggregatedProducts:
    """
    聚合产品数据

    包含来自多个平台的同类产品数据，用于跨平台分析。
    """
    category: str  # 品类标识
    query: str  # 搜索关键词

    # 多平台产品数据
    products_by_platform: Dict[str, List[StandardizedProduct]] = field(default_factory=dict)

    # 聚合统计
    total_products: int = 0
    platforms_count: int = 0

    # 价格统计（跨平台）
    price_min: float = 0
    price_max: float = 0
    price_median: float = 0
    price_avg: float = 0

    # 评分统计
    rating_avg: float = 0
    rating_weighted_avg: float = 0  # 按评论数加权

    # 竞争度
    total_sellers: int = 0
    avg_sellers_per_platform: float = 0

    # 趋势
    avg_google_trends_score: Optional[float] = None
    best_seller_count: int = 0

    # 元数据
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    data_sources: List[str] = field(default_factory=list)

    def add_products(self, platform: str, products: List[StandardizedProduct]):
        """添加平台产品"""
        self.products_by_platform[platform] = products
        self._recalculate()

    def _recalculate(self):
        """重新计算聚合统计"""
        all_products = []
        for prods in self.products_by_platform.values():
            all_products.extend(prods)

        self.total_products = len(all_products)
        self.platforms_count = len(self.products_by_platform)

        if not all_products:
            return

        # 价格统计
        prices = [p.price.current for p in all_products if p.price.current > 0]
        if prices:
            self.price_min = min(prices)
            self.price_max = max(prices)
            self.price_avg = sum(prices) / len(prices)
            sorted_prices = sorted(prices)
            mid = len(sorted_prices) // 2
            self.price_median = sorted_prices[mid]

        # 评分统计
        ratings = [(p.rating.average, p.rating.count) for p in all_products if p.rating.count > 0]
        if ratings:
            self.rating_avg = sum(r[0] for r in ratings) / len(ratings)
            total_reviews = sum(r[1] for r in ratings)
            if total_reviews > 0:
                self.rating_weighted_avg = sum(r[0] * r[1] for r in ratings) / total_reviews

        # 竞争度
        self.total_sellers = sum(
            p.seller.seller_count for p in all_products
            if p.seller.seller_count > 0
        ) or len(all_products)

        # 趋势
        trends_scores = [
            p.trend.google_trends_score
            for p in all_products
            if p.trend.google_trends_score is not None
        ]
        if trends_scores:
            self.avg_google_trends_score = sum(trends_scores) / len(trends_scores)

        self.best_seller_count = sum(
            1 for p in all_products if p.trend.is_best_seller
        )

        self.data_sources = list(self.products_by_platform.keys())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "category": self.category,
            "query": self.query,
            "total_products": self.total_products,
            "platforms_count": self.platforms_count,
            "platforms": list(self.products_by_platform.keys()),
            "price": {
                "min": self.price_min,
                "max": self.price_max,
                "median": self.price_median,
                "avg": self.price_avg,
            },
            "rating": {
                "avg": self.rating_avg,
                "weighted_avg": self.rating_weighted_avg,
            },
            "competition": {
                "total_sellers": self.total_sellers,
                "avg_sellers_per_platform": self.avg_sellers_per_platform,
            },
            "trend": {
                "avg_google_trends_score": self.avg_google_trends_score,
                "best_seller_count": self.best_seller_count,
            },
            "fetched_at": self.fetched_at.isoformat(),
            "data_sources": self.data_sources,
        }
