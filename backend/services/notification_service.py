# services/notification_service.py
"""多渠道通知服务

支持:
1. Telegram Bot - 实时推送监控报告和告警
2. 邮件通知 - 发送详细报告
3. WhatsApp (Twilio) - 重要告警

环境变量:
- TELEGRAM_BOT_TOKEN: Telegram Bot Token
- TELEGRAM_CHAT_ID: 接收通知的Chat ID
- SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS: 邮件配置
- TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN: Twilio配置 (WhatsApp)
- WHATSAPP_TO_NUMBER: 接收WhatsApp的号码
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class NotificationPriority(str, Enum):
    """通知优先级"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel:
    """通知渠道基类"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    async def send(
        self,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.INFO,
        **kwargs
    ) -> bool:
        """发送通知"""
        if not self.enabled:
            logger.debug(f"{self.__class__.__name__} is disabled, skipping notification")
            return False
        return False


class TelegramChannel(NotificationChannel):
    """Telegram Bot通知渠道"""

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        enabled: bool = True
    ):
        super().__init__(enabled)
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    async def send(
        self,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.INFO,
        **kwargs
    ) -> bool:
        """发送Telegram通知"""
        try:
            # 根据优先级添加emoji
            emoji_map = {
                NotificationPriority.INFO: "ℹ️",
                NotificationPriority.WARNING: "⚠️",
                NotificationPriority.ERROR: "❌",
                NotificationPriority.CRITICAL: "🚨"
            }
            emoji = emoji_map.get(priority, "")

            # 格式化消息
            formatted_message = f"{emoji} <b>{title}</b>\n\n{message}"

            # 添加时间戳
            formatted_message += f"\n\n🕔 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # 发送消息
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": formatted_message,
                        "parse_mode": "HTML"
                    }
                )
                response.raise_for_status()

            logger.info(f"Telegram notification sent: {title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False


class EmailChannel(NotificationChannel):
    """邮件通知渠道"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str],
        enabled: bool = True
    ):
        super().__init__(enabled)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails

    async def send(
        self,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.INFO,
        **kwargs
    ) -> bool:
        """发送邮件通知"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{priority.value.upper()}] {title}"
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)

            # 纯文本部分
            text_part = MIMEText(message, 'plain')
            msg.attach(text_part)

            # HTML部分
            html_message = f"""
            <html>
            <body>
                <h2>{title}</h2>
                <p>{message.replace(chr(10), '<br>')}</p>
                <hr>
                <p style="color: gray; font-size: 12px;">
                    时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                    优先级: {priority.value.upper()}
                </p>
            </body>
            </html>
            """
            html_part = MIMEText(html_message, 'html')
            msg.attach(html_part)

            # 发送邮件
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email notification sent: {title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False


class WhatsAppChannel(NotificationChannel):
    """WhatsApp通知渠道 (通过Twilio)"""

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        to_number: str,
        enabled: bool = True
    ):
        super().__init__(enabled)
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.to_number = to_number
        self.api_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

    async def send(
        self,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.INFO,
        **kwargs
    ) -> bool:
        """发送WhatsApp通知"""
        try:
            # WhatsApp主要用于重要告警
            if priority == NotificationPriority.INFO:
                logger.debug("Skipping WhatsApp for INFO priority")
                return False

            # 根据优先级添加emoji
            emoji_map = {
                NotificationPriority.WARNING: "⚠️",
                NotificationPriority.ERROR: "❌",
                NotificationPriority.CRITICAL: "🚨"
            }
            emoji = emoji_map.get(priority, "")

            formatted_message = f"{emoji} *{title}*\n\n{message}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    data={
                        "From": f"whatsapp:{self.from_number}",
                        "To": f"whatsapp:{self.to_number}",
                        "Body": formatted_message
                    },
                    auth=(self.account_sid, self.auth_token)
                )
                response.raise_for_status()

            logger.info(f"WhatsApp notification sent: {title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send WhatsApp notification: {e}")
            return False


class NotificationService:
    """统一通知服务"""

    def __init__(self):
        self.channels: List[NotificationChannel] = []

    def add_channel(self, channel: NotificationChannel):
        """添加通知渠道"""
        self.channels.append(channel)

    async def notify(
        self,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.INFO,
        channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        发送通知到所有或指定渠道

        Args:
            title: 通知标题
            message: 通知内容
            priority: 优先级
            channels: 指定渠道 (None表示所有渠道)

        Returns:
            各渠道发送结果
        """
        results = {}

        for channel in self.channels:
            channel_name = channel.__class__.__name__

            # 如果指定了渠道，只发送到指定的渠道
            if channels and channel_name not in channels:
                continue

            try:
                success = await channel.send(title, message, priority)
                results[channel_name] = success
            except Exception as e:
                logger.error(f"Failed to send notification via {channel_name}: {e}")
                results[channel_name] = False

        return results

    async def notify_monitoring_report(self, report: Dict[str, Any]) -> Dict[str, bool]:
        """发送监控报告"""
        status = report.get('health', {}).get('overall_status', 'unknown')

        # 根据状态确定优先级
        priority_map = {
            'healthy': NotificationPriority.INFO,
            'warning': NotificationPriority.WARNING,
            'critical': NotificationPriority.CRITICAL
        }
        priority = priority_map.get(status, NotificationPriority.INFO)

        # 构建消息
        title = f"双轨运行监控报告 - {status.upper()}"

        message = f"""
【数据采集对比】
APScheduler: {report.get('apscheduler', {}).get('articles_last_hour', 0)} 篇/小时
OpenClaw: {report.get('openclaw', {}).get('articles_last_hour', 0)} 篇/小时

【对比分析】
一致性评分: {report.get('comparison', {}).get('consistency_score', 0):.1%}
数量差异: {report.get('comparison', {}).get('count_diff', 0):+.0} ({report.get('comparison', {}).get('count_diff_pct', 0):+.1f}%)

【数据质量】
最新文章: {report.get('data_quality', {}).get('article_age_minutes', 0)} 分钟前
24h重复数: {report.get('data_quality', {}).get('duplicate_count_24h', 0)}

【健康评分】
整体: {report.get('health', {}).get('health_score', 0):.1%}
数据库: {report.get('health', {}).get('database', 'unknown')}
        """.strip()

        return await self.notify(title, message, priority)

    async def notify_error(self, error_message: str, context: str = "") -> Dict[str, bool]:
        """发送错误通知"""
        title = "OpenClaw执行错误"
        message = f"{context}\n\n{error_message}" if context else error_message
        return await self.notify(title, message, NotificationPriority.ERROR)


