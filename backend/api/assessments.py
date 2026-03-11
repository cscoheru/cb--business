# api/assessments.py
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime
import logging
import json

from schemas.assessment import (
    AssessmentType,
    CapabilityLevel,
    ResourceLevel,
    CapabilityRequest,
    InventoryRequest,
    InterestAnswer,
    GrowthProgressRequest,
    CapabilityResponse,
    InventoryResponse,
    InterestResponse,
    GrowthPathResponse,
    GrowthStage,
    Recommendation,
    Achievement,
)

router = APIRouter(prefix="/api/v1/assessments", tags=["assessments"])
logger = logging.getLogger(__name__)


# Assessment configuration matching frontend
CAPABILITY_QUESTIONS = [
    {"id": 1, "text": "跨境电商经验", "max": 5},
    {"id": 2, "text": "每周可用时间", "max": 5},
    {"id": 3, "text": "启动资金", "max": 5},
    {"id": 4, "text": "语言能力", "max": 5},
]

INVENTORY_QUESTIONS = [
    {"id": 1, "text": "供应链资源", "max": 5},
    {"id": 2, "text": "物流资源", "max": 5},
    {"id": 3, "text": "资金实力", "max": 5},
    {"id": 4, "text": "海外关系", "max": 5},
]

# Growth stages matching frontend
GROWTH_STAGES = [
    {
        "id": "stage_1",
        "title": "市场调研与选品",
        "description": "了解目标市场，选择合适的产品类别",
        "emoji": "🔍",
        "estimated_days": 7,
    },
    {
        "id": "stage_2",
        "title": "平台注册与认证",
        "description": "完成卖家账号注册和相关资质认证",
        "emoji": "📝",
        "estimated_days": 5,
    },
    {
        "id": "stage_3",
        "title": "供应链对接",
        "description": "找到可靠的供应商，建立采购渠道",
        "emoji": "🏭",
        "estimated_days": 14,
    },
    {
        "id": "stage_4",
        "title": "产品上架与优化",
        "description": "创建商品Listing，优化标题和描述",
        "emoji": "📦",
        "estimated_days": 7,
    },
    {
        "id": "stage_5",
        "title": "营销策略制定",
        "description": "规划促销活动，设置优惠券和折扣",
        "emoji": "🎯",
        "estimated_days": 5,
    },
    {
        "id": "stage_6",
        "title": "物流方案选择",
        "description": "选择合适的物流渠道，设置运费模板",
        "emoji": "🚚",
        "estimated_days": 5,
    },
    {
        "id": "stage_7",
        "title": "客服系统建立",
        "description": "设置客服渠道，准备常见问题回复",
        "emoji": "💬",
        "estimated_days": 3,
    },
    {
        "id": "stage_8",
        "title": "数据分析基础",
        "description": "学习查看店铺数据，分析销售趋势",
        "emoji": "📊",
        "estimated_days": 7,
    },
    {
        "id": "stage_9",
        "title": "广告投放入门",
        "description": "尝试平台广告，优化ROI",
        "emoji": "💰",
        "estimated_days": 7,
    },
    {
        "id": "stage_10",
        "title": "品牌建设初步",
        "description": "设计Logo，创建品牌故事",
        "emoji": "🏷️",
        "estimated_days": 7,
    },
    {
        "id": "stage_11",
        "title": "扩展多渠道",
        "description": "尝试在多个平台销售",
        "emoji": "🌐",
        "estimated_days": 14,
    },
    {
        "id": "stage_12",
        "title": "规模化运营",
        "description": "建立团队，标准化流程",
        "emoji": "🏢",
        "estimated_days": 30,
    },
]

# Achievements
ACHIEVEMENTS = [
    {"id": "first_step", "title": "初出茅庐", "description": "完成第一个成长阶段", "icon": "🌱"},
    {"id": "third_completed", "title": "渐入佳境", "description": "完成前3个成长阶段", "icon": "🌿"},
    {"id": "halfway", "title": "小有成就", "description": "完成一半成长阶段", "icon": "🌳"},
    {"id": "all_completed", "title": "大功告成", "description": "完成所有12个成长阶段", "icon": "🏆"},
    {"id": "week_one", "title": "坚持一周", "description": "7天内完成3个以上阶段", "icon": "🔥"},
]


