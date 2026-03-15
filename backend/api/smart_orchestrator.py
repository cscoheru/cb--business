# api/smart_orchestrator.py
"""智能编排服务API - Smart Orchestrator Service

协调AI分析、OpenClaw数据采集和商机状态管理的中心枢纽。

主要端点:
- POST /api/v1/smart-orchestrator/signal - 处理新信号，创建商机
- POST /api/v1/smart-orchestrator/callback - OpenClaw采集完成回调
- POST /api/v1/smart-orchestrator/funnel/check - 手动触发漏斗检查
- GET /api/v1/smart-orchestrator/stats - 获取系统统计信息
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from sqlalchemy import select
from config.database import AsyncSessionLocal, get_db
from services.smart_orchestrator import get_orchestrator
from services.signal_recognition import SignalRecognitionEngine
from models.business_opportunity import BusinessOpportunity, OpportunityStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/smart-orchestrator", tags=["smart-orchestrator"])


# ============================================================================
# Request/Response Models
# ============================================================================

class SignalRequest(BaseModel):
    """信号请求 - 用于创建新商机"""
    signal_type: str = Field(..., description="信号类型: article, keyword, product, manual")
    title: str = Field(..., description="信号标题")
    description: Optional[str] = Field(None, description="信号描述")
    source: str = Field(..., description="信号来源")
    url: Optional[str] = Field(None, description="相关URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    auto_collect: bool = Field(True, description="是否自动启动数据采集")


class SignalResponse(BaseModel):
    """信号处理响应"""
    success: bool
    opportunity_id: Optional[str] = None
    message: str
    opportunity_data: Optional[Dict[str, Any]] = None


class CallbackRequest(BaseModel):
    """OpenClaw采集完成回调"""
    request_id: str = Field(..., description="原始请求ID")
    status: str = Field(..., description="采集状态: completed, failed, partial")
    result: Optional[Dict[str, Any]] = Field(None, description="采集结果数据")
    error: Optional[Dict[str, Any]] = Field(None, description="错误信息")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FunnelCheckResponse(BaseModel):
    """漏斗检查响应"""
    success: bool
    checked_count: int
    evolved_count: int
    message: str


class StatsResponse(BaseModel):
    """系统统计响应"""
    total_opportunities: int
    status_distribution: Dict[str, int]
    total_tasks: int
    completed_tasks: int
    task_completion_rate: float


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/signal", response_model=SignalResponse)
async def process_signal(
    request: SignalRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    处理新信号，可能创建新商机

    工作流程:
    1. 接收新信号（文章、关键词、产品、手动输入等）
    2. AI分析信号，判断是否为商机
    3. 如果是商机，创建BusinessOpportunity记录
    4. 如果有数据需求，自动启动数据采集
    5. 返回创建的商机信息

    示例:
    ```json
    {
      "signal_type": "article",
      "title": "Amazon推出新的B2B平台",
      "description": "文章内容...",
      "source": "techcrunch",
      "url": "https://techcrunch.com/...",
      "auto_collect": true
    }
    ```
    """
    try:
        orchestrator = get_orchestrator()

        # 构建信号数据
        signal_data = {
            "type": request.signal_type,
            "title": request.title,
            "description": request.description or "",
            "source": request.source,
            "url": request.url,
            "metadata": request.metadata,
            "received_at": datetime.utcnow().isoformat()
        }

        logger.info(f"📥 收到信号: {request.title} (类型: {request.signal_type})")

        # 处理信号
        opportunity = await orchestrator.process_signal(
            signal_data,
            db,
            auto_collect=request.auto_collect
        )

        if opportunity:
            return SignalResponse(
                success=True,
                opportunity_id=str(opportunity.get('id')),
                message="成功创建商机",
                opportunity_data=opportunity
            )
        else:
            return SignalResponse(
                success=False,
                message="AI判断不是商机或处理失败"
            )

    except Exception as e:
        logger.error(f"处理信号失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/callback")
