"""
商机等级管理服务

负责商机等级的更新、历史记录和通知
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from logging import getLogger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.business_opportunity import BusinessOpportunity, OpportunityGrade
from models.card import Card
from services.grade_calculator import GradeCalculator
from services.opportunity_algorithm import opportunity_scorer

logger = getLogger(__name__)


class GradeManager:
    """
    商机等级管理器

    职责:
    1. 更新商机等级（自动升降）
    2. 记录等级变更历史
    3. 发送等级变更通知
    4. 批量更新商机等级
    """

    @staticmethod
    async def update_opportunity_grade(
        opportunity: BusinessOpportunity,
        new_cpi_score: float,
        detailed_scores: Dict[str, float],
        db: AsyncSession,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新商机等级

        Args:
            opportunity: 商机对象
            new_cpi_score: 新的C-P-I总分
            detailed_scores: 详细分数 {competition, potential, intelligence_gap}
            db: 数据库会话
            reason: 变更原因（可选）

        Returns:
            Dict: 更新结果 {grade_changed, old_grade, new_grade, history_entry}
        """
        old_grade = opportunity.grade
        old_score = opportunity.cpi_total_score or 0

        # 计算新等级
        new_grade = GradeCalculator.calculate_grade(new_cpi_score)

        result = {
            'grade_changed': False,
            'old_grade': old_grade.value if old_grade else None,
            'new_grade': new_grade.value,
            'old_score': old_score,
            'new_score': new_cpi_score,
            'history_entry': None
        }

        # 更新CPI分数
        opportunity.cpi_total_score = new_cpi_score
        opportunity.cpi_competition_score = detailed_scores.get('competition', 0)
        opportunity.cpi_potential_score = detailed_scores.get('potential', 0)
        opportunity.cpi_intelligence_gap_score = detailed_scores.get('intelligence_gap', 0)
        opportunity.last_cpi_recalc_at = datetime.utcnow()

        # 检查是否需要升级或降级
        if old_grade != new_grade:
            # 等级发生变化
            opportunity.grade = new_grade
            opportunity.last_grade_change_at = datetime.utcnow()

            # 创建历史记录
            history_entry = GradeCalculator.create_grade_history_entry(
                from_grade=old_grade or OpportunityGrade.LEAD,
                to_grade=new_grade,
                old_score=old_score,
                new_score=new_cpi_score,
                reason=reason
            )

            # 添加到历史
            if not opportunity.grade_history:
                opportunity.grade_history = []
            opportunity.grade_history.append(history_entry)

            result['grade_changed'] = True
            result['history_entry'] = history_entry

            logger.info(
                f"商机 {opportunity.id} 等级变更: {old_grade.value if old_grade else 'None'} → {new_grade.value} "
                f"(分数: {old_score:.1f} → {new_cpi_score:.1f})"
            )

            # 发送通知 (这里可以集成通知服务)
            await GradeManager._send_grade_change_notification(
                opportunity, old_grade, new_grade, old_score, new_cpi_score
            )

        return result

    @staticmethod
    async def recalculate_and_update(
        opportunity: BusinessOpportunity,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        重新计算C-P-I分数并更新等级

        Args:
            opportunity: 商机对象
            db: 数据库会话

        Returns:
            Dict: 更新结果
        """
        # 获取关联的Card
        if not opportunity.card_id:
            logger.warning(f"商机 {opportunity.id} 没有关联Card，跳过重算")
            return {
                'grade_changed': False,
                'error': 'No associated card'
            }

        card = await db.get(Card, opportunity.card_id)
        if not card:
            logger.warning(f"商机 {opportunity.id} 的Card {opportunity.card_id} 不存在")
            return {
                'grade_changed': False,
                'error': 'Card not found'
            }

        # 重新计算C-P-I分数
        try:
            cpi_result = await opportunity_scorer.calculate_opportunity_score(card, db)

            # 提取详细分数
            detailed_scores = {
                'competition': cpi_result['competition']['score'],
                'potential': cpi_result['potential']['score'],
                'intelligence_gap': cpi_result['intelligence_gap']['score']
            }

            # 更新商机等级
            return await GradeManager.update_opportunity_grade(
                opportunity,
                cpi_result['total_score'],
                detailed_scores,
                db,
                reason="定时任务重新计算"
            )

        except Exception as e:
            logger.error(f"重新计算商机 {opportunity.id} 的CPI分数失败: {e}")
            return {
                'grade_changed': False,
                'error': str(e)
            }

    @staticmethod
    async def batch_update_grades(
        opportunities: List[BusinessOpportunity],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        批量更新商机等级

        Args:
            opportunities: 商机列表
            db: 数据库会话

        Returns:
            List[Dict]: 更新结果列表
        """
        results = []

        for opportunity in opportunities:
            try:
                result = await GradeManager.recalculate_and_update(opportunity, db)
                result['opportunity_id'] = str(opportunity.id)
                result['title'] = opportunity.title
                results.append(result)
            except Exception as e:
                logger.error(f"更新商机 {opportunity.id} 等级失败: {e}")
                results.append({
                    'opportunity_id': str(opportunity.id),
                    'title': opportunity.title,
                    'grade_changed': False,
                    'error': str(e)
                })

        # 提交所有更改
        await db.commit()

        return results

    @staticmethod
    async def _send_grade_change_notification(
        opportunity: BusinessOpportunity,
        old_grade: Optional[OpportunityGrade],
        new_grade: OpportunityGrade,
        old_score: float,
        new_score: float
    ):
        """
        发送等级变更通知

        Args:
            opportunity: 商机对象
            old_grade: 原等级
            new_grade: 新等级
            old_score: 原分数
            new_score: 新分数
        """
        # TODO: 集成通知服务 (邮件、站内信等)

        action = "升级" if GradeCalculator.should_upgrade(old_score or 0, new_score) else "降级"
        logger.info(
            f"🔔 通知用户 {opportunity.user_id}: "
            f"商机「{opportunity.title}」{action}为{new_grade.value} "
            f"({old_score or 0:.1f} → {new_score:.1f})"
        )

        # 这里可以调用通知服务
        # await notification_service.send(...)

    @staticmethod
    def get_grade_summary(opportunity: BusinessOpportunity) -> Dict[str, Any]:
        """
        获取商机等级摘要

        Args:
            opportunity: 商机对象

        Returns:
            Dict: 等级摘要信息
        """
        current_grade = opportunity.grade
        current_score = opportunity.cpi_total_score or 0

        downgrade_threshold, upgrade_threshold = GradeCalculator.get_next_target_scores(
            current_grade or OpportunityGrade.LEAD
        )

        return {
            'current_grade': current_grade.value if current_grade else None,
            'current_score': current_score,
            'description': GradeCalculator.get_grade_description(
                current_grade or OpportunityGrade.LEAD
            ),
            'downgrade_threshold': downgrade_threshold,
            'upgrade_threshold': upgrade_threshold,
            'grade_change_count': len(opportunity.grade_history or []),
            'last_grade_change': opportunity.last_grade_change_at.isoformat() if opportunity.last_grade_change_at else None,
            'last_cpi_recalc': opportunity.last_cpi_recalc_at.isoformat() if opportunity.last_cpi_recalc_at else None,
        }
