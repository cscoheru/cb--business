# services/signal_recognition.py
"""信号识别引擎 - 从海量线索中识别高潜力商机信号

这是OpenClaw+AI智能协同系统的第一层：
扫描Card、用户收藏等数据源，应用C-P-I算法识别值得验证的高潜力信号
"""

import logging
from typing import Dict, Any, List, Optional, Set
from sqlalchemy import select, and_, Boolean
from sqlalchemy.ext.asyncio import AsyncSession

from models.card import Card
from models.business_opportunity import BusinessOpportunity
from services.opportunity_algorithm import opportunity_scorer

logger = logging.getLogger(__name__)


class SignalRecognitionEngine:
    """信号识别引擎"""

    # 信号识别阈值
    THRESHOLDS = {
        'high_potential': 70,      # C-P-I总分 >= 70 为高潜力
        'medium_potential': 60,    # C-P-I总分 >= 60 为中等潜力
        'intelligence_gap_high': 75,  # I值 >= 75 需要深度验证
        'competition_low': 50,     # C值 < 50 需要验证竞争度
    }

    async def scan_leads(
        self,
        db: AsyncSession,
        include_favorited: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        扫描所有线索，识别高潜力信号

        数据源:
        1. Cards表中的12个品类卡片
        2. 用户收藏的卡片 (通过favorites表)
        3. 近24小时新增的卡片

        Args:
            db: 数据库session
            include_favorited: 是否优先包含用户收藏
            limit: 最大返回数量

        Returns:
            高潜力线索列表，按优先级排序
        """
        try:
            logger.info("开始扫描线索...")

            # 1. 获取所有Cards (有amazon_data的)
            cards_query = select(Card).where(Card.amazon_data.isnot(None))
            cards_result = await db.execute(cards_query)
            all_cards = cards_result.scalars().all()

            logger.info(f"找到 {len(all_cards)} 张有效卡片")

            # 2. 获取用户收藏的卡片ID
            favorited_card_ids: Set[str] = set()
            if include_favorited:
                fav_query = select(BusinessOpportunity.card_id).where(
                    and_(
                        BusinessOpportunity.card_id.isnot(None),
                        BusinessOpportunity.user_interactions['saved'].astext.cast(Boolean) == True
                    )
                )
                fav_result = await db.execute(fav_query)
                favorited_card_ids = {str(row[0]) for row in fav_result.all() if row[0]}

                logger.info(f"用户收藏了 {len(favorited_card_ids)} 张卡片")

            # 3. 应用C-P-I算法评分
            scored_leads = []
            for card in all_cards:
                try:
                    # 计算C-P-I分数
                    score_result = await opportunity_scorer.calculate_opportunity_score(card, db)

                    # 判断是否为高潜力信号
                    total_score = score_result['total_score']
                    if total_score >= self.THRESHOLDS['high_potential']:
                        is_favorited = str(card.id) in favorited_card_ids
                        priority = self._calculate_priority(score_result, is_favorited)

                        scored_leads.append({
                            'card_id': str(card.id),
                            'card': card,
                            'category': card.category,
                            'title': card.content.get('summary', {}).get('title', card.category),
                            'cpi_score': score_result,
                            'is_favorited': is_favorited,
                            'priority': priority,
                            'signal_type': self._classify_signal_type(score_result),
                            'verification_needs': self._identify_verification_needs(score_result)
                        })

                except Exception as e:
                    logger.error(f"为Card {card.id} 计算C-P-I分数失败: {e}")
                    continue

            # 4. 按优先级排序
            scored_leads.sort(key=lambda x: x['priority'], reverse=True)

            logger.info(f"识别到 {len(scored_leads)} 个高潜力信号")

            return scored_leads[:limit]

        except Exception as e:
            logger.error(f"扫描线索失败: {e}")
            raise

    def _calculate_priority(
        self,
        score_result: Dict[str, Any],
        is_favorited: bool
    ) -> float:
        """
        计算信号优先级

        优先级规则 (从高到低):
        1. 用户收藏 +30分
        2. I值(信息差) > 80 +20分
        3. I值(信息差) > 75 +10分
        4. C值(竞争度) < 50 +15分 (低竞争，蓝海机会)
        5. C-P-I总分直接贡献

        Returns:
            优先级分数 (越高越优先)
        """
        priority = score_result['total_score']

        # 用户收藏权重最高
        if is_favorited:
            priority += 30

        # 信息差权重第二
        i_score = score_result['intelligence_gap']['score']
        if i_score > 80:
            priority += 20
        elif i_score > 75:
            priority += 10

        # 低竞争权重第三
        c_score = score_result['competition']['score']
        if c_score < 50:
            priority += 15

        return round(priority, 1)

    def _classify_signal_type(self, score_result: Dict[str, Any]) -> str:
        """
        分类信号类型

        基于C-P-I三维度组合，判断信号特征

        Returns:
            信号类型字符串
        """
        c = score_result['competition']['score']
        p = score_result['potential']['score']
        i = score_result['intelligence_gap']['score']

        if c < 50 and p > 70 and i > 75:
            return "蓝海机会型"  # 低竞争+高潜力+高信息差
        elif i > 85:
            return "痛点明确型"  # 信息差极高，痛点清晰
        elif p > 85:
            return "增长强劲型"  # 增长潜力极高
        elif c < 50:
            return "低竞争型"  # 竞争度低
        elif p > 70 and i > 70:
            return "均衡发展型"  # 潜力和信息差都好
        else:
            return "综合观察型"  # 各维度均衡

    def _identify_verification_needs(self, score_result: Dict[str, Any]) -> List[str]:
        """
        识别验证需求

        基于C-P-I分数，判断需要采集哪些验证数据

        Returns:
            所需验证数据类型列表
        """
        needs = []

        c = score_result['competition']['score']
        p = score_result['potential']['score']
        i = score_result['intelligence_gap']['score']

        # 竞争度验证需求
        if c < 60:
            needs.append("竞品品牌分布分析")
        if c < 50:
            needs.append("CPC出价监控")
        if c < 40:
            needs.append("新品上架速度追踪")

        # 增长潜力验证需求
        if 50 < p < 80:
            needs.append("关键词搜索量验证")
        if p < 70:
            needs.append("社交媒体声量追踪")
        if p < 60:
            needs.append("评论增长速度统计")

        # 信息差验证需求
        if i > 75:
            needs.append("竞品差评情感分析")
        if i > 80:
            needs.append("痛点集中度计算")
        if i > 85:
            needs.append("用户需求缺口识别")

        return needs if needs else ["基础数据验证"]

    async def get_top_signals(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        获取Top N高潜力信号的摘要信息

        用于首页展示或快速浏览

        Returns:
            包含Top信号列表和统计信息的字典
        """
        leads = await self.scan_leads(db, limit=limit)

        # 统计信息
        stats = {
            'total_scanned': len(leads),
            'by_type': {},
            'by_category': {},
            'avg_score': 0
        }

        total_score = 0
        for lead in leads:
            # 按类型统计
            signal_type = lead['signal_type']
            stats['by_type'][signal_type] = stats['by_type'].get(signal_type, 0) + 1

            # 按品类统计
            category = lead['category']
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1

            total_score += lead['cpi_score']['total_score']

        if leads:
            stats['avg_score'] = round(total_score / len(leads), 1)

        # Top信号简化信息
        top_signals = []
        for lead in leads[:limit]:
            top_signals.append({
                'card_id': lead['card_id'],
                'title': lead['title'],
                'category': lead['category'],
                'opportunity_type': lead['cpi_score']['opportunity_type'],
                'total_score': lead['cpi_score']['total_score'],
                'signal_type': lead['signal_type'],
                'is_favorited': lead['is_favorited'],
                'c_scores': {
                    'competition': lead['cpi_score']['competition']['score'],
                    'potential': lead['cpi_score']['potential']['score'],
                    'intelligence_gap': lead['cpi_score']['intelligence_gap']['score']
                }
            })

        return {
            'stats': stats,
            'signals': top_signals
        }


# 全局单例
signal_recognition_engine = SignalRecognitionEngine()
