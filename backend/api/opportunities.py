# api/opportunities.py
"""智能商机跟踪 API - 适配现有数据库结构

集成C-P-I 跨境商机矩阵算法系统:
- Competition (竞争度) - 40% weight
- Potential (增长潜力) - 40% weight
- Intelligence Gap (信息差/痛点) - 20% weight
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy import select, func, cast
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from config.database import get_db
from models.business_opportunity import BusinessOpportunity, OpportunityStatus, OpportunityType
from models.card import Card
from api.dependencies import get_current_user_optional
from services.opportunity_algorithm import opportunity_scorer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunities"])


@router.get("/funnel")
async def get_opportunity_funnel(
    db: AsyncSession = Depends(get_db)
):
    """获取商机漏斗数据 - 基于C-P-I评分分类"""
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
            "total": total,
            "description": "商机漏斗基于C-P-I算法: 线索发现 → 算法评估 → 数据验证 → 商机决策"
        }

    except Exception as e:
        logger.error(f"获取商机漏斗失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-from-cards")
async def generate_opportunities_from_cards(
    card_ids: Optional[List[str]] = Query(None, description="指定Card ID列表，不指定则处理所有高潜力卡片"),
    limit: int = Query(10, ge=1, le=50, description="最大生成数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    从Cards生成商机，应用C-P-I算法评分

    C-P-I算法:
    - Competition (竞争度): Top10品牌份额 × 0.7 + CPC出价 × 0.3
    - Potential (增长潜力): 关键词增长 × 0.6 + 评论速度 × 0.4
    - Intelligence Gap (信息差): 负面评论情感 / 产品特征一致性
    """
    try:
        from uuid import UUID

        # 构建查询
        query = select(Card).where(Card.amazon_data.isnot(None))

        if card_ids:
            # 过滤指定的cards
            card_uuids = [UUID(cid) for cid in card_ids]
            query = query.where(Card.id.in_(card_uuids))
        else:
            # 默认选择高opportunity_score的卡片
            query = query.order_by(Card.content['summary']['opportunity_score'].astext.cast(Integer).desc())

        query = query.limit(limit)
        result = await db.execute(query)
        cards = result.scalars().all()

        generated_opportunities = []
        for card in cards:
            # 应用C-P-I算法计算商机分数
            try:
                score_result = await opportunity_scorer.calculate_opportunity_score(card, db)

                # 创建商机记录
                opportunity = BusinessOpportunity(
                    title=f"[{score_result['opportunity_type']}] {card.content.get('summary', {}).get('title', card.category)}",
                    description=f"基于C-P-I算法生成的商机: 综合分数 {score_result['total_score']}",
                    status=OpportunityStatus.POTENTIAL,
                    opportunity_type=OpportunityType.PRODUCT,
                    card_id=card.id,
                    confidence_score=score_result['total_score'] / 100,  # 转换为0-1范围
                    elements={
                        'product': {
                            'category': card.category,
                            'amazon_products_count': len(card.amazon_data.get('products', [])),
                            'top_products': [
                                {
                                    'asin': p.get('asin'),
                                    'title': p.get('title'),
                                    'price': p.get('price'),
                                    'rating': p.get('rating')
                                }
                                for p in card.amazon_data.get('products', [])[:5]
                            ]
                        }
                    },
                    ai_insights={
                        'cpi_algorithm': {
                            'total_score': score_result['total_score'],
                            'competition': score_result['competition'],
                            'potential': score_result['potential'],
                            'intelligence_gap': score_result['intelligence_gap'],
                            'opportunity_type': score_result['opportunity_type'],
                            'calculated_at': score_result['calculated_at']
                        },
                        'why_opportunity': f"C-P-I综合评分{score_result['total_score']}分，属于{score_result['opportunity_type']}商机",
                        'verification_needs': [
                            '验证竞争度数据的准确性',
                            '监控增长趋势的变化',
                            '深入分析用户痛点评论'
                        ],
                        'confidence_history': []
                    }
                )

                db.add(opportunity)
                await db.flush()  # 获取ID但不提交

                generated_opportunities.append({
                    'card_id': str(card.id),
                    'card_title': card.content.get('summary', {}).get('title', card.category),
                    'opportunity_id': str(opportunity.id),
                    'opportunity_type': score_result['opportunity_type'],
                    'cpi_scores': score_result,
                    'confidence_score': opportunity.confidence_score
                })

                logger.info(f"生成商机: {opportunity.title} - C-P-I分数: {score_result['total_score']}")

            except Exception as e:
                logger.error(f"为Card {card.id} 计算C-P-I分数失败: {e}")
                continue

        # 提交所有变更
        await db.commit()

        return {
            "success": True,
            "generated_count": len(generated_opportunities),
            "opportunities": generated_opportunities,
            "message": f"成功从{len(cards)}张卡片中生成{len(generated_opportunities)}个商机，已应用C-P-I算法评分"
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"生成商机失败: {e}")
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


