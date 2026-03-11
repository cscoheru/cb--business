# schemas/assessment.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AssessmentType(str, Enum):
    """评估类型"""
    CAPABILITY = "capability"  # 个人能力照妖镜
    INVENTORY = "inventory"    # 资源盘点
    INTEREST = "interest"      # 兴趣推荐
    GROWTH = "growth"          # 成长路径


class ExperienceLevel(str, Enum):
    """经验水平"""
    NONE = "none"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class CapabilityLevel(str, Enum):
    """能力等级"""
    BEGINNER = "beginner"      # 新手路径
    INTERMEDIATE = "intermediate"  # 进阶路径
    ADVANCED = "advanced"      # 专业路径
    EXPERT = "expert"          # 专家路径


class ResourceLevel(str, Enum):
    """资源等级"""
    LIGHT = "light"            # 轻量策略
    MODERATE = "moderate"      # 稳健策略
    STRONG = "strong"          # 优势策略


class CapabilityAnswer(BaseModel):
    """能力评估答案"""
    question_id: int
    value: int


class CapabilityRequest(BaseModel):
    """能力评估请求"""
    experience: Optional[int] = Field(None, ge=0, le=5, description="跨境电商经验 (0-5年)")
    time_available: Optional[int] = Field(None, ge=1, le=5, description="每周可用时间 (1-5)")
    budget: Optional[int] = Field(None, ge=0, le=5, description="启动资金 (0-5)")
    language: Optional[int] = Field(None, ge=1, le=5, description="语言能力 (1-5)")


class InventoryRequest(BaseModel):
    """资源盘点请求"""
    supply_chain: Optional[int] = Field(None, ge=1, le=5, description="供应链资源")
    logistics: Optional[int] = Field(None, ge=1, le=5, description="物流资源")
    capital: Optional[int] = Field(None, ge=1, le=5, description="资金实力")
    overseas: Optional[int] = Field(None, ge=1, le=5, description="海外关系")


class InterestAnswer(BaseModel):
    """兴趣评估答案"""
    interests: List[str] = Field(default_factory=list, description="选择的兴趣标签")
    market_preference: Optional[str] = Field(None, description="市场偏好")


class GrowthProgress(BaseModel):
    """成长路径进度"""
    stage_id: str
    completed: bool
    completed_at: Optional[datetime] = None


class GrowthProgressRequest(BaseModel):
    """成长路径进度更新请求"""
    stage_id: str
    completed: bool


# Response Models
class Recommendation(BaseModel):
    """推荐项"""
    type: str
    title: str
    description: str
    icon: Optional[str] = None


class AssessmentResponse(BaseModel):
    """评估响应基类"""
    assessment_type: AssessmentType
    score: int
    level: str
    recommendations: List[Recommendation]
    created_at: datetime


class CapabilityResponse(AssessmentResponse):
    """能力评估响应"""
    experience_level: CapabilityLevel
    target_region: str
    target_platform: str
    next_steps: List[str]
    estimated_weeks: int


class InventoryResponse(AssessmentResponse):
    """资源盘点响应"""
    resource_level: ResourceLevel
    strategy: str
    focus_areas: List[str]
    risk_considerations: List[str]


class InterestResponse(AssessmentResponse):
    """兴趣推荐响应"""
    matched_categories: List[str]
    recommended_products: List[str]
    target_markets: List[str]
    learning_resources: List[str]


class GrowthStage(BaseModel):
    """成长阶段"""
    id: str
    title: str
    description: str
    emoji: str
    estimated_days: int
    completed: bool = False
    completed_at: Optional[datetime] = None


class GrowthPathResponse(BaseModel):
    """成长路径响应"""
    stages: List[GrowthStage]
    completed_count: int
    total_count: int
    percentage: int
    current_stage: Optional[str] = None
    next_stage: Optional[str] = None
    estimated_completion_days: Optional[int] = None
    unlocked_achievements: List[Dict[str, Any]]


class Achievement(BaseModel):
    """成就"""
    id: str
    title: str
    description: str
    icon: str
    unlocked: bool
    unlocked_at: Optional[datetime] = None
