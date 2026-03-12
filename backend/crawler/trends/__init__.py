# crawler/trends
"""趋势分析模块"""

from .google_trends import (
    GoogleTrendsClient,
    AITrendAnalyzer,
    TrendTopic,
)

__all__ = [
    'GoogleTrendsClient',
    'AITrendAnalyzer',
    'TrendTopic',
]
