# services/upsell_detector.py
from typing import Dict, Optional
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from models.user import User
from models.subscription import UserUsage
from schemas.subscription import UpsellSuggestionResponse


class UpsellDetector:
    """付费触发检测器"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_user_actions(self, user_id: str) -> Dict[str, bool]:
        """分析用户行为，判断是否应该触发付费推荐"""
        signals = {
            "cost_calculator_needed": False,
            "supplier_needed": False,
            "ai_analysis_needed": False,
            "data_export_needed": False,
        }

        # 检测成本计算器使用频率
        today = date.today()
        result = await self.db.execute(
            select(func.count(UserUsage.id))
            .where(
                and_(
                    UserUsage.user_id == user_id,
                    UserUsage.usage_type == "cost_calculator",
                    UserUsage.period_date == today,
                )
            )
        )
        usage_count = result.scalar() or 0

        if usage_count >= 3:
            signals["cost_calculator_needed"] = True

        # 检测品类浏览频率
        week_ago = today - timedelta(days=7)
        result = await self.db.execute(
            select(func.count(UserUsage.id))
            .where(
                and_(
                    UserUsage.user_id == user_id,
                    UserUsage.usage_type == "view_category",
                    UserUsage.period_date >= week_ago,
                )
            )
        )
        category_views = result.scalar() or 0

        if category_views >= 5:
            signals["supplier_needed"] = True

        # 检测AI分析尝试
        result = await self.db.execute(
            select(func.count(UserUsage.id))
            .where(
                and_(
                    UserUsage.user_id == user_id,
                    UserUsage.usage_type == "ai_analysis_attempt",
                    UserUsage.period_date >= week_ago,
                )
            )
        )
        ai_attempts = result.scalar() or 0

        if ai_attempts >= 2:
            signals["ai_analysis_needed"] = True

        # 检测数据导出尝试
        result = await self.db.execute(
            select(func.count(UserUsage.id))
            .where(
                and_(
                    UserUsage.user_id == user_id,
                    UserUsage.usage_type == "export_attempt",
                    UserUsage.period_date >= week_ago,
                )
            )
        )
        export_attempts = result.scalar() or 0

        if export_attempts >= 1:
            signals["data_export_needed"] = True

        return signals

    async def get_recommended_upgrade(self, user: User) -> Optional[UpsellSuggestionResponse]:
        """获取推荐的升级方案"""
        if user.plan_tier.value != "free":
            return None

        signals = await self.analyze_user_actions(str(user.id))

        # 根据信号确定推荐消息
        message = None
        features = []

        if signals["ai_analysis_needed"]:
            message = "您正在使用AI分析功能，专业版可以解锁无限次使用"
            features = ["AI智能分析", "精确成本计算器", "供应商数据库", "数据导出"]
        elif signals["supplier_needed"]:
            message = "您正在深入调研市场，专业版可以提供供应商数据库"
            features = ["供应商数据库", "精确成本计算器", "数据导出"]
        elif signals["cost_calculator_needed"]:
            message = "您正在频繁使用成本计算器，专业版可以提供更精确的数据"
            features = ["精确成本计算器", "无限API调用", "数据导出"]
        elif signals["data_export_needed"]:
            message = "您需要导出数据，专业版可以解锁此功能"
            features = ["数据导出", "精确成本计算器", "供应商数据库"]
        else:
            return None

        return UpsellSuggestionResponse(
            should_upgrade=True,
            message=message,
            recommended_plan="pro",
            features=features,
            price="¥99/月",
            action_url="/pricing",
        )

    async def get_user_engagement_score(self, user_id: str) -> float:
        """计算用户参与度分数（0-1）"""
        today = date.today()
        week_ago = today - timedelta(days=7)

        # 获取本周总使用次数
        result = await self.db.execute(
            select(func.sum(UserUsage.quantity))
            .where(
                and_(
                    UserUsage.user_id == user_id,
                    UserUsage.period_date >= week_ago,
                )
            )
        )
        total_usage = result.scalar() or 0

        # 获取活跃天数
        result = await self.db.execute(
            select(func.count(func.distinct(UserUsage.period_date)))
            .where(
                and_(
                    UserUsage.user_id == user_id,
                    UserUsage.period_date >= week_ago,
                )
            )
        )
        active_days = result.scalar() or 0

        # 计算分数（简单算法）
        usage_score = min(total_usage / 50, 1.0)  # 50次使用为满分
        activity_score = active_days / 7  # 7天活跃为满分

        return (usage_score + activity_score) / 2

    async def get_churn_risk(self, user_id: str) -> str:
        """获取用户流失风险等级"""
        today = date.today()

        # 获取最后活跃日期
        result = await self.db.execute(
            select(func.max(UserUsage.period_date))
            .where(UserUsage.user_id == user_id)
        )
        last_active = result.scalar() or today

        days_since_active = (today - last_active).days

        if days_since_active >= 14:
            return "high"
        elif days_since_active >= 7:
            return "medium"
        else:
            return "low"