def calculate_capability_score(request: CapabilityRequest) -> tuple[int, CapabilityLevel, Dict[str, Any]]:
    """计算能力评估分数和等级"""
    score = 0
    if request.experience is not None:
        score += request.experience
    if request.time_available is not None:
        score += request.time_available
    if request.budget is not None:
        score += request.budget
    if request.language is not None:
        score += request.language

    # Determine level
    if score <= 5:
        level = CapabilityLevel.BEGINNER
        config = {
            "level": "beginner",
            "target_region": "southeast_asia",
            "target_platform": "Shopee",
            "next_steps": [
                "从东南亚市场开始，选择泰国或越南",
                "Shopee平台适合新手，门槛较低",
                "建议从小批量测试开始，积累经验",
                "重点学习平台规则和本地化运营",
            ],
            "estimated_weeks": 12,
        }
    elif score <= 10:
        level = CapabilityLevel.INTERMEDIATE
        config = {
            "level": "intermediate",
            "target_region": "multi_region",
            "target_platform": "multi_platform",
            "next_steps": [
                "可以同时尝试东南亚和拉美市场",
                "Shopee + Lazada双平台运营",
                "建立初步的供应链体系",
                "开始关注品牌建设和口碑",
            ],
            "estimated_weeks": 8,
        }
    elif score <= 15:
        level = CapabilityLevel.ADVANCED
        config = {
            "level": "advanced",
            "target_region": "north_america",
            "target_platform": "Amazon",
            "next_steps": [
                "挑战北美市场，使用Amazon FBA",
                "考虑Shopify独立站建设",
                "建立专业的客服和售后体系",
                "注重产品差异化和服务质量",
            ],
            "estimated_weeks": 6,
        }
    else:
        level = CapabilityLevel.EXPERT
        config = {
            "level": "expert",
            "target_region": "global",
            "target_platform": "custom",
            "next_steps": [
                "全球布局，多平台多市场并行",
                "考虑本地仓储和海外仓策略",
                "建立品牌矩阵和多产品线",
                "探索B2B和B2C混合模式",
            ],
            "estimated_weeks": 4,
        }

    return score, level, config


def calculate_inventory_score(request: InventoryRequest) -> tuple[int, ResourceLevel, Dict[str, Any]]:
    """计算资源评估分数和等级"""
    score = 0
    if request.supply_chain is not None:
        score += request.supply_chain
    if request.logistics is not None:
        score += request.logistics
    if request.capital is not None:
        score += request.capital
    if request.overseas is not None:
        score += request.overseas

    # Determine level
    if score <= 8:
        level = ResourceLevel.LIGHT
        config = {
            "level": "light",
            "strategy": "轻量Dropshipping模式",
            "focus_areas": [
                "无货源代发模式",
                "数字产品和虚拟商品",
                "一件代发合作",
                "低资金门槛品类",
            ],
            "risk_considerations": [
                "利润率相对较低",
                "对供应商依赖性强",
                "需要严格把控产品质量",
            ],
        }
    elif score <= 15:
        level = ResourceLevel.MODERATE
        config = {
            "level": "moderate",
            "strategy": "稳健小库存模式",
            "focus_areas": [
                "小批量多次采购",
                "第三方海外仓",
                "混合物流方案",
                "中档价位产品",
            ],
            "risk_considerations": [
                "需要一定的资金周转",
                "库存管理要求提高",
                "平衡库存成本和销售速度",
            ],
        }
    else:
        level = ResourceLevel.STRONG
        config = {
            "level": "strong",
            "strategy": "优势自有品牌模式",
            "focus_areas": [
                "自有品牌建设",
                "专属供应链",
                "自建海外仓",
                "高端产品线",
            ],
            "risk_considerations": [
                "前期投入较大",
                "品牌建设周期长",
                "需要专业团队支持",
            ],
        }

    return score, level, config


def calculate_interest_matches(interests: List[str], market_pref: str) -> Dict[str, Any]:
    """计算兴趣匹配结果"""
    # Interest to category mapping
    category_map = {
        "美妆": ["beauty", "cosmetics"],
        "电子": ["electronics", "tech"],
        "家居": ["home", "living"],
        "服饰": ["fashion", "clothing"],
        "食品": ["food", "snacks"],
        "母婴": ["baby", "maternal"],
        "运动": ["sports", "outdoor"],
        "图书": ["books", "education"],
    }

    # Platform recommendations based on interests
    platform_map = {
        "美妆": ["Shopee", "Lazada", "TikTok Shop"],
        "电子": ["Shopee", "Lazada", "Amazon"],
        "家居": ["Shopee", "Lazada", "Amazon"],
        "服饰": ["Shopee", "TikTok Shop", "Amazon"],
        "食品": ["Shopee", "Lazada"],
        "母婴": ["Shopee", "Lazada", "Amazon"],
        "运动": ["Shopee", "Lazada", "Amazon"],
        "图书": ["Shopee", "Amazon"],
    }

    # Match categories
    matched_categories = []
    recommended_products = []
    target_platforms = set()

    for interest in interests:
        if interest in category_map:
            matched_categories.extend(category_map[interest])
        if interest in platform_map:
            target_platforms.update(platform_map[interest])

        # Add specific product recommendations
        if interest == "美妆":
            recommended_products.extend(["面膜", "口红", "护肤品"])
        elif interest == "电子":
            recommended_products.extend(["手机配件", "数码配件", "小家电"])
        elif interest == "家居":
            recommended_products.extend(["收纳用品", "装饰品", "厨房用品"])
        elif interest == "服饰":
            recommended_products.extend(["休闲装", "运动装", "配饰"])
        elif interest == "食品":
            recommended_products.extend(["零食", "保健品", "地方特产"])

    # Determine target markets
    if market_pref == "southeast_asia":
        target_markets = ["泰国", "越南", "马来西亚", "印尼", "菲律宾"]
    elif market_pref == "north_america":
        target_markets = ["美国", "加拿大"]
    elif market_pref == "latin_america":
        target_markets = ["巴西", "墨西哥", "哥伦比亚"]
    else:
        target_markets = ["泰国", "越南", "马来西亚", "美国", "巴西"]

    return {
        "matched_categories": list(set(matched_categories)),
        "recommended_products": list(set(recommended_products)),
        "target_platforms": list(target_platforms),
        "target_markets": target_markets,
        "learning_resources": [
            f"{market_pref}市场运营指南",
            "产品Listing优化技巧",
            "平台广告投放教程",
            "客服话术模板",
        ],
    }


