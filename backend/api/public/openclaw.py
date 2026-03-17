# api/public/openclaw.py
"""OpenClaw 调用公共 API

提供直接调用 OpenClaw 技能的端点

可用技能:
- deep_market_scan: 深度市场扫描
- mock_order_analysis: 模拟订单分析
- competitor_watch: 竞争对手监控
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
import time

from api.public.dependencies import get_api_key, UsageTracker
from models.api_key import APIKey
from config.mcp_client import get_mcp_client, call_openclaw_skill

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/public/openclaw", tags=["public-openclaw"])


# ============================================================================
# Request/Response Models
# ============================================================================

class InvokeRequest(BaseModel):
    """OpenClaw 调用请求"""
    skill: str = Field(
        ...,
        description="技能名称",
        example="deep_market_scan"
    )
    params: Dict[str, Any] = Field(
        ...,
        description="技能参数",
        example={"category": "phone_cases", "depth_level": "deep"}
    )


class InvokeResponse(BaseModel):
    """OpenClaw 调用响应"""
    success: bool
    skill: str
    data: Dict[str, Any]
    execution_time_ms: int
    tier: str


class SkillInfo(BaseModel):
    """技能信息"""
    name: str
    description: str
    params: Dict[str, str]


class SkillsListResponse(BaseModel):
    """技能列表响应"""
    skills: List[SkillInfo]
    total: int


# ============================================================================
# Available Skills Definition
# ============================================================================

AVAILABLE_SKILLS = {
    "deep_market_scan": {
        "description": "深度市场扫描 - 获取竞争度、价格分布、评论趋势",
        "params": {
            "category": "string - 产品类目 (必填)",
            "anomaly_detected": "boolean - 是否检测异常 (可选)",
            "depth_level": "string - 扫描深度: deep/standard/intensive (可选)"
        },
        "tier_required": "developer"
    },
    "mock_order_analysis": {
        "description": "模拟订单分析 - 获取真实成本、物流信息",
        "params": {
            "asin": "string - Amazon ASIN (必填)",
            "quantity": "integer - 购买数量 (可选，默认1)"
        },
        "tier_required": "business"
    },
    "competitor_watch": {
        "description": "竞争对手监控 - 跟踪价格变化、新品上架",
        "params": {
            "category": "string - 产品类目 (必填)",
            "competitors": "array - 竞争对手列表 (可选)",
            "watch_duration": "integer - 监控时长(秒) (可选)"
        },
        "tier_required": "business"
    }
}

TIER_HIERARCHY = {"developer": 1, "business": 2, "enterprise": 3}


def check_tier_access(user_tier: str, required_tier: str) -> bool:
    """检查用户层级是否有权限访问"""
    return TIER_HIERARCHY.get(user_tier, 0) >= TIER_HIERARCHY.get(required_tier, 999)


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/invoke", response_model=InvokeResponse)
async def invoke_openclaw_skill(
    request_body: InvokeRequest,
    request: Request,
    api_key: APIKey = Depends(get_api_key)
):
    """
    调用 OpenClaw 技能

    **可用技能**:

    | 技能 | 描述 | 订阅要求 |
    |------|------|----------|
    | `deep_market_scan` | 深度市场扫描 | Developer |
    | `mock_order_analysis` | 模拟订单分析 | Business |
    | `competitor_watch` | 竞争对手监控 | Business |

    **示例**:
    ```json
    {
        "skill": "deep_market_scan",
        "params": {
            "category": "phone_cases",
            "depth_level": "deep"
        }
    }
    ```
    """
    tracker = UsageTracker(request)
    start_time = time.time()

    # 验证技能名称
    skill_name = request_body.skill
    if skill_name not in AVAILABLE_SKILLS:
        await tracker.record(400, error_message=f"Invalid skill: {skill_name}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_skill",
                "message": f"Invalid skill: {skill_name}",
                "available_skills": list(AVAILABLE_SKILLS.keys())
            }
        )

    # 检查订阅层级
    skill_config = AVAILABLE_SKILLS[skill_name]
    required_tier = skill_config["tier_required"]
    if not check_tier_access(api_key.tier, required_tier):
        await tracker.record(403, error_message=f"Tier {api_key.tier} not allowed")
        raise HTTPException(
            status_code=403,
            detail={
                "error": "tier_not_allowed",
                "message": f"Skill '{skill_name}' requires {required_tier} tier or higher",
                "current_tier": api_key.tier,
                "required_tier": required_tier
            }
        )

    try:
        # 调用 OpenClaw
        result = await call_openclaw_skill(skill_name, request_body.params)

        execution_time = int((time.time() - start_time) * 1000)
        await tracker.record(200, tokens_used=50)

        return InvokeResponse(
            success=result.get("success", True),
            skill=skill_name,
            data=result.get("data", result),
            execution_time_ms=execution_time,
            tier=api_key.tier
        )

    except Exception as e:
        logger.error(f"OpenClaw skill invocation failed: {e}", exc_info=True)
        execution_time = int((time.time() - start_time) * 1000)
        await tracker.record(500, error_message=str(e))

        return InvokeResponse(
            success=False,
            skill=skill_name,
            data={"error": str(e)},
            execution_time_ms=execution_time,
            tier=api_key.tier
        )


@router.get("/skills", response_model=SkillsListResponse)
async def list_openclaw_skills(
    request: Request,
    api_key: APIKey = Depends(get_api_key)
):
    """
    列出可用的 OpenClaw 技能

    返回当前用户有权访问的所有技能及其参数说明
    """
    tracker = UsageTracker(request)
    await tracker.record(200, tokens_used=0)

    # 过滤出用户有权限的技能
    accessible_skills = []
    for name, config in AVAILABLE_SKILLS.items():
        if check_tier_access(api_key.tier, config["tier_required"]):
            accessible_skills.append(SkillInfo(
                name=name,
                description=config["description"],
                params=config["params"]
            ))

    return SkillsListResponse(
        skills=accessible_skills,
        total=len(accessible_skills)
    )


@router.get("/health")
async def openclaw_health(
    request: Request,
    api_key: APIKey = Depends(get_api_key)
):
    """
    OpenClaw MCP 服务健康检查

    返回 MCP 连接状态
    """
    tracker = UsageTracker(request)

    try:
        client = get_mcp_client()
        connected = client.is_connected()

        # 尝试连接
        if not connected:
            connected = await client.connect()

        tools = []
        if connected:
            tools = await client.list_tools()

        await tracker.record(200, tokens_used=0)

        return {
            "status": "healthy" if connected else "degraded",
            "mcp_connected": connected,
            "available_tools": tools,
            "server_url": getattr(client, 'base_url', 'stdio')
        }

    except Exception as e:
        await tracker.record(500, error_message=str(e))
        return {
            "status": "unhealthy",
            "mcp_connected": False,
            "error": str(e)
        }
