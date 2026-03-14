"""
商机等级计算服务

基于C-P-I总分自动计算商机等级：
- < 60分 → LEAD (线索)
- 60-69分 → NORMAL (普通商机)
- 70-84分 → PRIORITY (重点商机)
- ≥ 85分 → LANDABLE (落地商机)
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from logging import getLogger

from models.business_opportunity import OpportunityGrade

logger = getLogger(__name__)


class GradeCalculator:
    """
    商机等级计算器

    根据C-P-I总分动态计算商机等级，支持自动升降级
    """

    # 等级阈值配置
    THRESHOLDS = {
        'lead_max': 60,        # 线索上限
        'normal_min': 60,      # 普通商机下限
        'normal_max': 70,      # 普通商机上限
        'priority_min': 70,    # 重点商机下限
        'priority_max': 85,    # 重点商机上限
        'landable_min': 85,    # 落地商机下限
    }

    @classmethod
    def calculate_grade(cls, cpi_total_score: float) -> OpportunityGrade:
        """
        根据C-P-I总分计算商机等级

        Args:
            cpi_total_score: C-P-I总分 (0-100)

        Returns:
            OpportunityGrade: 对应的商机等级

        Examples:
            >>> GradeCalculator.calculate_grade(58)
            <OpportunityGrade.LEAD: 'lead'>
            >>> GradeCalculator.calculate_grade(65)
            <OpportunityGrade.NORMAL: 'normal'>
            >>> GradeCalculator.calculate_grade(80)
            <OpportunityGrade.PRIORITY: 'priority'>
            >>> GradeCalculator.calculate_grade(90)
            <OpportunityGrade.LANDABLE: 'landable'>
        """
        if cpi_total_score < cls.THRESHOLDS['lead_max']:
            return OpportunityGrade.LEAD
        elif cpi_total_score < cls.THRESHOLDS['normal_max']:
            return OpportunityGrade.NORMAL
        elif cpi_total_score < cls.THRESHOLDS['priority_max']:
            return OpportunityGrade.PRIORITY
        else:
            return OpportunityGrade.LANDABLE

    @classmethod
    def should_upgrade(cls, old_score: float, new_score: float) -> bool:
        """
        判断是否应该升级

        Args:
            old_score: 旧的C-P-I分数
            new_score: 新的C-P-I分数

        Returns:
            bool: 是否跨越了升级阈值
        """
        old_grade = cls.calculate_grade(old_score)
        new_grade = cls.calculate_grade(new_score)

        # 等级顺序: LEAD(0) < NORMAL(1) < PRIORITY(2) < LANDABLE(3)
        grade_order = {
            OpportunityGrade.LEAD: 0,
            OpportunityGrade.NORMAL: 1,
            OpportunityGrade.PRIORITY: 2,
            OpportunityGrade.LANDABLE: 3,
        }

        return grade_order[new_grade] > grade_order[old_grade]

    @classmethod
    def should_downgrade(cls, old_score: float, new_score: float) -> bool:
        """
        判断是否应该降级

        Args:
            old_score: 旧的C-P-I分数
            new_score: 新的C-P-I分数

        Returns:
            bool: 是否跨越了降级阈值
        """
        old_grade = cls.calculate_grade(old_score)
        new_grade = cls.calculate_grade(new_score)

        # 等级顺序: LEAD(0) < NORMAL(1) < PRIORITY(2) < LANDABLE(3)
        grade_order = {
            OpportunityGrade.LEAD: 0,
            OpportunityGrade.NORMAL: 1,
            OpportunityGrade.PRIORITY: 2,
            OpportunityGrade.LANDABLE: 3,
        }

        return grade_order[new_grade] < grade_order[old_grade]

    @classmethod
    def get_grade_change_reason(cls, old_score: float, new_score: float) -> str:
        """
        获取等级变更原因

        Args:
            old_score: 旧的C-P-I分数
            new_score: 新的C-P-I分数

        Returns:
            str: 变更原因描述
        """
        change = new_score - old_score
        old_grade = cls.calculate_grade(old_score)
        new_grade = cls.calculate_grade(new_score)

        if old_grade == new_grade:
            return f"分数变化: {old_score:.1f} → {new_score:.1f} ({change:+.1f}), 等级保持"

        action = "升级" if cls.should_upgrade(old_score, new_score) else "降级"
        return f"C-P-I分数{action}: {old_score:.1f} → {new_score:.1f} ({change:+.1f}), {old_grade.value} → {new_grade.value}"

    @classmethod
    def create_grade_history_entry(
        cls,
        from_grade: OpportunityGrade,
        to_grade: OpportunityGrade,
        old_score: float,
        new_score: float,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建等级变更历史记录

        Args:
            from_grade: 原等级
            to_grade: 新等级
            old_score: 旧分数
            new_score: 新分数
            reason: 变更原因（可选）

        Returns:
            Dict: 历史记录条目
        """
        return {
            'from_grade': from_grade.value if isinstance(from_grade, OpportunityGrade) else from_grade,
            'to_grade': to_grade.value if isinstance(to_grade, OpportunityGrade) else to_grade,
            'old_score': round(old_score, 2),
            'new_score': round(new_score, 2),
            'score_change': round(new_score - old_score, 2),
            'reason': reason or cls.get_grade_change_reason(old_score, new_score),
            'timestamp': datetime.utcnow().isoformat()
        }

    @classmethod
    def get_next_target_scores(cls, current_grade: OpportunityGrade) -> Tuple[Optional[float], Optional[float]]:
        """
        获取当前等级的上下目标分数

        Args:
            current_grade: 当前等级

        Returns:
            Tuple[downgrade_threshold, upgrade_threshold]:
            - downgrade_threshold: 低于此分数将降级 (None表示最低级)
            - upgrade_threshold: 达到此分数将升级 (None表示最高级)
        """
        if current_grade == OpportunityGrade.LEAD:
            # 线索: 无降级, 60分升级到普通商机
            return (None, cls.THRESHOLDS['lead_max'])
        elif current_grade == OpportunityGrade.NORMAL:
            # 普通商机: <60降级, 70分升级到重点商机
            return (cls.THRESHOLDS['lead_max'], cls.THRESHOLDS['normal_max'])
        elif current_grade == OpportunityGrade.PRIORITY:
            # 重点商机: <70降级, 85分升级到落地商机
            return (cls.THRESHOLDS['normal_min'], cls.THRESHOLDS['priority_max'])
        elif current_grade == OpportunityGrade.LANDABLE:
            # 落地商机: <85降级, 无升级
            return (cls.THRESHOLDS['landable_min'], None)
        else:
            return (None, None)

    @classmethod
    def get_grade_description(cls, grade: OpportunityGrade) -> str:
        """
        获取等级描述

        Args:
            grade: 商机等级

        Returns:
            str: 等级描述
        """
        descriptions = {
            OpportunityGrade.LEAD: "线索 - 需进一步验证市场潜力",
            OpportunityGrade.NORMAL: "普通商机 - 保持关注，定期评估",
            OpportunityGrade.PRIORITY: "重点商机 - 优先验证，重点关注",
            OpportunityGrade.LANDABLE: "落地商机 - 可执行落地，启动项目",
        }
        return descriptions.get(grade, "未知等级")