@router.post("/capability", response_model=CapabilityResponse)
async def assess_capability(request: CapabilityRequest):
    """个人能力照妖镜评估"""
    score, level, config = calculate_capability_score(request)

    recommendations = [
        Recommendation(
            type="region",
            title=config["target_region"],
            description="推荐目标市场",
            icon="🌍",
        ),
        Recommendation(
            type="platform",
            title=config["target_platform"],
            description="推荐电商平台",
            icon="🛒",
        ),
        Recommendation(
            type="timeline",
            title=f"{config['estimated_weeks']}周",
            description="预计上手时间",
            icon="⏱️",
        ),
    ]

    return CapabilityResponse(
        assessment_type=AssessmentType.CAPABILITY,
        score=score,
        level=level.value,
        recommendations=recommendations,
        created_at=datetime.utcnow(),
        experience_level=level,
        target_region=config["target_region"],
        target_platform=config["target_platform"],
        next_steps=config["next_steps"],
        estimated_weeks=config["estimated_weeks"],
    )


@router.post("/inventory", response_model=InventoryResponse)
async def assess_inventory(request: InventoryRequest):
    """资源盘点评估"""
    score, level, config = calculate_inventory_score(request)

    recommendations = [
        Recommendation(
            type="strategy",
            title=config["strategy"],
            description="推荐运营策略",
            icon="💡",
        ),
        Recommendation(
            type="level",
            title=level.value,
            description="资源等级",
            icon="📊",
        ),
    ]

    return InventoryResponse(
        assessment_type=AssessmentType.INVENTORY,
        score=score,
        level=level.value,
        recommendations=recommendations,
        created_at=datetime.utcnow(),
        resource_level=level,
        strategy=config["strategy"],
        focus_areas=config["focus_areas"],
        risk_considerations=config["risk_considerations"],
    )


@router.post("/interest", response_model=InterestResponse)
async def assess_interest(request: InterestAnswer):
    """兴趣推荐评估"""
    matches = calculate_interest_matches(request.interests, request.market_preference or "southeast_asia")

    recommendations = [
        Recommendation(
            type="category",
            title=", ".join(matches["matched_categories"][:3]),
            description="匹配产品类别",
            icon="📦",
        ),
        Recommendation(
            type="platform",
            title=", ".join(matches["target_platforms"][:2]),
            description="推荐平台",
            icon="🛒",
        ),
    ]

    return InterestResponse(
        assessment_type=AssessmentType.INTEREST,
        score=len(request.interests),
        level="matched",
        recommendations=recommendations,
        created_at=datetime.utcnow(),
        matched_categories=matches["matched_categories"],
        recommended_products=matches["recommended_products"],
        target_markets=matches["target_markets"],
        learning_resources=matches["learning_resources"],
    )


@router.get("/growth", response_model=GrowthPathResponse)
async def get_growth_path():
    """获取成长路径（不包含用户进度）"""
    stages = [
        GrowthStage(**stage, completed=False, completed_at=None)
        for stage in GROWTH_STAGES
    ]

    total_days = sum(stage["estimated_days"] for stage in GROWTH_STAGES)

    achievements = [
        Achievement(**achievement, unlocked=False, unlocked_at=None)
        for achievement in ACHIEVEMENTS
    ]

    return GrowthPathResponse(
        stages=stages,
        completed_count=0,
        total_count=len(GROWTH_STAGES),
        percentage=0,
        current_stage=GROWTH_STAGES[0]["id"],
        next_stage=GROWTH_STAGES[0]["id"],
        estimated_completion_days=total_days,
        unlocked_achievements=[],
    )


@router.get("/growth/config")
async def get_growth_config():
    """获取成长路径配置（静态数据）"""
    return {
        "stages": GROWTH_STAGES,
        "achievements": ACHIEVEMENTS,
        "total_stages": len(GROWTH_STAGES),
    }
