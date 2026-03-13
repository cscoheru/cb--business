#!/usr/bin/env python3
"""
测试通知服务

快速验证通知配置是否正确
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.notification_service import (
    send_notification,
    NotificationPriority,
    get_notification_service
)


async def test_all_channels():
    """测试所有通知渠道"""
    print("=" * 60)
    print("通知服务测试")
    print("=" * 60)

    service = get_notification_service()

    if not service.channels:
        print("\n❌ 没有配置任何通知渠道")
        print("\n请参考 backend/docs/NOTIFICATION_SETUP.md 配置通知服务\n")
        print("\n快速开始 (Telegram):")
        print("1. 在Telegram中搜索 @BotFather")
        print("2. 发送 /newbot 创建bot")
        print("3. 获取Bot Token和Chat ID")
        print("4. 设置环境变量:")
        print("   export TELEGRAM_BOT_TOKEN='your_token'")
        print("   export TELEGRAM_CHAT_ID='your_chat_id'")
        return 1

    print(f"\n✅ 发现 {len(service.channels)} 个通知渠道:")
    for i, channel in enumerate(service.channels, 1):
        status = "✅" if channel.enabled else "❌"
        print(f"   {i}. {status} {channel.__class__.__name__}")

    print("\n" + "-" * 60)
    print("发送测试通知...")
    print("-" * 60)

    results = await send_notification(
        title="📧 CB-Business 通知测试",
        message="这是一条测试通知。\n\n如果你看到这条消息，说明通知配置成功！",
        priority=NotificationPriority.INFO
    )

    print("\n发送结果:")
    success_count = 0
    for channel_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"  {channel_name}: {status}")
        if success:
            success_count += 1

    print("\n" + "=" * 60)
    if success_count > 0:
        print(f"✅ {success_count}/{len(results)} 个渠道发送成功")
        print("\n请检查你的 Telegram/邮件/WhatsApp 是否收到消息")
    else:
        print("❌ 所有渠道发送失败")
        print("\n请检查配置和网络连接")

    print("=" * 60)

    return 0 if success_count > 0 else 1


async def test_priority_levels():
    """测试不同优先级的通知"""
    service = get_notification_service()

    if not service.channels:
        print("❌ 没有配置通知渠道")
        return 1

    print("\n测试不同优先级的通知...")

    priorities = [
        (NotificationPriority.INFO, "ℹ️ 信息 - 正常运行"),
        (NotificationPriority.WARNING, "⚠️ 警告 - 需要注意"),
        (NotificationPriority.ERROR, "❌ 错误 - 执行失败"),
        (NotificationPriority.CRITICAL, "🚨 严重 - 需要立即处理")
    ]

    for priority, message in priorities:
        print(f"\n发送 {priority.value} 通知...")
        await send_notification(
            title=f"测试 - {priority.value.upper()}",
            message=message,
            priority=priority
        )
        print(f"  ✓ 已发送")

    print("\n✅ 优先级测试完成")
    return 0


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="测试通知服务")
    parser.add_argument(
        '--priorities',
        action='store_true',
        help='测试不同优先级的通知'
    )

    args = parser.parse_args()

    if args.priorities:
        return await test_priority_levels()
    else:
        return await test_all_channels()


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
