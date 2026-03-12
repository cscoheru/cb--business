# crawler/products
"""产品数据爬虫模块"""

from .shopee_trending import ShopeeTrendingCrawler
from .amazon_bestsellers import AmazonBestSellersCrawler

__all__ = ['ShopeeTrendingCrawler', 'AmazonBestSellersCrawler']
