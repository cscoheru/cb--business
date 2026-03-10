# schemas/common.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: datetime
    database: str
    redis: str


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True