async def openclaw_callback(
    request: CallbackRequest,
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    OpenClaw采集完成回调

    当OpenClaw完成数据采集后，调用此端点通知系统。

    工作流程:
    1. 接收采集结果
    2. 查找对应的DataCollectionTask
    3. 更新任务状态和结果
    4. 如果成功，AI分析新数据并更新商机置信度
    5. 检查是否需要更多数据或应该演进状态

    示例:
    ```json
    {
      "request_id": "req-123456",
      "status": "completed",
      "result": {
        "competition_data": {...},
        "price_analysis": {...}
      }
    }
    ```
    """
    try:
        orchestrator = get_orchestrator()

        logger.info(f"📬 收到OpenClaw回调: {request.request_id} (状态: {request.status})")

        # 构建回调数据
        callback_data = {
            "request_id": request.request_id,
            "status": request.status,
            "result": request.result,
            "error": request.error,
            "metadata": request.metadata,
            "received_at": datetime.utcnow().isoformat()
        }

        # 处理回调
        await orchestrator.on_collection_complete(callback_data, db)

        return {
            "success": True,
            "message": "回调处理成功"
        }

    except Exception as e:
        logger.error(f"处理回调失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/funnel/check", response_model=FunnelCheckResponse)
async def check_funnel(
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    手动触发漏斗检查

    检查所有商机的状态，执行自动演进。

    通常由定时任务自动执行，此端点用于手动触发。

    演进规则:
    - verifying → assessing: 置信度 >= 0.7 且所有数据采集完成
    - assessing → executing: 置信度 >= 0.85 且可行性报告通过
    """
    try:
        orchestrator = get_orchestrator()

        logger.info("🔄 手动触发漏斗检查")

        # 获取检查前的商机数量
        before_result = await db.execute(
            select(BusinessOpportunity).where(
                BusinessOpportunity.status.in_([
                    OpportunityStatus.VERIFYING,
                    OpportunityStatus.ASSESSING
                ])
            )
        )
        before_count = len(before_result.scalars().all())

        # 执行漏斗管理
        await orchestrator.manage_funnel(db)

        # 获取检查后的商机数量
        after_result = await db.execute(
            select(BusinessOpportunity).where(
                BusinessOpportunity.status.in_([
                    OpportunityStatus.VERIFYING,
                    OpportunityStatus.ASSESSING
                ])
            )
        )
        after_count = len(after_result.scalars().all())

        evolved_count = before_count - after_count

        return FunnelCheckResponse(
            success=True,
            checked_count=before_count,
            evolved_count=evolved_count,
            message=f"检查完成，{evolved_count}个商机已演进"
        )

    except Exception as e:
        logger.error(f"漏斗检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_statistics(
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    获取智能编排系统统计信息

    返回:
    - 总商机数
    - 各状态商机分布
    - 数据采集任务统计
    - 任务完成率
    """
    try:
        orchestrator = get_orchestrator()

        stats = await orchestrator.get_statistics(db)

        return StatsResponse(**stats)

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals")
async def scan_signals(
    limit: int = 20,
    include_favorited: bool = True,
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    扫描所有线索，识别高潜力商机信号

    从Cards表和用户收藏中扫描，应用C-P-I算法识别高潜力信号。

    参数:
    - limit: 最大返回数量 (默认: 20)
    - include_favorited: 是否优先包含用户收藏 (默认: true)

    返回:
    高潜力商机信号列表，按优先级排序
    """
    try:
        from services.signal_recognition import SignalRecognitionEngine

        engine = SignalRecognitionEngine()
        signals = await engine.scan_leads(
            db=db,
            include_favorited=include_favorited,
            limit=limit
        )

        return {
            "success": True,
            "count": len(signals),
            "signals": signals
        }

    except Exception as e:
        logger.error(f"信号扫描失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
