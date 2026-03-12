# crawler/products
"""产品数据爬虫模块"""

from .shopee_trending import ShopeeTrendingCrawler
from .lazada_api import LazadaAPIClient, LazadaOAuthClient, LazadaConfig, LazadaProduct

# Optional import for Amazon crawler (when implemented)
try:
    from .amazon_bestsellers import AmazonBestSellersCrawler
    __all__ = ['ShopeeTrendingCrawler', 'AmazonBestSellersCrawler', 'LazadaAPIClient', 'LazadaOAuthClient', 'LazadaConfig', 'LazadaProduct']
except ImportError:
    __all__ = ['ShopeeTrendingCrawler', 'LazadaAPIClient', 'LazadaOAuthClient', 'LazadaConfig', 'LazadaProduct']
