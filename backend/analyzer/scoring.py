# analyzer/scoring.py
"""AI 产品机会评分引擎"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class OpportunityScore:
    """机会评分结果"""
    total_score: float  # 总分 0-100
    demand_score: float  # 需求分数
    competition_score: float  # 竞争分数
    profitability_score: float  # 利润分数
    trend_score: float  # 趋势分数
    quality_score: float  # 质量分数

    # 详细分析
    insights: List[str]
    recommendations: List[str]
    risk_factors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_score": round(self.total_score, 1),
            "demand_score": round(self.demand_score, 1),
            "competition_score": round(self.competition_score, 1),
            "profitability_score": round(self.profitability_score, 1),
            "trend_score": round(self.trend_score, 1),
            "quality_score": round(self.quality_score, 1),
            "insights": self.insights,
            "recommendations": self.recommendations,
            "risk_factors": self.risk_factors,
        }


class OpportunityScoringEngine:
    """
    产品机会评分引擎

    评分逻辑:
    - 需求分数 (25%): 搜索量、搜索趋势
    - 竞争分数 (20%): Best Seller 排名、评论数
    - 利润分数 (20%): 价格区间、折扣
    - 趋势分数 (20%): 流量增长
    - 质量分数 (15%): 产品评分、Prime 标识
    """

    # 评分权重
    WEIGHTS = {
        "demand": 0.25,
        "competition": 0.20,
        "profitability": 0.20,
        "trend": 0.20,
        "quality": 0.15,
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def score_amazon_product(
        self,
        product_data: Dict[str, Any],
        trends_data: Optional[Dict[str, Any]] = None
    ) -> OpportunityScore:
        """
        对 Amazon 产品进行机会评分

        Args:
            product_data: Amazon 产品数据
            trends_data: Google Trends 数据 (可选)

        Returns:
            机会评分结果
        """
        # 1. 需求分数
        demand_score = self._calculate_demand_score(product_data, trends_data)

        # 2. 竞争分数
        competition_score = self._calculate_competition_score(product_data)

        # 3. 利润分数
        profitability_score = self._calculate_profitability_score(product_data)

        # 4. 趋势分数
        trend_score = self._calculate_trend_score(product_data, trends_data)

        # 5. 质量分数
        quality_score = self._calculate_quality_score(product_data)

        # 计算总分
        total_score = (
            demand_score * self.WEIGHTS["demand"] +
            competition_score * self.WEIGHTS["competition"] +
            profitability_score * self.WEIGHTS["profitability"] +
            trend_score * self.WEIGHTS["trend"] +
            quality_score * self.WEIGHTS["quality"]
        )

        # 生成洞察和建议
        insights, recommendations, risk_factors = self._generate_analysis(
            product_data,
            {
                "demand": demand_score,
                "competition": competition_score,
                "profitability": profitability_score,
                "trend": trend_score,
                "quality": quality_score,
            }
        )

        return OpportunityScore(
            total_score=total_score,
            demand_score=demand_score,
            competition_score=competition_score,
            profitability_score=profitability_score,
            trend_score=trend_score,
            quality_score=quality_score,
            insights=insights,
            recommendations=recommendations,
            risk_factors=risk_factors,
        )

    def score_trend_topic(
        self,
        trend_data: Dict[str, Any]
    ) -> OpportunityScore:
        """
        对 Google 趋势主题进行机会评分

        Args:
            trend_data: Google Trends 数据

        Returns:
            机会评分结果
        """
        # 趋势数据主要提供需求信号
        demand_score = min(trend_data.get("volume", 0) * 2, 100)
        trend_score = min(trend_data.get("traffic", 0) * 2, 100)

        # 其他维度基于趋势信息估算
        competition_score = 50  # 中等竞争
        profitability_score = 50  # 未知利润率
        quality_score = 50  # 未知质量

        total_score = (
            demand_score * self.WEIGHTS["demand"] +
            competition_score * self.WEIGHTS["competition"] +
            profitability_score * self.WEIGHTS["profitability"] +
            trend_score * self.WEIGHTS["trend"] +
            quality_score * self.WEIGHTS["quality"]
        )

        # 生成分析
        insights = [
            f"搜索量: {trend_data.get('volume', 0)}",
            f"流量增长: +{trend_data.get('traffic', 0)}%",
        ]

        recommendations = []
        if total_score > 70:
            recommendations.append("🔥 高潜力趋势，建议深入研究")
        if trend_data.get("traffic", 0) > 100:
            recommendations.append("📈 搜索量快速增长中")

        return OpportunityScore(
            total_score=total_score,
            demand_score=demand_score,
            competition_score=competition_score,
            profitability_score=profitability_score,
            trend_score=trend_score,
            quality_score=quality_score,
            insights=insights,
            recommendations=recommendations,
            risk_factors=[],
        )

    def _calculate_demand_score(
        self,
        product_data: Dict[str, Any],
        trends_data: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        计算需求分数 (0-100)

        因素:
        - 销量 (sold_count)
        - 评论数 (reviews_count)
        - Best Seller 排名 (rank)
        - Google Trends 搜索量
        """
        score = 50  # 基础分

        # 销量加分 (最多 30 分)
        sold_count = product_data.get("sold_count", 0)
        if sold_count > 0:
            score += min(sold_count / 100, 30)

        # 评论数加分 (最多 20 分)
        reviews_count = product_data.get("reviews_count", 0)
        if reviews_count > 0:
            score += min(reviews_count / 50, 20)

        # Best Seller 排名加分 (最多 30 分)
        rank = product_data.get("rank", 0)
        if rank > 0 and rank <= 100:
            score += 30 * (1 - rank / 100)

        # Google Trends 数据
        if trends_data:
            volume = trends_data.get("volume", 0)
            if volume > 50:
                score += min(volume / 5, 20)

        return min(score, 100)

    def _calculate_competition_score(
        self,
        product_data: Dict[str, Any]
    ) -> float:
        """
        计算竞争分数 (0-100)

        分数越高表示竞争越小（机会越大）

        因素:
        - Best Seller 排名 (排名越靠前，竞争越激烈)
        - 评论数 (评论越多，竞争越激烈)
        """
        score = 100  # 从满分开始

        # Best Seller 排名扣分
        rank = product_data.get("rank", 0)
        if rank > 0:
            # 前 10 名竞争最激烈
            if rank <= 10:
                score -= 50
            elif rank <= 50:
                score -= 30
            elif rank <= 100:
                score -= 10

        # 评论数扣分
        reviews_count = product_data.get("reviews_count", 0)
        if reviews_count > 10000:
            score -= 30
        elif reviews_count > 5000:
            score -= 20
        elif reviews_count > 1000:
            score -= 10

        return max(score, 0)

    def _calculate_profitability_score(
        self,
        product_data: Dict[str, Any]
    ) -> float:
        """
        计算利润分数 (0-100)

        因素:
        - 价格区间
        - 折扣幅度
        """
        score = 50  # 基础分

        price = product_data.get("price", 0)
        original_price = product_data.get("original_price")

        # 价格区间加分
        if 20 <= price <= 100:
            score += 20  # 最佳价格区间
        elif 100 < price <= 200:
            score += 10
        elif price > 200:
            score += 5

        # 折扣加分
        if original_price and original_price > price:
            discount = (original_price - price) / original_price
            score += min(discount * 100, 30)

        return min(score, 100)

    def _calculate_trend_score(
        self,
        product_data: Dict[str, Any],
        trends_data: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        计算趋势分数 (0-100)

        因素:
        - Google Trends 流量增长
        - 销量趋势
        """
        score = 50  # 基础分

        # Google Trends 流量增长
        if trends_data:
            traffic = trends_data.get("traffic", 0)
            score += min(traffic / 2, 50)

        return min(score, 100)

    def _calculate_quality_score(
        self,
        product_data: Dict[str, Any]
    ) -> float:
        """
        计算质量分数 (0-100)

        因素:
        - 产品评分
        - Prime 标识
        - Amazon's Choice 标识
        """
        score = 50  # 基础分

        # 评分加分
        rating = product_data.get("rating")
        if rating:
            if rating >= 4.5:
                score += 30
            elif rating >= 4.0:
                score += 20
            elif rating >= 3.5:
                score += 10

        # Prime 加分
        if product_data.get("is_prime"):
            score += 15

        # Amazon's Choice 加分
        if product_data.get("is_amazon_choice"):
            score += 20

        return min(score, 100)

    def _generate_analysis(
        self,
        product_data: Dict[str, Any],
        scores: Dict[str, float]
    ) -> tuple[List[str], List[str], List[str]]:
        """生成洞察、建议和风险因素"""
        insights = []
        recommendations = []
        risk_factors = []

        # 标题
        title = product_data.get("title", "")
        if title:
            insights.append(f"产品: {title[:60]}...")

        # 价格
        price = product_data.get("price", 0)
        if price > 0:
            insights.append(f"价格: ${price:.2f}")

        # 评分
        rating = product_data.get("rating")
        if rating:
            insights.append(f"评分: {rating}/5")

        # 排名
        rank = product_data.get("rank", 0)
        if rank > 0:
            insights.append(f"Best Seller 排名: #{rank}")

        # 基于分数生成建议
        if scores["demand"] > 70:
            recommendations.append("🔥 市场需求强烈")

        if scores["competition"] < 40:
            risk_factors.append("⚠️ 竞争激烈，需差异化")
        elif scores["competition"] > 70:
            recommendations.append("✅ 竞争较小，有利可图")

        if scores["profitability"] > 70:
            recommendations.append("💰 价格区间良好，利润空间大")

        if scores["trend"] > 70:
            recommendations.append("📈 呈上升趋势，值得关注")

        if scores["quality"] > 80:
            recommendations.append("⭐ 产品质量高，用户满意度好")

        if rating and rating < 3.5:
            risk_factors.append("⚠️ 评分较低，需注意产品质量")

        if rank > 0 and rank <= 10:
            risk_factors.append("⚠️ 排名太靠前，竞争激烈")

        return insights, recommendations, risk_factors

    def batch_score_products(
        self,
        products: List[Dict[str, Any]],
        trends_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量评分产品

        Args:
            products: 产品列表
            trends_data: 趋势数据 (可选)

        Returns:
            评分结果列表，按分数降序排列
        """
        results = []

        for product in products:
            try:
                score_result = self.score_amazon_product(product, trends_data)

                result = {
                    **product,
                    "opportunity_score": score_result.to_dict(),
                }
                results.append(result)

            except Exception as e:
                logger.error(f"评分失败: {e}")
                continue

        # 按分数排序
        results.sort(key=lambda x: x["opportunity_score"]["total_score"], reverse=True)

        return results


# ==================== API 集成示例 ====================

async def analyze_product_opportunity(
    product_data: Dict[str, Any],
    trends_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    分析产品机会

    这是一个便捷函数，供 API 调用
    """
    engine = OpportunityScoringEngine()
    score_result = engine.score_amazon_product(product_data, trends_data)

    return {
        "product_title": product_data.get("title", ""),
        "asin": product_data.get("asin"),
        "score": score_result.to_dict(),
        "analyzed_at": datetime.now().isoformat(),
    }
