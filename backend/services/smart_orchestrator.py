# services/smart_orchestrator.py
"""智能商机跟踪系统 - 协调器

协调AI和OpenClaw的交互，管理商机漏斗的演进
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, and_, or_
from config.database import AsyncSessionLocal
from models.business_opportunity import (
    BusinessOpportunity, DataCollectionTask,
    OpportunityStatus, TaskStatus
)
from services.ai_opportunity_analyzer import AIOpportunityAnalyzer
from services.signal_adapters import SignalAdapterFactory

logger = logging.getLogger(__name__)


class SmartOpportunityOrchestrator:
    """
    AI-OpenClaw智能联盟协调器

    职责：
    1. 处理新信号，发现商机
    2. 协调数据采集
    3. 管理商机状态演进
    4. 处理采集结果
    """

    def __init__(self):
        self.ai_analyzer = AIOpportunityAnalyzer()
        # openclaw_client将在需要时初始化

    async def process_signal(
        self,
        signal: Dict[str, Any],
        db: AsyncSessionLocal,
        auto_collect: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        处理新信号，可能创建新商机

        Args:
            signal: 原始信号数据
            db: 数据库session
            auto_collect: 是否自动启动数据采集

        Returns:
            创建的商机数据，如果不是商机则返回None
        """
        try:
            logger.info(f"📥 处理信号: {signal.get('title', 'N/A')}")

            # AI分析信号
            opportunity_data = await self.ai_analyzer.analyze_signal(signal)

            if not opportunity_data:
                logger.info("❌ AI判断不是商机")
                return None

            # 创建商机
            opportunity = BusinessOpportunity(
                title=opportunity_data.get('title'),
                description=opportunity_data.get('description'),
                opportunity_type=opportunity_data.get('opportunity_type', 'product'),
                status=OpportunityStatus.POTENTIAL,
                elements=opportunity_data.get('elements', {}),
                ai_insights=opportunity_data.get('ai_insights', {}),
                confidence_score=opportunity_data.get('confidence_score', 0.5)
            )

            db.add(opportunity)
            await db.commit()
            await db.refresh(opportunity)

            logger.info(f"🎯 创建商机: {opportunity.title} (置信度: {opportunity.confidence_score:.0%})")

            # 如果有数据需求，启动验证
            data_requirements = opportunity.ai_insights.get('data_requirements', [])
            if auto_collect and data_requirements:
                await self._initiate_verification(opportunity.id, data_requirements, db)

            return opportunity.to_dict()

        except Exception as e:
            logger.error(f"处理信号失败: {e}")
            await db.rollback()
            return None

    async def _initiate_verification(
        self,
        opportunity_id: UUID,
        data_requirements: List[Dict],
        db: AsyncSessionLocal
    ):
        """启动数据采集验证"""
        try:
            # 更新商机状态
            result = await db.execute(
                select(BusinessOpportunity).where(BusinessOpportunity.id == opportunity_id)
            )
            opportunity = result.scalar_one_or_none()

            if not opportunity:
                logger.error(f"商机不存在: {opportunity_id}")
                return

            # 转换到验证状态
            if opportunity.status == OpportunityStatus.POTENTIAL:
                opportunity.transition_to(OpportunityStatus.VERIFYING)
                opportunity.last_verification_at = datetime.utcnow()
                await db.commit()

            # 创建采集任务
            for req in data_requirements:
                task = DataCollectionTask(
                    opportunity_id=opportunity_id,
                    task_type=req.get('data_needed', {}).get('type', 'generic'),
                    priority=req.get('priority', 'medium'),
                    ai_request=req
                )

                db.add(task)
                await db.commit()

                # TODO: 提交给OpenClaw
                # await self.openclaw_client.submit_collection_task(str(task.id), req)

                logger.info(f"📤 创建采集任务: {req.get('question', 'N/A')}")

        except Exception as e:
            logger.error(f"启动验证失败: {e}")
            await db.rollback()

    async def on_collection_complete(
        self,
        task_result: Dict[str, Any],
        db: AsyncSessionLocal
    ):
        """
        处理OpenClaw采集完成的结果

        Args:
            task_result: 采集结果
            db: 数据库session
        """
        try:
            request_id = task_result.get('request_id')
            status = task_result.get('status')

            # 查找任务
            result = await db.execute(
                select(DataCollectionTask).where(
                    DataCollectionTask.ai_request.contains(request_id)
                )
            )
            tasks = result.scalars().all()

            if not tasks:
                logger.warning(f"未找到对应的采集任务: {request_id}")
                return

            task = tasks[0]

            # 更新任务状态
            if status == 'completed':
                task.result = task_result.get('result')
                task.completed_at = datetime.utcnow()
            else:
                task.error_message = task_result.get('error', {}).get('message')
                task.completed_at = datetime.utcnow()

            await db.commit()

            # 如果成功，通知AI分析
            if status == 'completed':
                await self._process_collection_result(task, task_result.get('result', {}), db)

        except Exception as e:
            logger.error(f"处理采集结果失败: {e}")
            await db.rollback()

    async def _process_collection_result(
        self,
        task: DataCollectionTask,
        result: Dict[str, Any],
        db: AsyncSessionLocal
    ):
        """处理采集结果，更新商机判断"""
        try:
            # 获取商机
            opp_result = await db.execute(
                select(BusinessOpportunity).where(BusinessOpportunity.id == task.opportunity_id)
            )
            opportunity = opp_result.scalar_one_or_none()

            if not opportunity:
                logger.error(f"商机不存在: {task.opportunity_id}")
                return

            # AI分析新数据
            old_confidence = opportunity.confidence_score
            updated = await self.ai_analyzer.update_with_new_data(
                opportunity.to_dict(),
                result,
                task.ai_request.get('question', 'Data collection')
            )

            # 更新商机
            opportunity.confidence_score = updated.get('confidence_score', old_confidence)
            opportunity.ai_insights = updated.get('ai_insights', {})
            opportunity.last_verification_at = datetime.utcnow()

            await db.commit()

            logger.info(
                f"📊 商机 {opportunity.id} 置信度更新: "
                f"{old_confidence:.0%} → {opportunity.confidence_score:.0%}"
            )

            # 检查是否需要更多数据
            data_requirements = updated.get('ai_insights', {}).get('data_requirements', [])
            if data_requirements:
                await self._initiate_verification(opportunity.id, data_requirements, db)
            else:
                # 没有更多数据需求，检查是否应该演进
                await self._check_and_evolve(opportunity, db)

        except Exception as e:
            logger.error(f"处理采集结果失败: {e}")
            await db.rollback()

    async def _check_and_evolve(
        self,
        opportunity: BusinessOpportunity,
        db: AsyncSessionLocal
    ):
        """检查并执行商机状态演进"""
        try:
            next_status = opportunity.should_auto_evolve()

            if next_status:
                old_status = opportunity.status
                opportunity.transition_to(next_status)
                await db.commit()

                logger.info(
                    f"🔄 商机 {opportunity.id} 状态演进: "
                    f"{old_status.value} → {next_status.value}"
                )

                # 如果进入评估期，生成可行性报告
                if next_status == OpportunityStatus.ASSESSING:
                    await self._generate_feasibility_report(opportunity, db)

        except Exception as e:
            logger.error(f"状态演进失败: {e}")
            await db.rollback()

    async def _generate_feasibility_report(
        self,
        opportunity: BusinessOpportunity,
        db: AsyncSessionLocal
    ):
        """生成可行性报告"""
        try:
            report = await self.ai_analyzer.generate_feasibility_report(
                opportunity.to_dict()
            )

            if report:
                opportunity.ai_insights['feasibility_report'] = report
                await db.commit()

                logger.info(f"📋 生成可行性报告: {opportunity.id}")

        except Exception as e:
            logger.error(f"生成可行性报告失败: {e}")

    async def manage_funnel(self, db: AsyncSessionLocal):
        """
        管理商机漏斗（定时任务）

        检查所有商机的状态，执行自动演进
        """
        try:
            logger.info("🔄 执行漏斗管理任务")

            # 查找需要检查的商机
            result = await db.execute(
                select(BusinessOpportunity)
                .where(
                    or_(
                        BusinessOpportunity.status == OpportunityStatus.VERIFYING,
                        BusinessOpportunity.status == OpportunityStatus.ASSESSING
                    )
                )
            )
            opportunities = result.scalars().all()

            logger.info(f"📊 检查 {len(opportunities)} 个商机")

            for opportunity in opportunities:
                try:
                    await self._check_and_evolve(opportunity, db)

                    # 超时处理
                    if opportunity.last_verification_at:
                        time_since_verify = datetime.utcnow() - opportunity.last_verification_at

                        # 验证期超过7天且置信度仍低 → 降低优先级
                    if opportunity.status == OpportunityStatus.VERIFYING:
                        if time_since_verify > timedelta(days=7):
                            if opportunity.confidence_score < 0.6:
                                logger.warning(f"⚠️ 商机 {opportunity.id} 验证超时，置信度低")
                                # 可以标记为低优先级或归档

                except Exception as e:
                    logger.error(f"处理商机 {opportunity.id} 失败: {e}")
                    continue

            logger.info("✅ 漏斗管理任务完成")

        except Exception as e:
            logger.error(f"漏斗管理失败: {e}")

    async def get_statistics(self, db: AsyncSessionLocal) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            # 总商机数
            total_result = await db.execute(select(BusinessOpportunity.id))
            total = len(total_result.all())

            # 各状态统计
            status_stats = {}
            for status in OpportunityStatus:
                result = await db.execute(
                    select(BusinessOpportunity.id).where(BusinessOpportunity.status == status)
                )
                count = len(result.all())
                status_stats[status.value] = count

            # 采集任务统计
            task_result = await db.execute(select(DataCollectionTask.id))
            total_tasks = len(task_result.all())

            completed_task_result = await db.execute(
                select(DataCollectionTask.id).where(DataCollectionTask.status == TaskStatus.COMPLETED)
            )
            completed_tasks = len(completed_task_result.all())

            return {
                "total_opportunities": total,
                "status_distribution": status_stats,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "task_completion_rate": completed_tasks / total_tasks if total_tasks > 0 else 0
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}


# 单例实例
_orchestrator_instance = None

def get_orchestrator() -> SmartOpportunityOrchestrator:
    """获取协调器单例"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = SmartOpportunityOrchestrator()
    return _orchestrator_instance