# ============================================================================
# 全局单例
# ============================================================================

_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """获取全局通知服务单例"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()

        # 从环境变量加载配置
        import os

        # Telegram
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if telegram_token and telegram_chat_id:
            _notification_service.add_channel(
                TelegramChannel(telegram_token, telegram_chat_id)
            )
            logger.info("Telegram notification enabled")

        # Email
        smtp_host = os.getenv('SMTP_HOST')
        smtp_port = os.getenv('SMTP_PORT', '587')
        smtp_user = os.getenv('SMTP_USER')
        smtp_pass = os.getenv('SMTP_PASS')
        from_email = os.getenv('FROM_EMAIL')
        to_emails = os.getenv('TO_EMAILS', '').split(',')
        if smtp_host and smtp_user and smtp_pass:
            _notification_service.add_channel(
                EmailChannel(
                    smtp_host=smtp_host,
                    smtp_port=int(smtp_port),
                    username=smtp_user,
                    password=smtp_pass,
                    from_email=from_email or smtp_user,
                    to_emails=[e.strip() for e in to_emails if e.strip()]
                )
            )
            logger.info("Email notification enabled")

        # WhatsApp
        twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        whatsapp_from = os.getenv('WHATSAPP_FROM_NUMBER')
        whatsapp_to = os.getenv('WHATSAPP_TO_NUMBER')
        if twilio_sid and twilio_token and whatsapp_from and whatsapp_to:
            _notification_service.add_channel(
                WhatsAppChannel(
                    account_sid=twilio_sid,
                    auth_token=twilio_token,
                    from_number=whatsapp_from,
                    to_number=whatsapp_to
                )
            )
            logger.info("WhatsApp notification enabled")

        if not _notification_service.channels:
            logger.warning("No notification channels configured")

    return _notification_service


# ============================================================================
# 便捷函数
# ============================================================================

async def send_notification(
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.INFO
) -> Dict[str, bool]:
    """发送通知"""
    service = get_notification_service()
    return await service.notify(title, message, priority)


async def send_monitoring_report(report: Dict[str, Any]) -> Dict[str, bool]:
    """发送监控报告"""
    service = get_notification_service()
    return await service.notify_monitoring_report(report)


async def send_error_alert(error_message: str, context: str = "") -> Dict[str, bool]:
    """发送错误告警"""
    service = get_notification_service()
    return await service.notify_error(error_message, context)
