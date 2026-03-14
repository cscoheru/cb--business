# api/opportunities.py
"""智能商机跟踪 API - 适配现有数据库结构"""

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy import select, func, cast
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
import logging

from config.database import get_db
from models.business_opportunity import BusinessOpportunity, OpportunityStatus
from api.dependencies import get_current_user_optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunities"])


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
            'potential': {'count': 0, 'avg_confidence': 0},
            'verifying': {'count': 0, 'avg_confidence': 0},
            'assessing': {'count': 0, 'avg_confidence': 0},
            'executing': {'count': 0, 'avg_confidence': 0},
        }

        for row in result:
            status = row[0]
            count = row[1]
            avg_conf = float(row[2]) if row[2] else 0.0

            if status in funnel_data:
                funnel_data[status] = {
                    'count': count,
                    'avg_confidence': round(avg_conf, 3)
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


@router.get("")
async def list_opportunities(
    status: Optional[str] = Query(None, description="筛选状态"),
    type: Optional[str] = Query(None, description="筛选类型"),
    min_confidence: Optional[float] = Query(None, description="最小置信度"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """获取商机列表"""
    try:
        # 显式选择存在的列（避免查询不存在的card_id/article_id/user_id列）
        query = select(
            BusinessOpportunity.id,
            BusinessOpportunity.title,
            BusinessOpportunity.description,
            BusinessOpportunity.status,
            BusinessOpportunity.opportunity_type,
            BusinessOpportunity.elements,
            BusinessOpportunity.ai_insights,
            BusinessOpportunity.confidence_score,
            BusinessOpportunity.last_verification_at,
            BusinessOpportunity.user_interactions,
            BusinessOpportunity.is_locked,
            BusinessOpportunity.locked_at,
            BusinessOpportunity.created_at,
            BusinessOpportunity.updated_at,
            BusinessOpportunity.archived_at,
            BusinessOpportunity.archive_reason,
        )

        # 应用状态筛选
        if status:
            query = query.where(BusinessOpportunity.status == status)

        # 应用类型筛选
        if type:
            query = query.where(BusinessOpportunity.opportunity_type == type)

        # 应用置信度筛选
        if min_confidence is not None:
            query = query.where(BusinessOpportunity.confidence_score >= min_confidence)

        # 排序
        query = query.order_by(BusinessOpportunity.created_at.desc())

        # 总数
        count_query = select(func.count()).select_from(BusinessOpportunity)
        if status:
            count_query = count_query.where(BusinessOpportunity.status == status)
        if type:
            count_query = count_query.where(BusinessOpportunity.opportunity_type == type)
        if min_confidence is not None:
            count_query = count_query.where(BusinessOpportunity.confidence_score >= min_confidence)

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        rows = result.all()

        # 转换为字典（从Row对象）
        opportunities_data = []
        for row in rows:
            opp_dict = {
                'id': str(row[0]),
                'title': row[1],
                'description': row[2],
                'status': row[3].value if hasattr(row[3], 'value') else row[3],
                'opportunity_type': row[4].value if hasattr(row[4], 'value') else row[4],
                'elements': row[5] or {},
                'ai_insights': row[6] or {},
                'confidence_score': row[7],
                'last_verification_at': row[8].isoformat() if row[8] else None,
                'user_interactions': row[9] or {},
                'is_locked': row[10],
                'locked_at': row[11].isoformat() if row[11] else None,
                'created_at': row[12].isoformat() if row[12] else None,
                'updated_at': row[13].isoformat() if row[13] else None,
                'archived_at': row[14].isoformat() if row[14] else None,
                'archive_reason': row[15],
            }
            opportunities_data.append(opp_dict)

        # 权限信息
        user_access = None
        if current_user:
            plan_tier = current_user.get('plan_tier', 'free')
            user_access = {
                'plan_tier': plan_tier,
                'plan_status': current_user.get('plan_status', 'active'),
                'accessible_statuses': _get_accessible_statuses(plan_tier)
            }

        return {
            "success": True,
            "opportunities": opportunities_data,
            "total": total,
            "skip": skip,
            "limit": limit,
            "user_access": user_access
        }

    except Exception as e:
        logger.error(f"获取商机列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{opportunity_id}")
async def get_opportunity(
    opportunity_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """获取商机详情"""
    try:
        from uuid import UUID
        from sqlalchemy import select

        # Parse the UUID string
        try:
            opportunity_uuid = UUID(opportunity_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid opportunity ID format")

        result = await db.execute(
            select(
                BusinessOpportunity.id,
                BusinessOpportunity.title,
                BusinessOpportunity.description,
                BusinessOpportunity.status,
                BusinessOpportunity.opportunity_type,
                BusinessOpportunity.elements,
                BusinessOpportunity.ai_insights,
                BusinessOpportunity.confidence_score,
                BusinessOpportunity.last_verification_at,
                BusinessOpportunity.user_interactions,
                BusinessOpportunity.is_locked,
                BusinessOpportunity.locked_at,
                BusinessOpportunity.created_at,
                BusinessOpportunity.updated_at,
                BusinessOpportunity.archived_at,
                BusinessOpportunity.archive_reason,
            ).where(
                BusinessOpportunity.id == opportunity_uuid
            )
        )
        row = result.first()

        if not row:
            raise HTTPException(status_code=404, detail="商机不存在")

        # 转换为字典
        data = {
            'id': str(row[0]),
            'title': row[1],
            'description': row[2],
            'status': row[3].value if hasattr(row[3], 'value') else row[3],
            'opportunity_type': row[4].value if hasattr(row[4], 'value') else row[4],
            'elements': row[5] or {},
            'ai_insights': row[6] or {},
            'confidence_score': row[7],
            'last_verification_at': row[8].isoformat() if row[8] else None,
            'user_interactions': row[9] or {},
            'is_locked': row[10],
            'locked_at': row[11].isoformat() if row[11] else None,
            'created_at': row[12].isoformat() if row[12] else None,
            'updated_at': row[13].isoformat() if row[13] else None,
            'archived_at': row[14].isoformat() if row[14] else None,
            'archive_reason': row[15],
        }

        # 检查权限
        status = row[3]
        is_accessible = True
        if current_user:
            plan_tier = current_user.get('plan_tier', 'free')
            accessible_statuses = _get_accessible_statuses(plan_tier)
            is_accessible = status in accessible_statuses
        else:
            # 未登录用户只能看到potential状态
            is_accessible = status == OpportunityStatus.POTENTIAL

        if not is_accessible:
            data['is_locked'] = True
            data['lock_reason'] = "此商机需要升级到Pro版查看"

        return {
            "success": True,
            "opportunity": data,
            "is_accessible": is_accessible
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取商机详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_accessible_statuses(plan_tier: str) -> List[str]:
    """根据用户计划获取可访问的状态"""
    if plan_tier == 'free':
        return ['potential']
    elif plan_tier in ['trial', 'pro']:
        return ['potential', 'verifying', 'assessing', 'executing']
    else:
        return ['potential']


def opportunity_to_dict(opp) -> Dict[str, Any]:
    """转换为API字典格式（不包含card_id/article_id）- 用于有完整对象的情况"""
    return {
        'id': str(opp.id),
        'title': opp.title,
        'description': opp.description,
        'status': opp.status.value if isinstance(opp.status, OpportunityStatus) else opp.status,
        'opportunity_type': opp.opportunity_type.value if hasattr(opp.opportunity_type, 'value') else opp.opportunity_type,
        'elements': opp.elements or {},
        'ai_insights': opp.ai_insights or {},
        'confidence_score': opp.confidence_score,
        'last_verification_at': opp.last_verification_at.isoformat() if opp.last_verification_at else None,
        'user_interactions': opp.user_interactions or {},
        'is_locked': opp.is_locked,
        'locked_at': opp.locked_at.isoformat() if opp.locked_at else None,
        'created_at': opp.created_at.isoformat() if opp.created_at else None,
        'updated_at': opp.updated_at.isoformat() if opp.updated_at else None,
        'archived_at': opp.archived_at.isoformat() if opp.archived_at else None,
        'archive_reason': opp.archive_reason,
    }
