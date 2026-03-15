# services/cpi_calculator.py
"""CPI (Competition-Potential-Intelligence) 评分计算模块

CPI 评分体系：
- C (Competition) 竞争度: 40%
  - 多平台价格离散度: 15%
  - 卖家密度: 15%
  - 评论增长趋势: 10%

- P (Potential) 潜力: 40%
  - Google Trends 增长: 20%
  - 区域市场对比: 20%

- I (Intelligence) 智能洞察: 20%
  - AI 综合建议

设计原则：
1. 多平台数据优先（Amazon + Lazada + Shopee）
2. 单平台时使用降级策略
3. 数据不足时标注置信度
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CPIResult:
    """CPI 计算结果"""
    c_score: float  # 竞争度分数 (0-100)
    p_score: float  # 潜力分数 (0-100)
    i_score: float  # 智能洞察分数 (0-100)
    total_score: float  # 加权总分 (0-100)

    # 置信度
    confidence: float  # 0-1, 基于数据完整性
    data_quality: str  # high, medium, low

    # 详细分析
    details: Dict[str, Any]

    # 建议
    recommendation: str
    risk_level: str  # low, medium, high

    def to_dict(self) -> Dict[str, Any]:
        return {
            "c_score": round(self.c_score, 1),
            "p_score": round(self.p_score, 1),
            "i_score": round(self.i_score, 1),
            "total_score": round(self.total_score, 1),
            "confidence": round(self.confidence, 2),
            "data_quality": self.data_quality,
            "details": self.details,
            "recommendation": self.recommendation,
            "risk_level": self.risk_level,
        }


class CPICalculator:
    """CPI 评分计算器"""

    # 权重配置
    WEIGHTS = {
        "competition": 0.40,
        "potential": 0.40,
        "intelligence": 0.20,
    }

    # 子权重
    SUB_WEIGHTS = {
        "competition": {
            "price_dispersion": 0.375,  # 15/40
            "seller_density": 0.375,    # 15/40
            "review_growth": 0.25,      # 10/40
        },
        "potential": {
            "google_trends": 0.50,      # 20/40
            "regional_comparison": 0.50, # 20/40
        },
    }

    def __init__(self):
        pass

    def calculate(
        self,
        multi_platform_data: Optional[Dict[str, Any]] = None,
        amazon_data: Optional[Dict[str, Any]] = None,
        google_trends_data: Optional[Dict[str, Any]] = None,
        article_insights: Optional[List[Dict[str, Any]]] = None,
    ) -> CPIResult:
        """
        计算 CPI 分数

        Args:
            multi_platform_data: 多平台聚合数据
            amazon_data: Amazon 单平台数据 (兼容)
            google_trends_data: Google Trends 数据
            article_insights: 相关文章洞察

        Returns:
            CPIResult: CPI 计算结果
        """
        # 确定数据源
        data_source = multi_platform_data or amazon_data or {}

        # 计算各维度分数
        c_score, c_details, c_confidence = self._calculate_competition(
            data_source, multi_platform_data is not None
        )
        p_score, p_details, p_confidence = self._calculate_potential(
            data_source, google_trends_data
        )
        i_score, i_details, i_confidence = self._calculate_intelligence(
            c_score, p_score, article_insights
        )

        # 加权总分
        total_score = (
            c_score * self.WEIGHTS["competition"] +
            p_score * self.WEIGHTS["potential"] +
            i_score * self.WEIGHTS["intelligence"]
        )

        # 计算整体置信度
        overall_confidence = (c_confidence + p_confidence + i_confidence) / 3

        # 确定数据质量
        if overall_confidence >= 0.8:
            data_quality = "high"
        elif overall_confidence >= 0.5:
            data_quality = "medium"
        else:
            data_quality = "low"

        # 生成建议
        recommendation = self._generate_recommendation(
            c_score, p_score, i_score, data_quality
        )

        # 风险等级
        risk_level = self._assess_risk(c_score, p_score, overall_confidence)

        return CPIResult(
            c_score=c_score,
            p_score=p_score,
            i_score=i_score,
            total_score=total_score,
            confidence=overall_confidence,
            data_quality=data_quality,
            details={
                "competition": c_details,
                "potential": p_details,
                "intelligence": i_details,
                "is_multi_platform": multi_platform_data is not None,
            },
            recommendation=recommendation,
            risk_level=risk_level,
        )

    def _calculate_competition(
        self,
        data: Dict[str, Any],
        is_multi_platform: bool
    ) -> tuple[float, Dict[str, Any], float]:
        """计算竞争度分数 (C)"""
        details = {}
        confidence = 0.5

        # 1. 价格离散度 (价格范围越宽，竞争越激烈)
        price = data.get("price", data.get("market_data", {}).get("price", {}))
        price_min = price.get("min", 0)
        price_max = price.get("max", 0)
        price_avg = price.get("avg", price.get("median", 0))

        if price_avg > 0 and price_max > price_min:
            price_dispersion = (price_max - price_min) / price_avg
            # 离散度 0-1 映射到分数 100-0 (离散度越高分数越低)
            price_score = max(0, 100 - price_dispersion * 100)
            details["price_dispersion"] = round(price_dispersion, 2)
            details["price_score"] = round(price_score, 1)
            confidence += 0.1
        else:
            price_score = 50  # 无数据时使用中值
            details["price_score"] = "N/A"

        # 2. 卖家密度
        competition = data.get("competition", {})
        total_sellers = competition.get("total_sellers", 0)
        total_products = data.get("total_products", 1) or 1

        if total_sellers > 0:
            seller_density = total_sellers / total_products
            # 密度 0-10 映射到分数 100-0
            seller_score = max(0, 100 - seller_density * 10)
            details["seller_density"] = round(seller_density, 2)
            details["seller_score"] = round(seller_score, 1)
            confidence += 0.1
        else:
            seller_score = 50
            details["seller_score"] = "N/A"

        # 3. 评论增长趋势 (需要历史数据，暂时使用评分作为代理)
        rating = data.get("rating", {})
        avg_rating = rating.get("avg", rating.get("weighted_avg", 0))
        review_count = rating.get("count", 0)

        if review_count > 0:
            # 评论数越多，市场越成熟，竞争越激烈
            # 但评论数也代表市场需求
            review_score = min(100, review_count / 10)  # 简化计算
            details["review_count"] = review_count
            details["review_score"] = round(review_score, 1)
            confidence += 0.1
        else:
            review_score = 50
            details["review_score"] = "N/A"

        # 多平台加权
        if is_multi_platform:
            confidence += 0.2
            details["multi_platform_bonus"] = True

        # 加权平均
        c_score = (
            price_score * self.SUB_WEIGHTS["competition"]["price_dispersion"] +
            seller_score * self.SUB_WEIGHTS["competition"]["seller_density"] +
            review_score * self.SUB_WEIGHTS["competition"]["review_growth"]
        )

        details["weighted_score"] = round(c_score, 1)

        return c_score, details, min(confidence, 1.0)

    def _calculate_potential(
        self,
        data: Dict[str, Any],
        google_trends: Optional[Dict[str, Any]]
    ) -> tuple[float, Dict[str, Any], float]:
        """计算潜力分数 (P)"""
        details = {}
        confidence = 0.3

        # 1. Google Trends 分数
        if google_trends:
            trends_score = google_trends.get("score", 50)
            growth_rate = google_trends.get("growth_rate", 0)

            # 增长率调整
            if growth_rate > 0:
                trends_score = min(100, trends_score + growth_rate * 10)

            details["google_trends_score"] = trends_score
            details["growth_rate"] = growth_rate
            confidence += 0.3
        else:
            # 从数据中获取趋势分数
            trend = data.get("trend", {})
            trends_score = trend.get("avg_google_trends_score", 50) or 50
            details["google_trends_score"] = trends_score
            confidence += 0.1

        # 2. 区域市场对比
        platforms = data.get("platforms", [])
        if len(platforms) > 1:
            # 多区域覆盖，潜力更高
            regional_score = min(100, 50 + len(platforms) * 10)
            details["regions_covered"] = len(platforms)
            details["regional_score"] = regional_score
            confidence += 0.3
        else:
            regional_score = 50
            details["regional_score"] = "single_region"

        # 加权平均
        p_score = (
            trends_score * self.SUB_WEIGHTS["potential"]["google_trends"] +
            regional_score * self.SUB_WEIGHTS["potential"]["regional_comparison"]
        )

        details["weighted_score"] = round(p_score, 1)

        return p_score, details, min(confidence, 1.0)

    def _calculate_intelligence(
        self,
        c_score: float,
        p_score: float,
        article_insights: Optional[List[Dict[str, Any]]]
    ) -> tuple[float, Dict[str, Any], float]:
        """计算智能洞察分数 (I)"""
        details = {}
        confidence = 0.5

        # 基础分数：C 和 P 的组合
        base_score = (c_score + p_score) / 2

        # 文章洞察加成
        if article_insights and len(article_insights) > 0:
            # 有相关文章，增加洞察分数
            insight_bonus = min(20, len(article_insights) * 5)
            i_score = min(100, base_score + insight_bonus)
            details["articles_analyzed"] = len(article_insights)
            details["insight_bonus"] = insight_bonus
            confidence += 0.3
        else:
            i_score = base_score
            details["articles_analyzed"] = 0

        details["base_score"] = round(base_score, 1)
        details["final_score"] = round(i_score, 1)

        return i_score, details, min(confidence, 1.0)

    def _generate_recommendation(
        self,
        c_score: float,
        p_score: float,
        i_score: float,
        data_quality: str
    ) -> str:
        """生成建议"""
        if data_quality == "low":
            return "数据不足，建议收集更多信息后再做决策"

        if c_score >= 70 and p_score >= 70:
            return "竞争适中，潜力较高，建议优先关注"
        elif c_score >= 70 and p_score < 50:
            return "市场成熟但增长有限，适合稳健型卖家"
        elif c_score < 50 and p_score >= 70:
            return "蓝海市场，潜力大但需验证需求"
        elif c_score < 50 and p_score < 50:
            return "竞争激烈且增长放缓，谨慎进入"
        else:
            return "建议进一步分析具体品类和价格区间"

    def _assess_risk(
        self,
        c_score: float,
        p_score: float,
        confidence: float
    ) -> str:
        """评估风险等级"""
        if confidence < 0.5:
            return "high"  # 数据不足，高风险

        if c_score < 40:  # 竞争激烈
            return "high"
        elif c_score < 60:
            return "medium"
        else:
            return "low"


# 便捷函数
def calculate_cpi(
    multi_platform_data: Optional[Dict[str, Any]] = None,
    amazon_data: Optional[Dict[str, Any]] = None,
    google_trends_data: Optional[Dict[str, Any]] = None,
    article_insights: Optional[List[Dict[str, Any]]] = None,
) -> CPIResult:
    """计算 CPI 分数的便捷函数"""
    calculator = CPICalculator()
    return calculator.calculate(
        multi_platform_data=multi_platform_data,
        amazon_data=amazon_data,
        google_trends_data=google_trends_data,
        article_insights=article_insights,
    )
