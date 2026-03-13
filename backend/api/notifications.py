# api/notifications.py
"""通知API - 统一的多渠道通知接口

支持Telegram、邮件、WhatsApp等多渠道通知
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

from services.notification_service import (
    get_notification_service,
    NotificationPriority
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


class NotificationPriorityEnum(str, Enum):
    """通知优先级"""
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class SendNotificationRequest(BaseModel):
    """发送通知请求"""
    title: str = Field(..., description="通知标题")
    message: str = Field(..., description="通知内容")
    priority: NotificationPriorityEnum = Field(
        default=NotificationPriorityEnum.info,
        description="通知优先级"
    )
    context: str = Field("", description="附加上下文信息")


class SendNotificationResponse(BaseModel):
    """发送通知响应"""
    success: bool
    channels: dict
    timestamp: str


@router.post("/notify", response_model=SendNotificationResponse)
async def send_notification_endpoint(request: SendNotificationRequest):
    """
    发送通知到所有配置的渠道

    用途:
    - OpenClaw Channel执行结果通知
    - 监控告警通知
    - 自定义通知

    示例:
        POST /api/v1/notifications/notify
        {
            "title": "OpenClaw执行成功",
            "message": "成功采集50篇文章",
            "priority": "info"
        }
    """
    try:
        service = get_notification_service()

        # 发送通知
        priority = NotificationPriority(request.priority.value)
        results = await service.notify(
            title=request.title,
            message=request.message,
            priority=priority
        )

        # 统计成功/失败
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)

        return SendNotificationResponse(
            success=success_count > 0,
            channels=results,
            timestamp=f"{len([k for k,v in results.items() if v])}/{total_count} channels succeeded"
        )

    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_notification():
    """
    测试通知功能

    发送一条测试通知到所有配置的渠道
    """
    try:
        service = get_notification_service()

        results = await service.notify(
            title="📧 测试通知",
            message="这是一条来自CB-Business的测试通知。\n\n如果你看到这条消息，说明通知配置成功！",
            priority=NotificationPriority.INFO
        )

        return {
            "success": True,
            "message": "测试通知已发送",
            "channels": results,
            "note": "请检查你的Telegram/邮件/WhatsApp是否收到消息"
        }

    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_notification_status():
    """
    获取通知服务状态

    返回配置的通知渠道及其状态
    """
    try:
        service = get_notification_service()

        channels_info = []
        for channel in service.channels:
            channel_info = {
                "type": channel.__class__.__name__,
                "enabled": channel.enabled
            }

            # 根据渠道类型添加额外信息
            if isinstance(channel, type(service.channels[0])):  # TelegramChannel
                # 这里需要实际导入类型来检查
                pass

            channels_info.append(channel_info)

        return {
            "success": True,
            "total_channels": len(service.channels),
            "channels": channels_info,
            "note": "没有配置通知渠道。请查看 docs/NOTIFICATION_SETUP.md 了解配置方法。" if len(service.channels) == 0 else None
        }

    except Exception as e:
        logger.error(f"Failed to get notification status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
