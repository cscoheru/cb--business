# api/opportunities.py
"""产品机会分析 API"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any, Optional
import logging

from analyzer.scoring import OpportunityScoringEngine, analyze_product_opportunity
from crawler.products.amazon_bestsellers import AmazonBestSellersCrawler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunities"])


@router.post("/score")
async def score_product(
    product_data: Dict[str, Any],
    include_trends: bool = Query(False, description="是否包含 Google Trends 数据")
):
    """
    对单个产品进行机会评分

    请求体示例:
    {
        "title": "Product Name",
        "price": 29.99,
        "rating": 4.5,
        "reviews_count": 1234,
        "rank": 15,
        "sold_count": 500,
        "is_prime": true,
        "is_amazon_choice": false
    }
    """
    try:
        engine = OpportunityScoringEngine()
        score_result = engine.score_amazon_product(product_data)

        return {
            "success": True,
            "product_title": product_data.get("title", ""),
            "score": score_result.to_dict(),
        }

    except Exception as e:
        logger.error(f"评分失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score/batch")
async def score_products_batch(
    products: List[Dict[str, Any]]
):
    """
    批量评分产品

    请求体示例:
    {
        "products": [
            {"title": "Product 1", "price": 29.99, ...},
            {"title": "Product 2", "price": 49.99, ...}
        ]
    }
    """
    try:
        engine = OpportunityScoringEngine()
        results = engine.batch_score_products(products)

        return {
            "success": True,
            "count": len(results),
            "products": results,
        }

    except Exception as e:
        logger.error(f"批量评分失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze")
async def analyze_market_opportunities(
    country: str = Query("us", description="国家代码"),
    category: str = Query(None, description="产品分类"),
    limit: int = Query(20, ge=1, le=100, description="分析产品数量")
):
    """
    分析市场机会

    综合 Amazon Best Sellers 和 AI 评分，发现高机会产品
    """
    try:
        # 1. 获取 Amazon Best Sellers
        async with AmazonBestSellersCrawler() as crawler:
            amazon_products = await crawler.fetch_bestsellers(
                country=country,
                category=category,
                max_products=limit
            )

        if not amazon_products:
            return {
                "success": False,
                "message": "未能获取产品数据",
                "opportunities": []
            }

        # 2. 批量评分
        engine = OpportunityScoringEngine()
        products_data = [p.to_dict() for p in amazon_products]
        scored_products = engine.batch_score_products(products_data)

        # 3. 筛选高机会产品 (分数 > 60)
        high_opportunities = [
            p for p in scored_products
            if p["opportunity_score"]["total_score"] > 60
        ]

        # 4. 生成报告
        report = {
            "success": True,
            "country": country.upper(),
            "category": category or "all",
            "analyzed_at": None,  # Will be set below
            "total_products_analyzed": len(scored_products),
            "high_opportunity_count": len(high_opportunities),
            "average_score": sum(p["opportunity_score"]["total_score"] for p in scored_products) / len(scored_products) if scored_products else 0,
            "top_opportunities": high_opportunities[:10],
        }

        return report

    except Exception as e:
        logger.error(f"市场机会分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def generate_opportunity_report(
    country: str = Query("us", description="国家代码"),
    min_score: float = Query(60, ge=0, le=100, description="最小机会评分")
):
    """
    生成产品机会报告

    返回详细的市场分析报告，包括:
    - 高机会产品列表
    - 评分分布统计
    - 关键洞察
    """
    try:
        # 获取并评分产品
        async with AmazonBestSellersCrawler() as crawler:
            products = await crawler.fetch_bestsellers(
                country=country,
                category="electronics",
                max_products=50
            )

        engine = OpportunityScoringEngine()
        products_data = [p.to_dict() for p in products]
        scored = engine.batch_score_products(products_data)

        # 筛选高机会产品
        opportunities = [p for p in scored if p["opportunity_score"]["total_score"] >= min_score]

        # 生成统计
        score_ranges = {
            "90-100": 0,
            "80-89": 0,
            "70-79": 0,
            "60-69": 0,
            "below_60": 0,
        }

        for product in scored:
            score = product["opportunity_score"]["total_score"]
            if score >= 90:
                score_ranges["90-100"] += 1
            elif score >= 80:
                score_ranges["80-89"] += 1
            elif score >= 70:
                score_ranges["70-79"] += 1
            elif score >= 60:
                score_ranges["60-69"] += 1
            else:
                score_ranges["below_60"] += 1

        # 提取关键洞察
        all_recommendations = []
        all_risk_factors = []

        for product in opportunities[:20]:
            all_recommendations.extend(product["opportunity_score"]["recommendations"])
            all_risk_factors.extend(product["opportunity_score"]["risk_factors"])

        # 统计最常见的建议和风险
        from collections import Counter
        top_recommendations = [r for r, _ in Counter(all_recommendations).most_common(5)]
        top_risks = [r for r, _ in Counter(all_risk_factors).most_common(5)]

        return {
            "success": True,
            "country": country.upper(),
            "min_score": min_score,
            "summary": {
                "total_analyzed": len(scored),
                "high_opportunities": len(opportunities),
                "score_distribution": score_ranges,
                "average_score": sum(p["opportunity_score"]["total_score"] for p in scored) / len(scored) if scored else 0,
            },
            "top_recommendations": top_recommendations,
            "top_risk_factors": top_risks,
            "opportunities": opportunities[:10],
        }

    except Exception as e:
        logger.error(f"报告生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/score/distribution")
async def get_score_distribution(
    country: str = Query("us", description="国家代码")
):
    """获取评分分布统计"""
    try:
        async with AmazonBestSellersCrawler() as crawler:
            products = await crawler.fetch_bestsellers(
                country=country,
                category="electronics",
                max_products=50
            )

        engine = OpportunityScoringEngine()
        products_data = [p.to_dict() for p in products]
        scored = engine.batch_score_products(products_data)

        # 计算分布
        scores = [p["opportunity_score"]["total_score"] for p in scored]

        if not scores:
            return {
                "success": True,
                "message": "无产品数据",
                "distribution": {}
            }

        # 统计各维度平均值
        avg_demand = sum(p["opportunity_score"]["demand_score"] for p in scored) / len(scored)
        avg_competition = sum(p["opportunity_score"]["competition_score"] for p in scored) / len(scored)
        avg_profitability = sum(p["opportunity_score"]["profitability_score"] for p in scored) / len(scored)
        avg_trend = sum(p["opportunity_score"]["trend_score"] for p in scored) / len(scored)
        avg_quality = sum(p["opportunity_score"]["quality_score"] for p in scored) / len(scored)

        return {
            "success": True,
            "country": country.upper(),
            "total_products": len(scored),
            "average_scores": {
                "total": sum(scores) / len(scores),
                "demand": avg_demand,
                "competition": avg_competition,
                "profitability": avg_profitability,
                "trend": avg_trend,
                "quality": avg_quality,
            },
            "score_ranges": {
                "90-100": len([s for s in scores if s >= 90]),
                "80-89": len([s for s in scores if 80 <= s < 90]),
                "70-79": len([s for s in scores if 70 <= s < 80]),
                "60-69": len([s for s in scores if 60 <= s < 70]),
                "below_60": len([s for s in scores if s < 60]),
            },
        }

    except Exception as e:
        logger.error(f"获取评分分布失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 智能商机跟踪系统 API (Smart Opportunity System)
# ============================================================================

from fastapi import Depends, BackgroundTasks, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

from sqlalchemy import select, desc
from config.database import AsyncSessionLocal, get_db
from models.business_opportunity import (
    BusinessOpportunity, DataCollectionTask,
    OpportunityStatus, OpportunityType, TaskStatus, TaskPriority
)
from models.user import User
from services.permission_service import PermissionService
from utils.auth import verify_access_token
import uuid as uuid_lib

# Optional authentication (allows unauthenticated access)
security = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSessionLocal = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns None if not authenticated
    Used for endpoints that work for both authenticated and unauthenticated users
    """
    if not credentials:
        return None

    token = credentials.credentials
    payload = verify_access_token(token)

    if payload is None:
        return None

    user_id_str = payload.get("sub")
    if user_id_str is None:
        return None

    try:
        user_id = uuid_lib.UUID(user_id_str)
    except ValueError:
        return None

    user = await db.get(User, user_id)
    return user


