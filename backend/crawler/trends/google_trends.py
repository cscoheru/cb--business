# crawler/trends/google_trends.py
"""Google Trends 数据获取器"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class TrendTopic:
    """趋势主题"""
    title: str
    volume: int  # 搜索量 0-100
    traffic: int  # 流量增长百分比
    related_queries: List[str]
    timestamp: datetime

    # 国家和分类
    country: str = "US"
    category: int = 0  # 0 = 所有分类

    # AI 分析结果
    sentiment: Optional[str] = None  # positive/neutral/negative
    opportunity_score: Optional[float] = None  # 0-100
    suggestions: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d


class GoogleTrendsClient:
    """Google Trends 非官方 API 客户端"""

    # Google Trends API 端点
    API_BASE = "https://trends.google.com/trends/api"

    # 支持的国家代码
    COUNTRY_CODES = {
        "us": "US",
        "th": "TH",
        "vn": "VN",
        "my": "MY",
        "sg": "SG",
        "id": "ID",
        "ph": "PH",
        "br": "BR",
        "mx": "MX",
    }

    # 分类代码
    CATEGORY_CODES = {
        "all": 0,
        "shopping": 244,  # 购物
        "electronics": 3,  # 电子产品
        "fashion": 8,  # 时尚
        "home": 11,  # 家居
        "beauty": 44,  # 美容
        "toys": 21,  # 玩具
        "sports": 24,  # 体育
    }

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def get_realtime_trends(
        self,
        country: str = "us",
        category: str = "all",
        max_results: int = 20
    ) -> List[TrendTopic]:
        """
        获取实时搜索趋势

        Args:
            country: 国家代码 (us, th, vn, my, sg, id, ph)
            category: 分类 (all, shopping, electronics, fashion, etc.)
            max_results: 最大结果数

        Returns:
            趋势主题列表
        """
        country_code = self.COUNTRY_CODES.get(country, "US")
        category_code = self.CATEGORY_CODES.get(category, 0)

        url = f"{self.API_BASE}/trendingsearches/daily"

        params = {
            "hl": "en-US",
            "tz": -60,  # 时区
            "req": {"geo": country_code, "category": category_code},
            "ajax": 1,
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            # Google Trends 返回 JSON 前有多余的字符
            content = response.text
            if content.startswith(")]}'"):
                content = content[5:]

            import json
            data = json.loads(content)

            topics = []

            if "default" in data and "rankedList" in data["default"]:
                for ranked_list in data["default"]["rankedList"][:1]:  # 只取第一个列表
                    for item in ranked_list["rankedKeyword"][:max_results]:
                        topic = TrendTopic(
                            title=item.get("query", ""),
                            volume=int(item.get("formattedValue", "0").replace("+", "").replace(",", "").replace("K", "00").replace("M", "000000")),
                            traffic=int(item.get("formattedTraffic", "0").replace("+", "").replace("%", "")),
                            related_queries=item.get("relatedQueries", [])[:5],
                            timestamp=datetime.now(),
                            country=country.upper(),
                            category_code,
                        )
                        topics.append(topic)

            logger.info(f"从 Google Trends 获取到 {len(topics)} 个趋势")
            return topics

        except Exception as e:
            logger.error(f"获取 Google Trends 失败: {e}")
            return []

    async def get_related_topics(
        self,
        keyword: str,
        country: str = "us"
    ) -> Dict[str, Any]:
        """
        获取关键词的相关主题

        Args:
            keyword: 关键词
            country: 国家代码

        Returns:
            相关主题数据
        """
        country_code = self.COUNTRY_CODES.get(country, "US")

        # 使用 pytrends 风格的请求
        url = f"{self.API_BASE}/explore"

        params = {
            "hl": "en-US",
            "tz": -60,
            "req": {
                "comparisonItem": [{"keyword": keyword, "geo": country_code, "time": "now 7-d"}],
                "category": 0,
                "property": "",
            },
            "ajax": 1,
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            content = response.text
            if content.startswith(")]}'"):
                content = content[5:]

            import json
            data = json.loads(content)

            return data

        except Exception as e:
            logger.error(f"获取相关主题失败 ({keyword}): {e}")
            return {}

    async def get_interest_over_time(
        self,
        keyword: str,
        country: str = "us",
        timeframe: str = "today 7-d"  # today 7-d, today 1-m, today 3-m, today 12-m
    ) -> Dict[str, Any]:
        """
        获取关键词的搜索兴趣随时间变化

        Args:
            keyword: 关键词
            country: 国家代码
            timeframe: 时间范围

        Returns:
            时间序列数据
        """
        # 使用 pytrends 风格的多参数请求
        url = f"{self.API_BASE}/multirange"

        country_code = self.COUNTRY_CODES.get(country, "US")

        params = {
            "hl": "en-US",
            "tz": -60,
            "req": {
                "comparisonItem": [{"keyword": keyword, "geo": country_code, "time": timeframe}],
                "category": 0,
                "property": "",
            },
            "ajax": 1,
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            content = response.text
            if content.startswith(")]}'"):
                content = content[5:]

            import json
            data = json.loads(content)

            return data

        except Exception as e:
            logger.error(f"获取兴趣趋势失败 ({keyword}): {e}")
            return {}


# ==================== AI 趋势分析器 ====================

class AITrendAnalyzer:
    """AI 驱动的趋势分析器"""

    def __init__(self):
        self.client = None  # 可以集成 OpenAI 或智谱 AI

    async def analyze_topic(self, topic: TrendTopic) -> TrendTopic:
        """
        分析趋势主题的商机价值

        Args:
            topic: 趋势主题

        Returns:
            包含 AI 分析结果的主题
        """
        # 这里可以调用真实的 AI API
        # 目前使用简单的规则分析

        # 1. 计算机会评分
        opportunity_score = self._calculate_opportunity_score(topic)

        # 2. 判断情感倾向
        sentiment = self._analyze_sentiment(topic.title)

        # 3. 生成建议
        suggestions = self._generate_suggestions(topic)

        # 更新主题
        topic.opportunity_score = opportunity_score
        topic.sentiment = sentiment
        topic.suggestions = suggestions

        return topic

    def _calculate_opportunity_score(self, topic: TrendTopic) -> float:
        """
        计算机会评分 (0-100)

        考虑因素:
        - 搜索量 (volume)
        - 流量增长 (traffic)
        - 关键词特征
        """
        # 基础分数
        base_score = min(topic.volume, 50)  # 搜索量最多贡献 50 分

        # 增长分数
        growth_score = min(topic.traffic * 2, 30)  # 流量增长最多贡献 30 分

        # 关键词特征加分
        keyword_bonus = 0
        title_lower = topic.title.lower()

        # 产品相关关键词
        product_keywords = ["buy", "cheap", "best", "review", "price", "sale", "discount"]
        if any(kw in title_lower for kw in product_keywords):
            keyword_bonus += 10

        # 电子产品
        tech_keywords = ["phone", "tablet", "laptop", "watch", "camera", "headphone"]
        if any(kw in title_lower for kw in tech_keywords):
            keyword_bonus += 5

        # 总分
        total = base_score + growth_score + keyword_bonus
        return min(total, 100)

    def _analyze_sentiment(self, title: str) -> str:
        """
        分析情感倾向

        基于关键词的简单规则
        """
        positive_keywords = ["best", "top", "good", "great", "amazing", "excellent"]
        negative_keywords = ["bad", "worst", "terrible", "scam", "fake", "broken"]

        title_lower = title.lower()

        if any(kw in title_lower for kw in positive_keywords):
            return "positive"
        elif any(kw in title_lower for kw in negative_keywords):
            return "negative"
        else:
            return "neutral"

    def _generate_suggestions(self, topic: TrendTopic) -> List[str]:
        """生成商机建议"""
        suggestions = []
        title_lower = topic.title.lower()

        # 根据标题内容生成建议
        if "iphone" in title_lower or "samsung" in title_lower:
            suggestions.append("考虑手机配件市场")
            suggestions.append("关注相关手机壳、充电器等产品")

        if "sale" in title_lower or "discount" in title_lower:
            suggestions.append("把握促销时机进行选品")
            suggestions.append("关注季节性产品机会")

        if topic.opportunity_score and topic.opportunity_score > 70:
            suggestions.append("🔥 高机会趋势，建议深入研究")
            suggestions.append("可以考虑快速跟进")

        if topic.traffic > 100:
            suggestions.append("📈 搜索量快速增长中")

        return suggestions

    async def analyze_batch(self, topics: List[TrendTopic]) -> List[TrendTopic]:
        """批量分析趋势主题"""
        results = []
        for topic in topics:
            analyzed = await self.analyze_topic(topic)
            results.append(analyzed)
        return results

    async def discover_product_opportunities(
        self,
        country: str = "us",
        category: str = "all",
        min_score: float = 60
    ) -> List[Dict[str, Any]]:
        """
        发现产品机会

        综合流程:
        1. 获取实时趋势
        2. AI 分析每个趋势
        3. 筛选高机会项目
        4. 生成推荐报告
        """
        trends_client = GoogleTrendsClient()

        try:
            # 1. 获取趋势
            topics = await trends_client.get_realtime_trends(
                country=country,
                category=category,
                max_results=50
            )

            # 2. AI 分析
            analyzed_topics = await self.analyze_batch(topics)

            # 3. 筛选高机会项目
            opportunities = [
                t for t in analyzed_topics
                if t.opportunity_score and t.opportunity_score >= min_score
            ]

            # 4. 排序
            opportunities.sort(key=lambda x: x.opportunity_score or 0, reverse=True)

            # 5. 生成报告
            report = {
                "country": country.upper(),
                "category": category,
                "generated_at": datetime.now().isoformat(),
                "total_trends_analyzed": len(topics),
                "high_opportunity_count": len(opportunities),
                "opportunities": [t.to_dict() for t in opportunities[:20]],
            }

            return report

        finally:
            await trends_client.close()


# ==================== 测试代码 ====================

async def test_google_trends():
    """测试 Google Trends 获取器"""
    analyzer = AITrendAnalyzer()

    try:
        report = await analyzer.discover_product_opportunities(
            country="us",
            category="shopping",
            min_score=50
        )

        print(f"\n=== 产品机会分析报告 ===")
        print(f"国家: {report['country']}")
        print(f"分析趋势总数: {report['total_trends_analyzed']}")
        print(f"高机会项目: {report['high_opportunity_count']}")
        print(f"\n前10个机会:")

        for i, opp in enumerate(report['opportunities'][:10], 1):
            print(f"\n{i}. {opp['title']}")
            print(f"   机会评分: {opp['opportunity_score']:.1f}/100")
            print(f"   搜索量: {opp['volume']}")
            print(f"   流量增长: +{opp['traffic']}%")
            if opp['suggestions']:
                print(f"   建议:")
                for s in opp['suggestions']:
                    print(f"     - {s}")

    finally:
        pass


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(test_google_trends())
