# crawler/reviews
"""评论爬虫模块"""

from .amazon_reviews import AmazonReviewCrawler
from .shopee_reviews import ShopeeReviewCrawler

__all__ = ['AmazonReviewCrawler', 'ShopeeReviewCrawler']