# Request/Response Models
class OpportunityDiscoveryRequest(BaseModel):
    """商机发现请求"""
    signal: Dict[str, Any] = Field(..., description="原始信号数据")
    source: str = Field(default="manual", description="信号来源")
    auto_collect: bool = Field(default=True, description="是否自动启动数据采集")


class OpportunityUpdateRequest(BaseModel):
    """商机更新请求"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    elements: Optional[Dict[str, Any]] = None


class UserFeedbackRequest(BaseModel):
    """用户反馈请求"""
    feedback: str = Field(..., description="用户反馈内容")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分 1-5")


class UserNotesRequest(BaseModel):
    """用户笔记请求"""
    notes: str = Field(..., description="用户笔记")


async def start_data_collection(opportunity_id: UUID, data_requirements: List[Dict], db: AsyncSessionLocal):
    """后台任务：启动数据采集"""
    try:
        # TODO: 实现OpenClaw客户端
        # from services.openclaw_client import OpenClawClient
        # client = OpenClawClient()

        for req in data_requirements:
            task = DataCollectionTask(
                opportunity_id=opportunity_id,
                task_type=req.get('data_needed', {}).get('type', 'generic'),
                priority=TaskPriority(req.get('priority', 'medium')),
                ai_request=req
            )

            db.add(task)
            await db.commit()

            # TODO: 提交给OpenClaw
            # await client.submit_collection_task(str(task.id), req)

            logger.info(f"📤 创建采集任务: {req.get('question', 'N/A')}")

        # await client.close()

    except Exception as e:
        logger.error(f"数据采集启动失败: {e}")


@router.post("/discover", response_model=Dict[str, Any])
async def discover_opportunity(
    request: OpportunityDiscoveryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_optional_user),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    发现新商机

    从原始信号中识别商机，创建BusinessOpportunity记录

    权限: 需要认证 (Trial/Pro用户可创建商机，Free用户受限)
    """
    try:
        # 权限检查：需要认证
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail={
                    'code': 'AUTH_REQUIRED',
                    'message': '请先登录后再创建商机'
                }
            )

        # Free用户: 检查每日配额
        if current_user.plan_tier == 'free':
            permission_service = PermissionService(db)
            # TODO: 检查每日创建配额
            pass

        # 使用AI分析器分析信号
        from services.ai_opportunity_analyzer import AIOpportunityAnalyzer
        analyzer = AIOpportunityAnalyzer()
        opportunity_data = await analyzer.analyze_signal(request.signal)

        # 如果AI判断不是商机，返回提示
        if not opportunity_data:
            return {
                'success': False,
                'message': 'AI分析后判断此信号不是有价值的商机',
                'opportunity': None
            }

        # 创建商机对象
        opportunity = BusinessOpportunity(
            title=opportunity_data.get('title'),
            description=opportunity_data.get('description'),
            opportunity_type=OpportunityType(opportunity_data.get('opportunity_type', 'product')),
            status=OpportunityStatus.POTENTIAL,
            elements=opportunity_data.get('elements', {}),
            ai_insights=opportunity_data.get('ai_insights', {}),
            confidence_score=opportunity_data.get('confidence_score', 0.5)
        )

        # 保存到数据库
        db.add(opportunity)
        await db.commit()
        await db.refresh(opportunity)

        logger.info(f"🎯 发现新商机: {opportunity.title} (置信度: {opportunity.confidence_score:.0%})")

        # 如果有数据需求，后台启动验证
        data_requirements = opportunity.ai_insights.get('data_requirements', [])
        if data_requirements and request.auto_collect:
            background_tasks.add_task(start_data_collection, opportunity.id, data_requirements, db)

        return {
            'success': True,
            'opportunity': opportunity.to_dict(),
            'message': f"发现{opportunity.opportunity_type.value}类型商机"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"商机发现失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=Dict[str, Any])
async def list_opportunities(
    status: Optional[str] = Query(None, description="按状态筛选"),
    type: Optional[str] = Query(None, description="按类型筛选"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1, description="最低置信度"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取商机列表

    权限规则:
    - 未登录: 只显示potential状态商机
    - Free用户: 只显示potential状态商机
    - Trial用户: 显示所有商机（试用期内）
    - Pro用户: 显示所有商机
    """
    try:
        # 初始化权限服务
        permission_service = PermissionService(db)

        # 构建查询 - 根据用户权限筛选
        if not current_user or current_user.plan_tier == 'free':
            # Free/unauth: 只显示potential阶段
            query = select(BusinessOpportunity).where(
                BusinessOpportunity.status == OpportunityStatus.POTENTIAL
            )
        elif current_user.plan_tier == 'trial':
            # Trial: 检查是否过期
            if await permission_service._is_trial_expired(current_user):
                # 过期：只显示potential
                query = select(BusinessOpportunity).where(
                    BusinessOpportunity.status == OpportunityStatus.POTENTIAL
                )
            else:
                # 有效：显示所有非归档商机
                query = select(BusinessOpportunity).where(
                    BusinessOpportunity.status != OpportunityStatus.ARCHIVED
                )
        else:
            # Pro: 显示所有非归档商机
            query = select(BusinessOpportunity).where(
                BusinessOpportunity.status != OpportunityStatus.ARCHIVED
            )

        # 应用筛选
        if status:
            try:
                status_enum = OpportunityStatus(status)
                query = query.where(BusinessOpportunity.status == status_enum)
            except ValueError:
                pass

        if type:
            try:
                type_enum = OpportunityType(type)
                query = query.where(BusinessOpportunity.opportunity_type == type_enum)
            except ValueError:
                pass

        if min_confidence is not None:
            query = query.where(BusinessOpportunity.confidence_score >= min_confidence)

        # 排序和分页
        query = query.order_by(desc(BusinessOpportunity.created_at))
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        opportunities = result.scalars().all()

        # 获取用户权限信息
        user_access = None
        if current_user:
            user_access = {
                'plan_tier': current_user.plan_tier,
                'plan_status': current_user.plan_status,
                'trial_ends_at': current_user.trial_ends_at.isoformat() if current_user.trial_ends_at else None,
                'is_trial_expired': await permission_service._is_trial_expired(current_user) if current_user.plan_tier == 'trial' else False
            }

        # 获取总数
        count_query = select(BusinessOpportunity.id).where(
            BusinessOpportunity.status != OpportunityStatus.ARCHIVED
        )
        total_result = await db.execute(count_query)
        total = len(total_result.all())

        return {
            'success': True,
            'total': total,
            'count': len(opportunities),
            'user_access': user_access,
            'opportunities': [opp.to_dict() for opp in opportunities]
        }

    except Exception as e:
        logger.error(f"获取商机列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/funnel", response_model=Dict[str, Any])
async def get_opportunity_funnel(
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取商机漏斗数据

    权限规则:
    - 未登录/Free: 只返回potential阶段数据
    - Trial/Pro: 返回所有阶段数据
    """
    try:
        permission_service = PermissionService(db)

        # 确定用户可访问的状态
        if not current_user or current_user.plan_tier == 'free':
            # Free/unauth: 只显示potential
            accessible_statuses = [OpportunityStatus.POTENTIAL]
        elif current_user.plan_tier == 'trial':
            # Trial: 检查是否过期
            if await permission_service._is_trial_expired(current_user):
                accessible_statuses = [OpportunityStatus.POTENTIAL]
            else:
                accessible_statuses = list(OpportunityStatus)
        else:
            # Pro: 所有状态
            accessible_statuses = list(OpportunityStatus)

        funnel = {}

        for status in accessible_statuses:
            result = await db.execute(
                select(BusinessOpportunity).where(BusinessOpportunity.status == status)
            )
            opps = result.scalars().all()
            count = len(opps)
            avg_confidence = sum(opp.confidence_score for opp in opps) / len(opps) if opps else 0

            funnel[status.value] = {
                'count': count,
                'avg_confidence': round(avg_confidence, 2)
            }

        # 添加用户访问信息
        user_access = None
        if current_user:
            user_access = {
                'plan_tier': current_user.plan_tier,
                'accessible_statuses': [s.value for s in accessible_statuses],
                'trial_expired': await permission_service._is_trial_expired(current_user) if current_user.plan_tier == 'trial' else False
            }

        return {
            'success': True,
            'funnel': funnel,
            'user_access': user_access
        }

    except Exception as e:
        logger.error(f"获取漏斗数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{opportunity_id}", response_model=Dict[str, Any])
async def get_opportunity(
    opportunity_id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取商机详情

    权限规则:
    - 未登录: 只能查看potential状态商机
    - Free用户: 只能查看potential状态商机
    - Trial用户: 可查看所有商机（试用期内）
    - Pro用户: 可查看所有商机
    """
    try:
        result = await db.execute(
            select(BusinessOpportunity).where(BusinessOpportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            raise HTTPException(status_code=404, detail="商机不存在")

        # 权限检查
        permission_service = PermissionService(db)
        access = await permission_service.get_opportunity_access(current_user, opportunity)

        # 检查查看权限
        if not access.get('can_view', False):
            raise HTTPException(
                status_code=403 if access.get('access_level') != 'denied' else 401,
                detail={
                    'code': 'ACCESS_DENIED',
                    'message': access.get('reason', '无权限访问此商机'),
                    'access_level': access.get('access_level'),
                    'upgrade_required': access.get('upgrade_required', False)
                }
            )

        # 获取关联的数据采集任务
        tasks_result = await db.execute(
            select(DataCollectionTask)
            .where(DataCollectionTask.opportunity_id == opportunity_id)
            .order_by(DataCollectionTask.created_at.desc())
        )
        tasks = tasks_result.scalars().all()

        response_data = {
            'success': True,
            'opportunity': opportunity.to_dict(),
            'data_collection_tasks': [task.to_dict() for task in tasks],
            'access': access
        }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取商机详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{opportunity_id}/save", response_model=Dict[str, Any])
async def toggle_save_opportunity(
    opportunity_id: str,
    db: AsyncSessionLocal = Depends(get_db)
):
    """收藏/取消收藏商机"""
    try:
        result = await db.execute(
            select(BusinessOpportunity).where(BusinessOpportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            raise HTTPException(status_code=404, detail="商机不存在")

        if not opportunity.user_interactions:
            opportunity.user_interactions = {}

        current_saved = opportunity.user_interactions.get('saved', False)
        opportunity.user_interactions['saved'] = not current_saved

        await db.commit()

        return {
            'success': True,
            'saved': not current_saved,
            'message': '已收藏' if not current_saved else '已取消收藏'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"收藏操作失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{opportunity_id}/feedback", response_model=Dict[str, Any])
async def submit_feedback(
    opportunity_id: str,
    request: UserFeedbackRequest,
    db: AsyncSessionLocal = Depends(get_db)
):
    """提交用户反馈"""
    try:
        result = await db.execute(
            select(BusinessOpportunity).where(BusinessOpportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            raise HTTPException(status_code=404, detail="商机不存在")

        if not opportunity.user_interactions:
            opportunity.user_interactions = {}

        opportunity.user_interactions['feedback'] = request.feedback
        if request.rating:
            opportunity.user_interactions['rating'] = request.rating
        opportunity.user_interactions['feedbacked_at'] = datetime.utcnow().isoformat()

        await db.commit()

        return {
            'success': True,
            'message': '反馈已提交'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交反馈失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{opportunity_id}", response_model=Dict[str, Any])
async def archive_opportunity(
    opportunity_id: str,
    reason: Optional[str] = Query(None, description="归档原因"),
    db: AsyncSessionLocal = Depends(get_db)
):
    """归档商机"""
    try:
        result = await db.execute(
            select(BusinessOpportunity).where(BusinessOpportunity.id == opportunity_id)
        )
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            raise HTTPException(status_code=404, detail="商机不存在")

        opportunity.transition_to(OpportunityStatus.ARCHIVED, reason)
        await db.commit()

        return {
            'success': True,
            'message': '商机已归档'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"归档商机失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
