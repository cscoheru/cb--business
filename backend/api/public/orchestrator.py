# api/public/orchestrator.py
"""AI Orchestrator 公共 API

提供 AI 驱动的商机分析服务
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import time

from config.database import get_db
from api.public.dependencies import get_api_key, UsageTracker
from models.api_key import APIKey
from services.ai_orchestrator import ai_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/public/orchestrator", tags=["public-orchestrator"])


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalyzeRequest(BaseModel):
    """分析请求"""
    category: str = Field(..., description="产品类目", example="phone_cases")
    amazon_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Amazon 产品数据 (价格、评分、评论等)"
    )
    google_trends_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Google Trends 数据 (趋势分数、增长率等)"
    )
    depth_level: str = Field(
        "standard",
        description="分析深度: standard (标准), deep (深度)",
        pattern="^(standard|deep)$"
    )


class AnalyzeResponse(BaseModel):
    """分析响应"""
    success: bool = True
    category: str
    initial_score: Dict[str, Any]
    data_gaps: List[Dict[str, Any]]
    data_gaps_filled: List[Dict[str, Any]]
    final_score: Dict[str, Any]
    confidence_improvement: float
    execution_time_ms: int
    tier: str


class BatchAnalyzeRequest(BaseModel):
    """批量分析请求"""
    items: List[AnalyzeRequest] = Field(..., max_items=10, description="最多10个")


class BatchAnalyzeResponse(BaseModel):
    """批量分析响应"""
    success: bool = True
    results: List[AnalyzeResponse]
    total: int
    execution_time_ms: int


class OrchestratorStatus(BaseModel):
    """Orchestrator 状态"""
    status: str
    version: str
    capabilities: List[str]
    uptime_seconds: int


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_opportunity(
    request_body: AnalyzeRequest,
    request: Request,
    api_key: APIKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    分析商机 - AI 驱动的智能分析

    返回:
    - initial_score: 初始 C-P-I 评分
    - data_gaps: 识别的数据缺口
    - data_gaps_filled: 补齐的数据 (如调用 OpenClaw)
    - final_score: 最终 C-P-I 评分
    - confidence_improvement: 置信度提升

    **订阅要求**: Developer 或更高
    """
    tracker = UsageTracker(request)

    try:
        # 构建临时 Card 对象用于分析
        from models.card import Card
        temp_card = Card(
            category=request_body.category,
            amazon_data=request_body.amazon_data or {},
            content={
                "google_trends": request_body.google_trends_data,
                "depth_level": request_body.depth_level
            }
        )

        # 调用 AI Orchestrator
        result = await ai_orchestrator.analyze_and_verify(temp_card, db)

        response = AnalyzeResponse(
            success=True,
            category=request_body.category,
            initial_score=result["initial_score"],
            data_gaps=result.get("data_gaps", []),
            data_gaps_filled=result.get("data_gaps_filled", []),
            final_score=result["final_score"],
            confidence_improvement=result["confidence_improvement"],
            execution_time_ms=0,  # Will be set below
            tier=api_key.tier
        )

        # Record usage
        await tracker.record(200, tokens_used=100)

        return response

    except Exception as e:
        logger.error(f"Orchestrator analyze failed: {e}", exc_info=True)
        await tracker.record(500, error_message=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": "analysis_failed", "message": str(e)}
        )


@router.post("/analyze/batch", response_model=BatchAnalyzeResponse)
async def batch_analyze(
    request_body: BatchAnalyzeRequest,
    request: Request,
    api_key: APIKey = Depends(get_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    批量分析 - 最多 10 个

    **订阅要求**: Business 或更高
    """
    # 检查订阅层级
    if api_key.tier == "developer":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tier_not_allowed",
                "message": "Batch analysis requires Business tier or higher"
            }
        )

    tracker = UsageTracker(request)
    start_time = time.time()

    results = []
    for item in request_body.items:
        try:
            result = await analyze_opportunity(item, request, api_key, db)
            results.append(result)
        except Exception as e:
            results.append(AnalyzeResponse(
                success=False,
                category=item.category,
                initial_score={},
                data_gaps=[],
                data_gaps_filled=[],
                final_score={},
                confidence_improvement=0,
                execution_time_ms=0,
                tier=api_key.tier
            ))

    total_time = int((time.time() - start_time) * 1000)
    await tracker.record(200, tokens_used=100 * len(results))

    return BatchAnalyzeResponse(
        success=True,
        results=results,
        total=len(results),
        execution_time_ms=total_time
    )


@router.get("/status", response_model=OrchestratorStatus)
async def orchestrator_status(
    request: Request,
    api_key: APIKey = Depends(get_api_key)
):
    """
    Orchestrator 服务状态

    返回服务健康状态和支持的能力列表
    """
    import time as time_module
    # Uptime approximation (从进程启动开始)
    uptime = int(time_module.time() - time_module.time() % 86400)  # 简化

    return OrchestratorStatus(
        status="active",
        version="1.0.0",
        capabilities=[
            "cpi_scoring",
            "data_gap_detection",
            "openclaw_integration",
            "batch_analysis"
        ],
        uptime_seconds=uptime
    )
