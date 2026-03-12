# crawler/products/lazada_api.py
"""Lazada Open Platform API 客户端"""

import hashlib
import hmac
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlencode
import httpx

logger = logging.getLogger(__name__)


@dataclass
class LazadaConfig:
    """Lazada API 配置"""
    app_key: str
    app_secret: str
    country: str  # th, vn, my, sg, id, ph
    access_token: Optional[str] = None

    # API 端点配置
    API_ENDPOINTS = {
        "th": "https://api.lazada.co.th",
        "vn": "https://api.lazada.vn",
        "my": "https://api.lazada.com.my",
        "sg": "https://api.lazada.sg",
        "id": "https://api.lazada.co.id",
        "ph": "https://api.lazada.ph",
    }

    @property
    def api_base(self) -> str:
        """获取当前国家的 API 端点"""
        return self.API_ENDPOINTS.get(self.country, "https://api.lazada.sg")


@dataclass
class LazadaProduct:
    """Lazada 商品数据模型"""
    item_id: str
    title: str
    price: float
    original_price: Optional[float] = None
    sold_count: int = 0
    rating: Optional[float] = None
    reviews_count: int = 0
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    category: Optional[str] = None
    shop_id: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    country: str = None
    platform: str = "lazada"

    # 趋势数据
    trend_rank: Optional[int] = None
    is_best_seller: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "item_id": self.item_id,
            "title": self.title,
            "price": self.price,
            "original_price": self.original_price,
            "sold_count": self.sold_count,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "image_url": self.image_url,
            "product_url": self.product_url,
            "category": self.category,
            "shop_id": self.shop_id,
            "brand": self.brand,
            "description": self.description,
            "country": self.country,
            "platform": self.platform,
            "trend_rank": self.trend_rank,
            "is_best_seller": self.is_best_seller,
        }


@dataclass
class LazadaReview:
    """Lazada 评论数据模型"""
    review_id: str
    product_id: str
    rating: int
    title: Optional[str] = None
    content: Optional[str] = None
    author_name: Optional[str] = None
    review_date: Optional[str] = None
    helpful_count: int = 0
    images: List[str] = None

    def __post_init__(self):
        if self.images is None:
            self.images = []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "review_id": self.review_id,
            "product_id": self.product_id,
            "rating": self.rating,
            "title": self.title,
            "content": self.content,
            "author_name": self.author_name,
            "review_date": self.review_date,
            "helpful_count": self.helpful_count,
            "images": self.images,
        }