@router.post("/{opportunity_id}/recalculate-score")
async def recalculate_opportunity_score(
    opportunity_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    重新计算商机的C-P-I分数

    当关联的Card数据更新时，调用此接口动态更新商机分数
    实现商机分数随验证数据的累积而变化
    """
    try:
        from uuid import UUID

        # 解析UUID
        try:
            opportunity_uuid = UUID(opportunity_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid opportunity ID format")

        # 查询商机
        result = await db.execute(
            select(BusinessOpportunity).where(BusinessOpportunity.id == opportunity_uuid)
        )
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            raise HTTPException(status_code=404, detail="商机不存在")

        # 检查是否有关联的Card
        if not opportunity.card_id:
            raise HTTPException(status_code=400, detail="此商机没有关联的Card，无法重新计算分数")

        # 查询关联的Card
        card_result = await db.execute(
            select(Card).where(Card.id == opportunity.card_id)
        )
        card = card_result.scalar_one_or_none()

        if not card:
            raise HTTPException(status_code=404, detail="关联的Card不存在")

        # 保存旧分数用于历史记录
        old_score = opportunity.confidence_score

        # 重新计算C-P-I分数
        new_score_result = await opportunity_scorer.calculate_opportunity_score(card, db)
        new_confidence = new_score_result['total_score'] / 100  # 转换为0-1范围

        # 更新商机
        opportunity.confidence_score = new_confidence
        opportunity.last_verification_at = datetime.utcnow()

        # 更新AI insights中的C-P-I算法数据
        if 'cpi_algorithm' not in opportunity.ai_insights:
            opportunity.ai_insights['cpi_algorithm'] = {}

        opportunity.ai_insights['cpi_algorithm'] = {
            'total_score': new_score_result['total_score'],
            'competition': new_score_result['competition'],
            'potential': new_score_result['potential'],
            'intelligence_gap': new_score_result['intelligence_gap'],
            'opportunity_type': new_score_result['opportunity_type'],
            'calculated_at': new_score_result['calculated_at']
        }

        # 添加置信度变更历史
        opportunity.add_confidence_history(
            old_score=old_score,
            new_score=new_confidence,
            data_source='cpi_algorithm_recalculation',
            reasoning=f"C-P-I算法重新计算: {new_score_result['opportunity_type']} - 综合分数{new_score_result['total_score']}"
        )

        # 检查是否应该自动演进状态
        new_status = opportunity.should_auto_evolve()
        status_changed = False
        if new_status:
            old_status = opportunity.status
            opportunity.transition_to(new_status, reason=f"C-P-I分数达到{new_score_result['total_score']}，自动演进")
            status_changed = True
            logger.info(f"商机 {opportunity.id} 从 {old_status} 自动演进到 {new_status}")

        await db.commit()

        return {
            "success": True,
            "opportunity_id": str(opportunity.id),
            "old_confidence": round(old_score, 3),
            "new_confidence": round(new_confidence, 3),
            "confidence_change": round(new_confidence - old_score, 3),
            "cpi_scores": new_score_result,
            "status_changed": status_changed,
            "new_status": new_status.value if new_status else opportunity.status.value,
            "message": f"C-P-I分数已更新: {old_score:.3f} → {new_confidence:.3f}"
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"重新计算商机分数失败: {e}")
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
