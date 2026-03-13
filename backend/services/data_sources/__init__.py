# services/data_sources/__init__.py
"""数据源适配器包"""

from .oxylabs_source import OxylabsDataSource
from .google_trends_source import GoogleTrendsDataSource

__all__ = [
    "OxylabsDataSource",
    "GoogleTrendsDataSource"
]
