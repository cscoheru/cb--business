# api/opportunities.py
"""商机 API - Simplified Version for Production Deployment

提供商机列表和详情查询功能。
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import uuid

from config.database import get_db
from models.business_opportunity import BusinessOpportunity, OpportunityStatus, OpportunityType, OpportunityGrade
from models.card import Card
from models.user import User
from api.dependencies import get_current_user, get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunities"])


# ============================================================================
# Specific routes (must come before parameterized routes)
# ============================================================================

@router.get("/funnel")
async def get_opportunity_funnel(
    db: AsyncSession = Depends(get_db)
):
    """获取商机漏斗数据"""
    try:
        # 查询各状态的统计数据
        result = await db.execute(
            select(
                BusinessOpportunity.status,
                func.count(BusinessOpportunity.id).label('count'),
                func.avg(BusinessOpportunity.confidence_score).label('avg_confidence')
            )
            .group_by(BusinessOpportunity.status)
        )

        funnel_data = {
            'potential': {'count': 0, 'avg_confidence': 0, 'label': '发现期'},
            'verifying': {'count': 0, 'avg_confidence': 0, 'label': '验证期'},
            'assessing': {'count': 0, 'avg_confidence': 0, 'label': '评估期'},
            'executing': {'count': 0, 'avg_confidence': 0, 'label': '执行期'},
        }

        for row in result:
            status = row[0]
            count = row[1]
            avg_conf = float(row[2]) if row[2] else 0.0

            if status in funnel_data:
                funnel_data[status] = {
                    'count': count,
                    'avg_confidence': round(avg_conf, 3),
                    'label': funnel_data[status]['label']
                }

        total = sum(s['count'] for s in funnel_data.values())

        return {
            "success": True,
            "funnel": funnel_data,
            "total": total
        }

    except Exception as e:
        logger.error(f"获取商机漏斗失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grades")
async def get_opportunity_grades(
    db: AsyncSession = Depends(get_db)
):
    """获取所有商机的等级统计"""
    try:
        result = await db.execute(
            select(
                BusinessOpportunity.grade,
                func.count(BusinessOpportunity.id).label('count'),
                func.avg(BusinessOpportunity.cpi_total_score).label('avg_score')
            )
            .where(BusinessOpportunity.grade.isnot(None))
            .group_by(BusinessOpportunity.grade)
        )

        grades = {}
        for row in result:
            grade = row[0]
            count = row[1]
            avg_score = float(row[2]) if row[2] else 0.0

            grades[grade] = {
                "count": count,
                "avg_score": round(avg_score, 2),
                "label": {
                    "lead": "线索 (<60分)",
                    "normal": "普通 (60-69分)",
                    "priority": "重点 (70-84分)",
                    "landable": "落地 (≥85分)"
                }.get(grade, grade)
            }

        return {
            "success": True,
            "grades": grades,
            "total": sum(g["count"] for g in grades.values())
        }

    except Exception as e:
        logger.error(f"获取等级统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_opportunity_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取商机统计信息"""
    try:
        # 总数
        total_result = await db.execute(
            select(func.count()).select_from(BusinessOpportunity)
        )
        total = total_result.scalar() or 0

        # 按状态统计
        status_result = await db.execute(
            select(
                BusinessOpportunity.status,
                func.count(BusinessOpportunity.id)
            )
            .group_by(BusinessOpportunity.status)
        )
        by_status = {row[0]: row[1] for row in status_result}

        # 按等级统计
        grade_result = await db.execute(
            select(
                BusinessOpportunity.grade,
                func.count(BusinessOpportunity.id)
            )
            .where(BusinessOpportunity.grade.isnot(None))
            .group_by(BusinessOpportunity.grade)
        )
        by_grade = {row[0].value: row[1] for row in grade_result}

        return {
            "success": True,
            "total": total,
            "by_status": by_status,
            "by_grade": by_grade,
            "recent_count": 5  # TODO: 实际查询最近7天新增的商机数
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# List and detail routes
# ============================================================================

@router.get("")
async def list_opportunities(
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None),
    grade: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取商机列表"""
    try:
        query = select(BusinessOpportunity)

        # 应用筛选
        if status:
            query = query.where(BusinessOpportunity.status == status)
        if type:
            query = query.where(BusinessOpportunity.opportunity_type == type)
        if min_confidence is not None:
            query = query.where(BusinessOpportunity.confidence_score >= min_confidence)
        if grade:
            query = query.where(BusinessOpportunity.grade == grade)

        # 排序
        query = query.order_by(BusinessOpportunity.created_at.desc())

        # 总数
        count_query = select(func.count()).select_from(query)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        opportunities = result.scalars().all()

        return {
            "success": True,
            "total": total,
            "opportunities": [
                {
                    "id": str(opp.id),
                    "title": opp.title,
                    "description": opp.description,
                    "status": opp.status.value if hasattr(opp.status, 'value') else opp.status,
                    "opportunity_type": opp.opportunity_type.value if hasattr(opp.opportunity_type, 'value') else opp.opportunity_type,
                    "grade": opp.grade.value if opp.grade else None,
                    "confidence_score": opp.confidence_score,
                    "cpi_total_score": opp.cpi_total_score,
                    "is_locked": opp.is_locked,
                    "created_at": opp.created_at.isoformat() if opp.created_at else None,
                    "elements": opp.elements or {},
                    "ai_insights": opp.ai_insights or {}
                }
                for opp in opportunities
            ]
        }

    except Exception as e:
        logger.error(f"获取商机列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{opportunity_id}")
async def get_opportunity(
    opportunity_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取商机详情"""
    try:
        from uuid import UUID

        # Parse the UUID string
        try:
            opportunity_uuid = UUID(opportunity_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid opportunity ID format")

        result = await db.execute(
            select(BusinessOpportunity).where(
                BusinessOpportunity.id == opportunity_uuid
            )
        )
        opp = result.scalar_one_or_none()

        if not opp:
            raise HTTPException(status_code=404, detail="商机不存在")

        return {
            "success": True,
            "opportunity": {
                "id": str(opp.id),
                "title": opp.title,
                "description": opp.description,
                "status": opp.status.value if hasattr(opp.status, 'value') else opp.status,
                "opportunity_type": opp.opportunity_type.value if hasattr(opp.opportunity_type, 'value') else opp.opportunity_type,
                "elements": opp.elements or {},
                "ai_insights": opp.ai_insights or {},
                "confidence_score": opp.confidence_score,
                "grade": opp.grade.value if opp.grade else None,
                "cpi_total_score": opp.cpi_total_score,
                "cpi_competition_score": opp.cpi_competition_score,
                "cpi_potential_score": opp.cpi_potential_score,
                "cpi_intelligence_gap_score": opp.cpi_intelligence_gap_score,
                "last_verification_at": opp.last_verification_at.isoformat() if opp.last_verification_at else None,
                "user_interactions": opp.user_interactions or {},
                "is_locked": opp.is_locked,
                "created_at": opp.created_at.isoformat() if opp.created_at else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取商机详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/from-card/{card_id}", status_code=status.HTTP_201_CREATED)
async def create_opportunity_from_card(
    card_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    从卡片创建商机 (关注为商机)

    匿名用户限制： 最多3个商机
    认证用户: 无限制
    """
    from services.opportunity_algorithm import opportunity_scorer
    from services.grade_calculator import GradeCalculator
    from pydantic import BaseModel

    class OpportunityCreateResponse(BaseModel):
        id: str
        title: str
        card_id: str
        grade: Optional[str] = None
        cpi_total_score: Optional[float] = None
        confidence_score: float
        status: str
        created_at: str

    try:
        # 飘化 card_id 为 UUID
        try:
            card_uuid = uuid.UUID(card_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的卡片ID格式"
            )

        # 装载卡片
        card = await db.get(Card, card_uuid)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="卡片不存在"
            )

        # 检查匿名用户限制
        if not current_user:
            # 匿名用户: 检查已有商机数量
            anon_opportunities_count = await db.execute(
                select(func.count()).select_from(BusinessOpportunity).where(
                    BusinessOpportunity.user_id.is_(None)
                )
            )
            count = anon_opportunities_count.scalar() or 0

            if count >= 3:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "message": "匿名用户最多只能关注3个商机",
                        "limit": 3,
                        "current": count,
                        "upgrade_required": True
                    }
                )

        # 检查是否已存在该卡片对应的商机
        existing_result = await db.execute(
            select(BusinessOpportunity).where(
                BusinessOpportunity.card_id == card_uuid,
                BusinessOpportunity.user_id == (current_user.id if current_user else None)
            )
        )
        existing_opp = existing_result.scalar_one_or_none()

        if existing_opp:
            # 已存在，返回现有商机
            return OpportunityCreateResponse(
                id=str(existing_opp.id),
                title=existing_opp.title,
                card_id=str(existing_opp.card_id),
                grade=existing_opp.grade.value if existing_opp.grade else None,
                cpi_total_score=existing_opp.cpi_total_score,
                confidence_score=existing_opp.confidence_score,
                status=existing_opp.status.value,
                created_at=existing_opp.created_at.isoformat()
            )

        # 计算 CPI 分数
        logger.info(f"🎯 创建商机: card={card_id}, user={current_user.id if current_user else 'anonymous'}")
        cpi_result = await opportunity_scorer.calculate_opportunity_score(card, db)

        # 根据分数确定等级
        grade = GradeCalculator.calculate_grade(cpi_result['total_score'])

        # 创建商机
        opportunity = BusinessOpportunity(
            title=f"商机: {card.category}",
            description=card.content.get('summary', {}).get('description', '') if card.content else '',
            status=OpportunityStatus.POTENTIAL,
            opportunity_type=OpportunityType.PRODUCT,
            card_id=card_uuid,
            user_id=current_user.id if current_user else None,
            # 皂时标记为线索
            grade=grade,
            grade_history=[],
            last_grade_change_at=datetime.utcnow(),
            last_cpi_recalc_at=datetime.utcnow(),
            # CPI 分数
            cpi_total_score=cpi_result['total_score'],
            cpi_competition_score=cpi_result['competition']['score'],
            cpi_potential_score=cpi_result['potential']['score'],
            cpi_intelligence_gap_score=cpi_result['intelligence_gap']['score'],
            # 用户交互
            user_interactions={
                "followed": True,
                "source": "card_follow",
                "followed_at": datetime.utcnow().isoformat()
            },
            # AI 分析结果
            ai_insights={
                "initial_cpi_score": cpi_result,
                "data_requirements": [],
                "verification_needs": []
            },
            confidence_score=cpi_result['total_score'] / 100,  # 蚂时转换为 0-1 范围
            # 商机要素
            elements={
                "product": {
                    "category": card.category,
                    "opportunity_score": cpi_result['total_score'],
                    "amazon_products_count": len(card.amazon_data.get('products', [])) if card.amazon_data else 0
                }
            }
        )

        db.add(opportunity)
        await db.commit()
        await db.refresh(opportunity)

        logger.info(
            f"✅ 商机创建成功: card={card_id}, opportunity={opportunity.id}, "
            f"grade={grade.value}, score={cpi_result['total_score']:.1f}"
        )

        return OpportunityCreateResponse(
            id=str(opportunity.id),
            title=opportunity.title,
            card_id=str(opportunity.card_id),
            grade=opportunity.grade.value if opportunity.grade else None,
            cpi_total_score=opportunity.cpi_total_score,
            confidence_score=opportunity.confidence_score,
            status=opportunity.status.value,
            created_at=opportunity.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建商机失败: card={card_id}, error={e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建商机失败: {str(e)}"
        )


@router.delete("/{opportunity_id}")
async def archive_opportunity(
    opportunity_id: str,
    reason: str = Query(None, description="归档原因"),
    db: AsyncSession = Depends(get_db)
):
    """归档商机"""
    try:
        from uuid import UUID

        try:
            opportunity_uuid = UUID(opportunity_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid opportunity ID format")

        result = await db.execute(
            select(BusinessOpportunity).where(
                BusinessOpportunity.id == opportunity_uuid
            )
        )
        opp = result.scalar_one_or_none()

        if not opp:
            raise HTTPException(status_code=404, detail="商机不存在")
        # 更新状态为归档
        opp.status = OpportunityStatus.ARCHIVED
        opp.archived_at = datetime.utcnow()
        opp.archive_reason = reason
        await db.commit()

        return {
            "success": True,
            "message": "商机已归档"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"归档商机失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