class LazadaAPIClient:
    """Lazada Open Platform API 客户端"""

    def __init__(self, config: LazadaConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        生成 API 签名

        Lazada API 签名算法:
        1. 将参数按 key 字母顺序排序
        2. 拼接成 key=value&key=value 格式
        3. 在前面拼接 app_key
        4. 在后面拼接参数字符串（不含app_key）
        5. HMAC-SHA256 计算，使用 app_secret
        """
        # 移除空值和签名字段
        filtered_params = {k: v for k, v in params.items() if v is not None and v != ''}

        # 按字母顺序排序
        sorted_params = sorted(filtered_params.items())

        # 拼接参数字符串
        param_string = '&'.join([f"{k}={v}" for k, v in sorted_params if k != 'sign'])

        # 拼接 app_key
        string_to_sign = f"{self.config.app_key}{param_string}"

        # 计算 HMAC-SHA256
        signature = hmac.new(
            self.config.app_secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()

        return signature

    def _build_common_params(self, method: str) -> Dict[str, Any]:
        """构建通用参数"""
        return {
            'app_key': self.config.app_key,
            'timestamp': int(time.time() * 1000),
            'sign_method': 'sha256',
            'method': method,
            'format': 'json',
            'v': '2.0',
        }

    async def _call_api(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        调用 Lazada API

        Args:
            method: API 方法名，如 '/products/get'
            params: 请求参数
            access_token: 访问令牌（如果需要）

        Returns:
            API 响应数据
        """
        # 构建基础参数
        request_params = self._build_common_params(method)

        # 添加业务参数
        if params:
            request_params.update(params)

        # 添加 access_token（如果需要）
        if access_token:
            request_params['access_token'] = access_token
        elif self.config.access_token:
            request_params['access_token'] = self.config.access_token

        # 生成签名
        request_params['sign'] = self._generate_signature(request_params)

        # 发送请求
        url = f"{self.config.api_base}/rest"
        logger.info(f"调用 Lazada API: {method}")

        try:
            response = await self.client.post(url, data=request_params)
            response.raise_for_status()

            data = response.json()

            # 检查错误响应
            if 'code' in data and data['code'] != '0':
                error_msg = data.get('message', 'Unknown error')
                logger.error(f"Lazada API 错误: {error_msg}")
                raise Exception(f"Lazada API error: {error_msg}")

            return data

        except httpx.HTTPError as e:
            logger.error(f"HTTP 请求失败: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            raise

    # ==================== 商品相关接口 ====================

    async def get_products(
        self,
        filter_value: Optional[str] = None,
        created_after: Optional[str] = None,
        updated_after: Optional[str] = None,
        offset: int = 0,
        limit: int = 50
    ) -> List[LazadaProduct]:
        """
        获取商品列表

        Args:
            filter_value: 筛选条件 (all, live, inactive, deleted, image-missing)
            created_after: 创建时间之后
            updated_after: 更新时间之后
            offset: 偏移量
            limit: 返回数量 (最大50)

        Returns:
            商品列表
        """
        params = {
            'filter': filter_value or 'all',
            'offset': offset,
            'limit': min(limit, 50),
        }

        if created_after:
            params['created_after'] = created_after
        if updated_after:
            params['updated_after'] = updated_after

        # 注意: /products/get 需要卖家授权的 access_token
        # 如果获取他人商品数据，可能需要使用其他接口
        response = await self._call_api('/products/get', params)

        products = []
        if 'data' in response and 'products' in response['data']:
            for item in response['data']['products']:
                product = self._parse_product(item)
                products.append(product)

        return products

    async def get_product_details(self, item_id: str) -> Optional[LazadaProduct]:
        """
        获取单个商品详情

        Args:
            item_id: 商品ID

        Returns:
            商品详情
        """
        params = {'item_id': item_id}

        response = await self._call_api('/product/item/get', params)

        if 'data' in response:
            return self._parse_product(response['data'])

        return None

    async def search_products(
        self,
        keyword: str,
        offset: int = 0,
        limit: int = 20
    ) -> List[LazadaProduct]:
        """
        搜索商品

        注意: Lazada API 是否提供公开搜索接口需要确认
        此方法基于常见 API 设计，具体端点需要查阅文档

        Args:
            keyword: 搜索关键词
            offset: 偏移量
            limit: 返回数量

        Returns:
            商品列表
        """
        # TODO: 确认 Lazada 是否提供公开搜索接口
        # 可能需要使用爬虫或其他方案
        logger.warning("Lazada 公开搜索接口待确认")
        return []

    def _parse_product(self, data: Dict[str, Any]) -> LazadaProduct:
        """解析商品数据"""
        return LazadaProduct(
            item_id=str(data.get('item_id', '')),
            title=data.get('title', ''),
            price=float(data.get('price', {}).get('currency', '0').replace(',', '')),
            original_price=float(data.get('original_price', {}).get('currency', '0').replace(',', '')) if data.get('original_price') else None,
            sold_count=int(data.get('sold_count', 0)),
            rating=float(data.get('rating_star', 0)) if data.get('rating_star') else None,
            reviews_count=int(data.get('review_count', 0)),
            image_url=data.get('images', [None])[0] if data.get('images') else None,
            product_url=data.get('url', ''),
            category=data.get('primary_category', {}).get('name', '') if data.get('primary_category') else None,
            shop_id=str(data.get('seller_id', '')),
            brand=data.get('brand', ''),
            description=data.get('description', ''),
            country=self.config.country,
            platform='lazada',
        )

    # ==================== 评论相关接口 ====================

    async def get_product_reviews(
        self,
        item_id: str,
        offset: int = 0,
        limit: int = 20
    ) -> List[LazadaReview]:
        """
        获取商品评论列表

        注意: 此接口端点需要确认，基于 Alibaba 文档提及

        Args:
            item_id: 商品ID
            offset: 偏移量
            limit: 返回数量

        Returns:
            评论列表
        """
        params = {
            'item_id': item_id,
            'offset': offset,
            'limit': min(limit, 100),
        }

        # TODO: 确认评论接口端点
        # 可能是 /product/review/list 或类似
        response = await self._call_api('/product/review/list', params)

        reviews = []
        if 'data' in response and 'reviews' in response['data']:
            for item in response['data']['reviews']:
                review = self._parse_review(item, item_id)
                reviews.append(review)

        return reviews

    def _parse_review(self, data: Dict[str, Any], product_id: str) -> LazadaReview:
        """解析评论数据"""
        return LazadaReview(
            review_id=str(data.get('review_id', '')),
            product_id=product_id,
            rating=int(data.get('rating_star', 0)),
            title=data.get('review_title', ''),
            content=data.get('review_content', ''),
            author_name=data.get('review_author_name', ''),
            review_date=data.get('review_date', ''),
            helpful_count=int(data.get('helpful', 0)),
            images=data.get('images', []),
        )

    # ==================== 热销/排行榜接口 ====================

    async def get_category_tree(self) -> List[Dict[str, Any]]:
        """
        获取分类树

        Returns:
            分类列表
        """
        response = await self._call_api('/category/tree/get')

        if 'data' in response and 'categories' in response['data']:
            return response['data']['categories']

        return []

    async def get_products_by_category(
        self,
        category_id: str,
        offset: int = 0,
        limit: int = 50
    ) -> List[LazadaProduct]:
        """
        获取指定分类下的商品

        注意: 此接口端点需要确认

        Args:
            category_id: 分类ID
            offset: 偏移量
            limit: 返回数量

        Returns:
            商品列表
        """
        # TODO: 确认按分类获取商品的接口
        params = {
            'category_id': category_id,
            'offset': offset,
            'limit': min(limit, 50),
        }

        response = await self._call_api('/products/get', params)

        products = []
        if 'data' in response and 'products' in response['data']:
            for item in response['data']['products']:
                product = self._parse_product(item)
                products.append(product)

        return products


# ==================== OAuth 认证相关 ====================

class LazadaOAuthClient:
    """Lazada OAuth 认证客户端"""

    AUTH_URL = "https://auth.lazada.com/rest"

    def __init__(self, app_key: str, app_secret: str, redirect_uri: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    def get_authorization_url(self, country: str = 'th') -> str:
        """
        生成授权URL

        Args:
            country: 国家代码

        Returns:
            授权URL，用户需要在浏览器中打开此URL进行授权
        """
        params = {
            'response_type': 'code',
            'force_auth': 'true',
            'client_id': self.app_key,
            'redirect_uri': self.redirect_uri,
        }

        # 不同国家可能使用不同的授权URL
        country_urls = {
            'th': 'https://auth.lazada.co.th',
            'vn': 'https://auth.lazada.vn',
            'my': 'https://auth.lazada.com.my',
            'sg': 'https://auth.lazada.com.sg',
            'id': 'https://auth.lazada.co.id',
            'ph': 'https://auth.lazada.ph',
        }

        auth_base = country_urls.get(country, self.AUTH_URL)
        return f"{auth_base}/authorize?{urlencode(params)}"

    async def get_access_token(self, code: str) -> Dict[str, Any]:
        """
        使用授权码换取访问令牌

        Args:
            code: 授权后获得的 code

        Returns:
            包含 access_token, refresh_token, expires_in 等的字典
        """
        params = {
            'app_key': self.app_key,
            'app_secret': self.app_secret,
            'code': code,
            'grant_type': 'authorization_code',
        }

        response = await self.client.post(
            f"{self.AUTH_URL}/token",
            data=params
        )
        response.raise_for_status()

        data = response.json()

        if 'access_token' not in data:
            raise Exception(f"获取 access_token 失败: {data}")

        return data

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的访问令牌信息
        """
        params = {
            'app_key': self.app_key,
            'app_secret': self.app_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }

        response = await self.client.post(
            f"{self.AUTH_URL}/token",
            data=params
        )
        response.raise_for_status()

        data = response.json()

        if 'access_token' not in data:
            raise Exception(f"刷新 access_token 失败: {data}")

        return data


# ==================== 测试代码 ====================

async def test_lazada_api():
    """测试 Lazada API 客户端（需要有效的凭证）"""
    # TODO: 替换为实际的凭证
    config = LazadaConfig(
        app_key="YOUR_APP_KEY",
        app_secret="YOUR_APP_SECRET",
        country="th",
        access_token="YOUR_ACCESS_TOKEN"  # 从 OAuth 获取
    )

    client = LazadaAPIClient(config)

    try:
        # 测试获取商品列表
        products = await client.get_products(limit=10)
        print(f"获取到 {len(products)} 个商品")

        for product in products[:3]:
            print(f"- {product.title} ({product.price})")

    finally:
        await client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # asyncio.run(test_lazada_api())
