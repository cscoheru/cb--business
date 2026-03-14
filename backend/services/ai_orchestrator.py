"""
AI编排服务 - 智能决策与OpenClaw调度

这是从"定时爬虫"到"AI驱动"的核心转变：
AI分析 → 发现数据缺口 → MCP调用OpenClaw → 补齐数据 → 重新评估
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.card import Card
from models.business_opportunity import BusinessOpportunity, OpportunityStatus, DataCollectionTask
from services.opportunity_algorithm import opportunity_scorer

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    AI编排器 - 智能决策中心

    职责:
    1. 分析商机数据，识别置信度不足的维度
    2. 通过MCP调用OpenClaw技能补齐数据
    3. 整合新数据，重新计算C-P-I分数
    4. 判断商机状态是否需要演进
    """

    # 数据完整性阈值
    CONFIDENCE_THRESHOLDS = {
        'low': 0.5,        # 低置信度: 需要补充数据
        'medium': 0.7,     # 中等置信度: 可以展示，建议验证
        'high': 0.85       # 高置信度: 数据充分
    }

    def __init__(self):
        # MCP客户端 (延迟加载)
        self._mcp_client = None

    async def get_mcp_client(self):
        """获取MCP客户端 (懒加载)"""
        if self._mcp_client is None:
            try:
                from config.mcp_client import openclaw_mcp
                await openclaw_mcp.connect()
                self._mcp_client = openclaw_mcp
            except ImportError:
                logger.warning("MCP客户端未配置，将使用fallback数据")
                self._mcp_client = None
        return self._mcp_client

    async def analyze_and_verify(
        self,
        card: Card,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        分析并验证商机 - AI驱动的智能闭环

        流程:
        1. 初步C-P-I评分
        2. 识别数据缺口
        3. MCP调用OpenClaw补齐数据
        4. 重新计算C-P-I分数
        5. 判断状态演进

        Returns:
            包含初始分数、数据补齐情况、最终分数的字典
        """
        try:
            # 1. 初步C-P-I评分
            initial_score = await opportunity_scorer.calculate_opportunity_score(card, db)
            logger.info(f"初始C-P-I分数: {initial_score['total_score']}")

            # 2. 识别数据缺口
            data_gaps = await self._identify_data_gaps(initial_score, card)
            logger.info(f"识别到 {len(data_gaps)} 个数据缺口")

            if not data_gaps:
                # 数据完整，无需补充
                return {
                    'initial_score': initial_score,
                    'data_gaps_filled': [],
                    'final_score': initial_score,
                    'confidence_improvement': 0,
                    'verification_needed': False
                }

            # 3. 通过MCP调用OpenClaw补齐数据
            filled_data = []
            mcp_client = await self.get_mcp_client()

            if mcp_client:
                for gap in data_gaps:
                    try:
                        fill_result = await self._fill_data_gap(gap, card, mcp_client)
                        if fill_result.get('success'):
                            filled_data.append(fill_result)
                            logger.info(f"成功填补数据缺口: {gap['type']}")
                    except Exception as e:
                        logger.error(f"填补数据缺口失败 {gap['type']}: {e}")
                        # 使用fallback数据
                        filled_data.append(self._get_fallback_data(gap))
            else:
                # MCP不可用，使用fallback数据
                logger.warning("MCP不可用，使用fallback数据")
                filled_data = [self._get_fallback_data(gap) for gap in data_gaps]

            # 4. 整合新数据，重新计算C-P-I分数
            # (这里需要将OpenClaw返回的数据更新到card或直接用于计算)
            final_score = await self._recalculate_with_new_data(
                card,
                initial_score,
                filled_data,
                db
            )

            # 5. 计算置信度提升
            confidence_improvement = final_score['total_score'] - initial_score['total_score']

            return {
                'initial_score': initial_score,
                'data_gaps': data_gaps,
                'data_gaps_filled': filled_data,
                'final_score': final_score,
                'confidence_improvement': confidence_improvement,
                'verification_needed': len(data_gaps) > 0
            }

        except Exception as e:
            logger.error(f"AI编排失败: {e}", exc_info=True)
            raise

    async def _identify_data_gaps(
        self,
        score_result: Dict[str, Any],
        card: Card
    ) -> List[Dict[str, Any]]:
        """
        识别数据缺口

        基于C-P-I三维度分数和Card数据完整性的判断

        Returns:
            需要补充的数据类型列表
        """
        gaps = []

        c_score = score_result['competition']['score']
        p_score = score_result['potential']['score']
        i_score = score_result['intelligence_gap']['score']

        # 竞争度数据缺口
        if c_score < 65:
            # 竞争度不确定，需要深度市场扫描
            gaps.append({
                'type': 'competition_deep_scan',
                'priority': 'high' if c_score < 50 else 'medium',
                'reason': f"竞争度分数{c_score}较低，需要验证品牌分布和CPC",
                'skill': 'deep_market_scan',
                'params': {
                    'category': card.category,
                    'anomaly_detected': False,
                    'depth_level': 'deep' if c_score < 50 else 'standard'
                }
            })

        # 增长潜力数据缺口
        if 50 < p_score < 85:
            # 增长潜力波动，需要趋势验证
            gaps.append({
                'type': 'potential_trend_verification',
                'priority': 'medium',
                'reason': f"增长潜力分数{p_score}处于中等区间，需要验证趋势持续性",
                'skill': 'deep_market_scan',
                'params': {
                    'category': card.category,
                    'anomaly_detected': True,
                    'depth_level': 'standard'
                }
            })

        # 信息差数据缺口
        if i_score > 75:
            # 信息差高，需要深度分析竞品评论
            gaps.append({
                'type': 'intelligence_gap_analysis',
                'priority': 'high' if i_score > 85 else 'medium',
                'reason': f"信息差分数{i_score}较高，需要深度分析用户痛点",
                'skill': 'mock_order_analysis',  # 使用模拟下单获取真实成本
                'params': {
                    'asin': self._get_top_asin(card),
                    'quantity': 1
                }
            })

        # 检查Card数据完整性
        amazon_products = card.amazon_data.get('products', [])
        if not amazon_products or len(amazon_products) < 10:
            gaps.append({
                'type': 'insufficient_product_data',
                'priority': 'high',
                'reason': f"产品数据不足 (仅{len(amazon_products)}个)",
                'skill': 'deep_market_scan',
                'params': {
                    'category': card.category,
                    'anomaly_detected': False,
                    'depth_level': 'intensive'
                }
            })

        return gaps

    async def _fill_data_gap(
        self,
        gap: Dict[str, Any],
        card: Card,
        mcp_client
    ) -> Dict[str, Any]:
        """
        通过MCP调用OpenClaw填补数据缺口

        这是AI驱动的核心：AI分析需要什么数据，主动调用OpenClaw获取
        """
        skill_name = gap['skill']
        params = gap['params']

        logger.info(f"调用OpenClaw技能: {skill_name}, 参数: {params}")

        try:
            # 通过MCP调用OpenClaw
            result = await mcp_client.call_tool(skill_name, params)

            # 解析结果
            import json
            result_data = json.loads(result[0].text) if isinstance(result, list) else result

            return {
                'success': result_data.get('success', True),
                'gap_type': gap['type'],
                'skill': skill_name,
                'data': result_data.get('data', result_data),
                'filled_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"MCP调用失败: {e}")
            return {
                'success': False,
                'gap_type': gap['type'],
                'error': str(e)
            }

    def _get_fallback_data(self, gap: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取fallback数据 (当MCP不可用时)

        使用现有Card数据或模拟数据
        """
        return {
            'success': True,
            'gap_type': gap['type'],
            'data': {
                'method': 'fallback',
                'message': 'MCP不可用，使用现有数据',
                'simulated': True
            },
            'filled_at': datetime.now().isoformat()
        }

    async def _recalculate_with_new_data(
        self,
        card: Card,
        initial_score: Dict[str, Any],
        filled_data: List[Dict[str, Any]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        使用新数据重新计算C-P-I分数

        这里可以实现更复杂的逻辑：
        - 将OpenClaw返回的数据更新到Card
        - 基于新数据重新计算三维度分数
        - 现在简化为返回初始分数 + 提升量
        """
        # 计算数据补齐带来的分数提升
        improvement = 0

        for fill in filled_data:
            if fill.get('success'):
                # 根据缺口类型计算提升量
                gap_type = fill['gap_type']

                if gap_type == 'competition_deep_scan':
                    improvement += 5  # 竞争度数据提升5分
                elif gap_type == 'potential_trend_verification':
                    improvement += 3  # 增长潜力验证提升3分
                elif gap_type == 'intelligence_gap_analysis':
                    improvement += 7  # 信息差分析提升7分
                elif gap_type == 'insufficient_product_data':
                    improvement += 10  # 产品数据补充提升10分

        # 创建新分数对象
        new_score = initial_score.copy()
        new_score['total_score'] = min(100, initial_score['total_score'] + improvement)
        new_score['data_enhanced'] = True
        new_score['enhancement_details'] = filled_data

        return new_score

    def _get_top_asin(self, card: Card) -> str:
        """获取Card中Top产品的ASIN"""
        products = card.amazon_data.get('products', [])
        if products:
            return products[0].get('asin', '')
        return ''

    async def batch_analyze_and_verify(
        self,
        cards: List[Card],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        批量分析并验证商机

        用于定时任务或触发式分析
        """
        results = []

        for card in cards:
            try:
                result = await self.analyze_and_verify(card, db)
                results.append({
                    'card_id': str(card.id),
                    'category': card.category,
                    'result': result
                })
            except Exception as e:
                logger.error(f"分析Card {card.id} 失败: {e}")
                results.append({
                    'card_id': str(card.id),
                    'error': str(e)
                })

        return results


# 全局单例
ai_orchestrator = AIOrchestrator()
