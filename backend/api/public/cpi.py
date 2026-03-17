# api/public/cpi.py
"""CPI 算法公共 API

提供 CPI (Competition-Potential-Intelligence) 评分计算服务

CPI 评分体系:
- C (Competition) 竞争度: 40%
  - 多平台价格离散度: 15%
  - 卖家密度: 15%
  - 评论增长趋势: 10%

- P (Potential) 潜力: 40%
  - Google Trends 增长: 20%
  - 区域市场对比: 20%

- I (Intelligence) 智能洞察: 20%
  - AI 综合建议
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging

from api.public.dependencies import get_api_key, UsageTracker
from models.api_key import APIKey
from services.cpi_calculator import CPICalculator, CPIResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/public/cpi", tags=["public-cpi"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CPICalculateRequest(BaseModel):
    """CPI 计算请求"""
    multi_platform_data: Optional[Dict[str, Any]] = Field(
        None,
        description="多平台聚合数据 (Amazon + Lazada + Shopee)"
    )
    amazon_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Amazon 单平台数据 (兼容模式)"
    )
    google_trends_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Google Trends 数据"
    )
    article_insights: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="相关文章洞察"
    )


class CPICalculateResponse(BaseModel):
    """CPI 计算响应"""
    success: bool = True
    c_score: float = Field(..., description="竞争度分数 (0-100)")
    p_score: float = Field(..., description="潜力分数 (0-100)")
    i_score: float = Field(..., description="智能洞察分数 (0-100)")
    total_score: float = Field(..., description="加权总分 (0-100)")
    confidence: float = Field(..., description="数据置信度 (0-1)")
    data_quality: str = Field(..., description="数据质量: high, medium, low")
    recommendation: str = Field(..., description="AI 建议")
    risk_level: str = Field(..., description="风险等级: low, medium, high")
    details: Dict[str, Any] = Field(..., description="详细分析")
    tier: str = Field(..., description="当前订阅层级")


class CPIAdvancedResponse(BaseModel):
    """高级 CPI 响应"""
    result: Dict[str, Any]
    algorithm_version: str
    weights: Dict[str, float]
    sub_weights: Dict[str, Dict[str, float]]


class CPIWeightsResponse(BaseModel):
    """CPI 权重配置"""
    competition: Dict[str, Any]
    potential: Dict[str, Any]
    intelligence: Dict[str, Any]


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/calculate", response_model=CPICalculateResponse)
async def calculate_cpi(
    request_body: CPICalculateRequest,
    request: Request,
    api_key: APIKey = Depends(get_api_key)
):
    """
    计算 CPI 分数

    CPI (Competition-Potential-Intelligence) 评分体系:

    - **C (Competition) 竞争度: 40%**
      - 多平台价格离散度: 15%
      - 卖家密度: 15%
      - 评论增长趋势: 10%

    - **P (Potential) 潜力: 40%**
      - Google Trends 增长: 20%
      - 区域市场对比: 20%

    - **I (Intelligence) 智能洞察: 20%**
      - AI 综合建议

    **订阅要求**: Developer 或更高
    """
    tracker = UsageTracker(request)

    try:
        calculator = CPICalculator()
        result: CPIResult = calculator.calculate(
            multi_platform_data=request_body.multi_platform_data,
            amazon_data=request_body.amazon_data,
            google_trends_data=request_body.google_trends_data,
            article_insights=request_body.article_insights
        )

        await tracker.record(200, tokens_used=50)

        return CPICalculateResponse(
            success=True,
            c_score=result.c_score,
            p_score=result.p_score,
            i_score=result.i_score,
            total_score=result.total_score,
            confidence=result.confidence,
            data_quality=result.data_quality,
            recommendation=result.recommendation,
            risk_level=result.risk_level,
            details=result.details,
            tier=api_key.tier
        )

    except Exception as e:
        logger.error(f"CPI calculation failed: {e}", exc_info=True)
        await tracker.record(500, error_message=str(e))
        raise


@router.post("/calculate/advanced", response_model=CPIAdvancedResponse)
async def calculate_cpi_advanced(
    request_body: CPICalculateRequest,
    request: Request,
    api_key: APIKey = Depends(get_api_key)
):
    """
    高级 CPI 计算 - 包含完整分析报告

    返回完整的算法信息和权重配置

    **订阅要求**: Business 或更高
    """
    # 检查订阅层级
    if api_key.tier == "developer":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tier_not_allowed",
                "message": "Advanced calculation requires Business tier or higher"
            }
        )

    tracker = UsageTracker(request)

    try:
        calculator = CPICalculator()
        result = calculator.calculate(
            multi_platform_data=request_body.multi_platform_data,
            amazon_data=request_body.amazon_data,
            google_trends_data=request_body.google_trends_data,
            article_insights=request_body.article_insights
        )

        await tracker.record(200, tokens_used=100)

        return CPIAdvancedResponse(
            result=result.to_dict(),
            algorithm_version="2.0",
            weights=calculator.WEIGHTS,
            sub_weights=calculator.SUB_WEIGHTS
        )

    except Exception as e:
        logger.error(f"Advanced CPI calculation failed: {e}", exc_info=True)
        await tracker.record(500, error_message=str(e))
        raise


@router.get("/weights", response_model=CPIWeightsResponse)
async def get_cpi_weights(
    request: Request,
    api_key: APIKey = Depends(get_api_key)
):
    """
    获取 CPI 权重配置

    返回各维度的权重和子权重配置
    """
    tracker = UsageTracker(request)
    await tracker.record(200, tokens_used=0)

    return CPIWeightsResponse(
        competition={
            "weight": 0.40,
            "description": "竞争度 - 衡量市场竞争激烈程度",
            "components": {
                "price_dispersion": {
                    "weight": 0.375,
                    "description": "价格离散度 - 价格范围越宽竞争越激烈"
                },
                "seller_density": {
                    "weight": 0.375,
                    "description": "卖家密度 - 卖家数量与产品数量比值"
                },
                "review_growth": {
                    "weight": 0.25,
                    "description": "评论增长趋势 - 市场成熟度指标"
                }
            }
        },
        potential={
            "weight": 0.40,
            "description": "潜力 - 衡量市场增长空间",
            "components": {
                "google_trends": {
                    "weight": 0.50,
                    "description": "Google Trends 增长趋势"
                },
                "regional_comparison": {
                    "weight": 0.50,
                    "description": "区域市场对比 - 多区域覆盖潜力"
                }
            }
        },
        intelligence={
            "weight": 0.20,
            "description": "智能洞察 - AI 综合分析和建议",
            "components": {
                "ai_insights": {
                    "weight": 1.0,
                    "description": "基于 C 和 P 分数的 AI 综合判断"
                }
            }
        }
    )


from fastapi import HTTPException
