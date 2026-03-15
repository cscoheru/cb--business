# services/opportunity_algorithm.py
"""C-P-I 跨境商机矩阵算法系统

商机综合分 (Score) = 0.4×竞争度(C) + 0.4×增长潜力(P) + 0.2×信息差(I)

数据来源:
- C (Competition): OpenClaw抓取类目头部品牌分布、CPC出价
- P (Potential): OpenClaw监控社交媒体声量、搜索趋势
- I (Intelligence Gap): AI分析评论情感，计算痛点集中度
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from config.database import AsyncSessionLocal
from models.card import Card
from models.article import Article
from models.business_opportunity import BusinessOpportunity, OpportunityStatus, OpportunityType

logger = logging.getLogger(__name__)


class OpportunityScorer:
    """C-P-I 商机评分器"""

    # 权重配置
    WEIGHTS = {
        'competition': 0.4,  # w1
        'potential': 0.4,    # w2
        'intelligence_gap': 0.2  # w3
    }

    # 评分阈值
    THRESHOLDS = {
        'high': 80,      # 高价值商机
        'medium': 60,    # 中等价值商机
        'low': 40        # 低价值商机
    }

    async def calculate_opportunity_score(
        self,
        card: Card,
        db: AsyncSession,
        enable_mcp: bool = True
    ) -> Dict[str, Any]:
        """
        为单个 Card 计算商机综合分

        Args:
            card: 商机卡片
            db: 数据库会话
            enable_mcp: 是否启用MCP增强（默认True）

        Returns:
            {
                'total_score': 85.5,  # 综合分数
                'competition': {'score': 70, 'details': {...}},
                'potential': {'score': 90, 'details': {...}},
                'intelligence_gap': {'score': 88, 'details': {...}},
                'opportunity_type': '长尾暴利型',  # 商机类型标签
                'mcp_enhanced': True  # 是否使用了MCP增强
            }
        """
        try:
            # 第一步: 初始评分
            initial_result = await self._calculate_base_score(card, db)

            # 第二步: 检查是否需要MCP增强
            if not enable_mcp:
                return initial_result

            needs_enhancement = self._check_if_needs_mcp_enhancement(initial_result)

            if not needs_enhancement:
                logger.info(f"Card {card.id} 数据完整，无需MCP增强")
                return {**initial_result, 'mcp_enhanced': False}

            # 第三步: MCP增强
            logger.info(f"Card {card.id} 数据置信度不足，触发MCP增强")
            enhanced_result = await self._enhance_with_mcp(card, initial_result, db)

            return {**enhanced_result, 'mcp_enhanced': True}

        except Exception as e:
            logger.error(f"计算商机分数失败: {e}")
            raise

    async def _calculate_base_score(
        self,
        card: Card,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """计算基础C-P-I分数（不使用MCP）"""
        # 并行计算三个维度
        competition_score, competition_details = await self._calculate_competition(card, db)
        potential_score, potential_details = await self._calculate_potential(card, db)
        intelligence_score, intelligence_details = await self._calculate_intelligence_gap(card, db)

        # 加权计算综合分
        total_score = (
            competition_score * self.WEIGHTS['competition'] +
            potential_score * self.WEIGHTS['potential'] +
            intelligence_score * self.WEIGHTS['intelligence_gap']
        )

        # 确定商机类型
        opportunity_type = self._classify_opportunity_type(
            competition_score,
            potential_score,
            intelligence_score
        )

        return {
            'total_score': round(total_score, 1),
            'competition': {
                'score': competition_score,
                'details': competition_details,
                'weight': self.WEIGHTS['competition']
            },
            'potential': {
                'score': potential_score,
                'details': potential_details,
                'weight': self.WEIGHTS['potential']
            },
            'intelligence_gap': {
                'score': intelligence_score,
                'details': intelligence_details,
                'weight': self.WEIGHTS['intelligence_gap']
            },
            'opportunity_type': opportunity_type,
            'calculated_at': datetime.now().isoformat()
        }

    def _check_if_needs_mcp_enhancement(self, score_result: Dict[str, Any]) -> bool:
        """
        检查是否需要MCP增强

        判断标准:
        1. 竞争度分数为中等值(50分)且包含estimated标记
        2. 增长潜力分数为中等值(50分)且文章数量少于20
        3. 信息差分数为中等值(50分)且使用fallback数据
        """
        comp_details = score_result['competition']['details']
        pot_details = score_result['potential']['details']
        intel_details = score_result['intelligence_gap']['details']

        # 检查竞争度
        comp_low_confidence = (
            score_result['competition']['score'] == 50.0 and
            comp_details.get('estimated') == True
        )

        # 检查增长潜力
        pot_low_confidence = (
            score_result['potential']['score'] == 50.0 and
            'error' in pot_details
        )

        # 检查信息差
        intel_low_confidence = (
            score_result['intelligence_gap']['score'] == 50.0 and
            intel_details.get('fallback') == True
        )

        return comp_low_confidence or pot_low_confidence or intel_low_confidence

    async def _enhance_with_mcp(
        self,
        card: Card,
        initial_result: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        使用MCP增强商机评分

        流程:
        1. 调用deep_market_scan获取更准确的竞争度数据
        2. 用新数据重新计算分数
        3. 合并结果
        """
        try:
            from config.mcp_client import call_openclaw_skill

            # 调用深度市场扫描
            mcp_result = await call_openclaw_skill(
                'deep_market_scan',
                {
                    'category': card.category,
                    'anomaly_detected': False,
                    'depth_level': 'standard'
                }
            )

            if not mcp_result.get('success'):
                logger.warning(f"MCP调用失败，使用初始分数: {mcp_result.get('error')}")
                return initial_result

            # 从MCP结果中提取增强数据
            enhanced_data = mcp_result.get('data', {})

            # 用MCP数据增强竞争度分数
            enhanced_competition = self._enhance_competition_with_mcp(
                initial_result['competition'],
                enhanced_data
            )

            # 重新计算总分
            new_total = (
                enhanced_competition['score'] * self.WEIGHTS['competition'] +
                initial_result['potential']['score'] * self.WEIGHTS['potential'] +
                initial_result['intelligence_gap']['score'] * self.WEIGHTS['intelligence_gap']
            )

            # 重新分类商机类型
            new_opportunity_type = self._classify_opportunity_type(
                enhanced_competition['score'],
                initial_result['potential']['score'],
                initial_result['intelligence_gap']['score']
            )

            return {
                'total_score': round(new_total, 1),
                'competition': enhanced_competition,
                'potential': initial_result['potential'],
                'intelligence_gap': initial_result['intelligence_gap'],
                'opportunity_type': new_opportunity_type,
                'calculated_at': datetime.now().isoformat(),
                'mcp_data': enhanced_data
            }

        except ImportError:
            logger.warning("MCP客户端未配置，使用初始分数")
            return initial_result
        except Exception as e:
            logger.error(f"MCP增强失败: {e}，使用初始分数")
            return initial_result

    def _enhance_competition_with_mcp(
        self,
        original_competition: Dict[str, Any],
        mcp_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用MCP数据增强竞争度评分"""
        # MCP返回的brand_concentration更准确
        brand_concentration = mcp_data.get('brand_concentration', 0.5)

        # 转换为竞争度分数：品牌集中度越高，竞争越激烈，分数越低
        enhanced_comp_score = max(0, 100 - (brand_concentration * 100))

        return {
            'score': round(enhanced_comp_score, 1),
            'details': {
                **original_competition['details'],
                'mcp_enhanced': True,
                'brand_concentration_mcp': round(brand_concentration * 100, 2),
                'sample_size_mcp': mcp_data.get('sample_size', 0),
                'price_range': mcp_data.get('price_range', {}),
                'new_product_count': mcp_data.get('new_product_count', 0)
            },
            'weight': original_competition['weight']
        }

    async def _calculate_competition(
        self,
        card: Card,
        db: AsyncSession
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算竞争度 (C) = Top10_Brand_Share × 0.7 + CPC_Bid_Estimate × 0.3

        数据来源: amazon_data 中的产品数据
        """
        try:
            amazon_products = card.amazon_data.get('products', []) if card.amazon_data else []

            if not amazon_products:
                # 无产品数据，返回中等竞争度（保守估计）
                return 50.0, {'reason': '无产品数据', 'estimated': True}

            # 计算Top10品牌份额（模拟）
            brand_counts = {}
            for product in amazon_products[:50]:  # 取前50个产品
                brand = product.get('brand', 'Unknown')
                brand_counts[brand] = brand_counts.get(brand, 0) + 1

            total_products = sum(brand_counts.values())
            if total_products == 0:
                return 50.0, {'reason': '无品牌数据', 'estimated': True}

            # 计算前10大品牌的市场份额
            sorted_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)
            top_10_share = sum(count for _, count in sorted_brands[:10]) / total_products if total_products > 0 else 0

            # Top10品牌份额越高，竞争越激烈，分数越低
            # 转换为0-100分，份额越大分数越低
            brand_competition_score = max(0, 100 - (top_10_share * 100))

            # CPC出价（模拟）
            # 假设CPC与类目竞争度正相关
            category_cpc = self._get_category_cpc(card.category)
            cpc_normalized = min(100, category_cpc / 2)  # 假设最高CPC为$2

            # 计算竞争度分数
            competition_score = (brand_competition_score * 0.7 + cpc_normalized * 0.3)

            return round(competition_score, 1), {
                'brand_concentration': round(top_10_share * 100, 2),
                'estimated_cpc': category_cpc,
                'sample_size': len(amazon_products),
                'top_brands': dict(sorted_brands[:5])
            }

        except Exception as e:
            logger.error(f"计算竞争度失败: {e}")
            return 50.0, {'error': str(e)}

    async def _calculate_potential(
        self,
        card: Card,
        db: AsyncSession
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算增长潜力 (P) = Keyword_Growth × 0.6 + Review_Velocity × 0.4

        数据来源:
        - Articles表中相关关键词的文章增长趋势
        - Amazon产品的评论增长速度
        """
        try:
            category_keywords = self._get_category_keywords(card.category)

            # 查询最近30天的相关文章
            cutoff_date = datetime.now() - timedelta(days=30)
            result = await db.execute(
                select(Article)
                .where(
                    and_(
                        Article.published_at >= cutoff_date,
                    ) | self._build_keyword_search(category_keywords)
                )
                .order_by(Article.published_at.asc())
                .limit(100)
            )
            articles = result.scalars().all()

            # 计算关键词增长（通过文章数量趋势）
            if len(articles) < 10:
                # 文章数量太少，无法判断趋势
                keyword_growth_score = 50.0
            else:
                # 计算最近15天 vs 15-30天的文章数量比
                now = datetime.now(tz=timezone.utc)
                recent_15 = [a for a in articles if a.published_at >= now - timedelta(days=15)]
                previous_15 = [a for a in articles if a.published_at < now - timedelta(days=15)]

                if len(previous_15) > 0:
                    growth_rate = len(recent_15) / len(previous_15)
                    # 增长率转换为分数，100%增长 = 100分，200%增长 = 120分（上限）
                    keyword_growth_score = min(120, 50 + growth_rate * 70)
                else:
                    keyword_growth_score = 50.0

            # 计算评论速度（Review Velocity）
            amazon_products = card.amazon_data.get('products', []) if card.amazon_data else []
            avg_reviews = sum(p.get('reviews_count', 0) for p in amazon_products[:20]) / min(len(amazon_products), 20)

            # 评论数量多说明活跃，但评论太多也可能意味着竞争激烈
            # 假设平均评论数在50-500之间是健康的
            review_velocity_score = min(100, avg_reviews / 5)

            # 计算增长潜力分数
            potential_score = (keyword_growth_score * 0.6 + review_velocity_score * 0.4)

            return round(potential_score, 1), {
                'article_trend': f'+{len(articles)} articles in 30 days',
                'growth_rate': round(len(recent_15) / len(previous_15) * 100 - 100, 1) if len(previous_15) > 0 else 0.0,
                'avg_reviews': round(avg_reviews, 1),
                'sample_size': len(amazon_products)
            }

        except Exception as e:
            logger.error(f"计算增长潜力失败: {e}")
            return 50.0, {'error': str(e)}

    async def _calculate_intelligence_gap(
        self,
        card: Card,
        db: AsyncSession
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算信息差/痛点 (I) = Negative_Review_Sentiment / Product_Feature_Consistency

        这是AI的核心战场！
        通过分析评论中的负面情感集中度来评估痛点清晰度

        数据来源:
        - AI分析Articles中的相关文章内容
        - Amazon产品评论（需要OpenClaw采集）
        """
        try:
            # 查找相关的AI分析文章
            category_keywords = self._get_category_keywords(card.category)

            cutoff_date = datetime.now() - timedelta(days=30)
            result = await db.execute(
                select(Article.content_theme, Article.summary)
                .where(
                    and_(
                        Article.published_at >= cutoff_date,
                        Article.is_processed == True
                    ) | self._build_keyword_search(category_keywords)
                )
                .limit(20)
            )
            articles = result.all()

            if not articles:
                # 无AI分析数据，返回中等信息差
                return 50.0, {'reason': '无AI分析数据', 'fallback': True}

            # 计算痛点集中度（模拟）
            # 在实际实现中，这应该由AI分析评论数据得出
            # 这里我们用文章内容主题作为代理指标

            # 统计内容主题分布
            theme_counts = {}
            for article in articles:
                theme = article[0]  # content_theme
                if theme:
                    theme_counts[theme] = theme_counts.get(theme, 0) + 1

            # 如果某个主题特别集中，说明痛点明确
            if theme_counts:
                max_count = max(theme_counts.values())
                total_themes = sum(theme_counts.values())
                concentration_ratio = max_count / total_themes if total_themes > 0 else 0

                # 痛点越集中（concentration_ratio高），I值越高
                intelligence_score = concentration_ratio * 100
            else:
                intelligence_score = 50.0

            return round(intelligence_score, 1), {
                'theme_distribution': theme_counts,
                'dominant_theme': max(theme_counts.items(), key=lambda x: x[1])[0] if theme_counts else None,
                'concentration_ratio': round(concentration_ratio, 2),
                'article_count': len(articles),
                'data_source': 'ai_articles'
            }

        except Exception as e:
            logger.error(f"计算信息差失败: {e}")
            return 50.0, {'error': str(e)}

    def _classify_opportunity_type(
        self,
        competition_score: float,
        potential_score: float,
        intelligence_score: float
    ) -> str:
        """
        根据C-P-I三维度分类商机类型

        分类规则:
        - "长尾暴利型": C低(<60), P中(60-80), I高(>70) - 适合个人卖家
        - "类目收割型": P极高(>90), C高(>70) - 适合资本型卖家
        - "技术改良型": I极高(>85) - 适合工厂型卖家
        """
        c, p, i = competition_score, potential_score, intelligence_score

        if p > 90 and c > 70:
            return "类目收割型"
        elif i > 85:
            return "技术改良型"
        elif c < 60 and p > 50 and i > 60:
            return "长尾暴利型"
        elif c > 80:
            return "高竞争型"
        elif p < 40:
            return "低潜力型"
        else:
            return "综合型"

    def _get_category_keywords(self, category: str) -> List[str]:
        """获取品类相关关键词"""
        keyword_map = {
            'wireless_earbuds': ['耳机', 'earbuds', 'headphones', 'audio'],
            'smart_plugs': ['智能插座', 'smart plug', 'outlet'],
            'fitness_trackers': ['健身', 'fitness', 'tracker', 'watch'],
            'phone_chargers': ['充电器', 'charger', 'charging'],
            'desk_lamps': ['台灯', 'desk lamp', 'lighting'],
            'phone_cases': ['手机壳', 'phone case', 'case'],
            'yoga_mats': ['瑜伽垫', 'yoga mat', 'fitness'],
            'coffee_makers': ['咖啡机', 'coffee maker'],
            'bluetooth_speakers': ['音箱', 'speakers', 'audio', 'sound'],
            'webcams': ['摄像头', 'webcam', 'camera'],
            'keyboards': ['键盘', 'keyboard'],
            'mouse': ['鼠标', 'mouse']
        }
        return keyword_map.get(category, [category])

    def _get_category_cpc(self, category: str) -> float:
        """
        获取品类的估计CPC（每点击成本）

        这是模拟数据，实际应该从Google Ads API或类似来源获取
        """
        cpc_map = {
            'wireless_earbuds': 1.2,
            'smart_plugs': 0.8,
            'fitness_trackers': 1.5,
            'phone_chargers': 0.5,
            'desk_lamps': 0.6,
            'phone_cases': 0.4,
            'yoga_mats': 0.7,
            'coffee_makers': 1.0,
            'bluetooth_speakers': 0.9,
            'webcams': 1.8,
            'keyboards': 0.7,
            'mouse': 0.5
        }
        return cpc_map.get(category, 1.0)

    def _build_keyword_search(self, keywords: List[str]) -> Any:
        """构建关键词搜索条件"""
        from sqlalchemy import or_

        conditions = []
        for keyword in keywords[:3]:  # 限制关键词数量
            conditions.append(Article.title.ilike(f'%{keyword}%'))
            conditions.append(Article.summary.ilike(f'%{keyword}%'))

        return or_(*conditions) if conditions else True


# 全局单例
opportunity_scorer = OpportunityScorer()
