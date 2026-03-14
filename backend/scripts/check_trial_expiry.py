#!/usr/bin/env python3
"""
Trial用户到期检查脚本

功能:
1. 检查所有Trial用户是否到期
2. 自动将到期用户降级到Free计划
3. 记录到期日志
4. 可选: 发送到期通知邮件

使用方法:
  python scripts/check_trial_expiry.py [--dry-run] [--notify]

  --dry-run: 只显示将要处理的用户，不实际执行
  --notify: 发送到期通知邮件 (需要配置邮件服务)
"""

import asyncio
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, and_
from config.database import AsyncSessionLocal, get_db
from models.user import User
from models.subscription import Subscription


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrialExpiryChecker:
    """Trial到期检查器"""

    def __init__(self, dry_run: bool = False, notify: bool = False):
        self.dry_run = dry_run
        self.notify = notify
        self.stats = {
            'checked': 0,
            'expired': 0,
            'downgraded': 0,
            'notified': 0,
            'errors': 0
        }

    async def get_expired_trial_users(self, db: AsyncSessionLocal) -> List[User]:
        """获取所有已到期但仍是trial计划的用户"""
        now = datetime.utcnow()

        # 查找条件:
        # 1. plan_tier = 'trial'
        # 2. trial_ends_at < now
        # 3. plan_status != 'expired' (避免重复处理)
        query = select(User).where(
            and_(
                User.plan_tier == 'trial',
                User.trial_ends_at < now,
                User.plan_status != 'expired'
            )
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def downgrade_user_to_free(self, user: User, db: AsyncSessionLocal) -> bool:
        """将Trial用户降级到Free计划"""
        try:
            # 更新用户计划
            user.plan_tier = 'free'
            user.plan_status = 'active'
            # trial_ends_at 保留，用于记录原试用结束时间

            # 更新关联的订阅状态
            sub_query = select(Subscription).where(
                and_(
                    Subscription.user_id == user.id,
                    Subscription.status == 'active'
                )
            )
            sub_result = await db.execute(sub_query)
            subscription = sub_result.scalar_one_or_none()

            if subscription:
                subscription.status = 'canceled'
                subscription.canceled_at = datetime.utcnow()
                subscription.auto_renew = False

            # 记录日志
            logger.info(f"✅ 降级用户: {user.email} (Trial → Free)")

            return True

        except Exception as e:
            logger.error(f"❌ 降级失败 {user.email}: {e}")
            self.stats['errors'] += 1
            return False

    async def send_expiry_notification(self, user: User) -> bool:
        """发送试用到期通知"""
        # TODO: 实现邮件发送功能
        # 这里需要集成邮件服务 (如 SendGrid, AWS SES等)
        logger.info(f"📧 发送到期通知: {user.email} (功能待实现)")
        return True

    async def check_users_soon_to_expire(self, db: AsyncSessionLocal, days_ahead: int = 3) -> List[User]:
        """获取即将到期的用户（用于提醒）"""
        now = datetime.utcnow()
        reminder_date = now + timedelta(days=days_ahead)

        # 查找条件:
        # 1. plan_tier = 'trial'
        # 2. trial_ends_at 在接下来3天内
        query = select(User).where(
            and_(
                User.plan_tier == 'trial',
                User.trial_ends_at <= reminder_date,
                User.trial_ends_at > now
            )
        ).order_by(User.trial_ends_at)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def run(self):
        """执行检查任务"""
        logger.info("=" * 50)
        logger.info("Trial到期检查任务开始")
        if self.dry_run:
            logger.info("⚠️  DRY RUN 模式 - 不会实际修改数据")
        logger.info("=" * 50)

        async with AsyncSessionLocal() as db:
            try:
                # 1. 检查已到期的Trial用户
                expired_users = await self.get_expired_trial_users(db)
                self.stats['checked'] = len(expired_users)

                logger.info(f"\n📊 检查结果: 找到 {len(expired_users)} 个已到期用户")

                if expired_users:
                    logger.info("\n已到期用户列表:")
                    for user in expired_users:
                        days_expired = (datetime.utcnow() - user.trial_ends_at.replace(tzinfo=None)).days if user.trial_ends_at else 0
                        logger.info(f"  - {user.email}")
                        logger.info(f"    试用结束: {user.trial_ends_at}")
                        logger.info(f"    已过期 {days_expired} 天")

                    if not self.dry_run:
                        # 降级处理
                        for user in expired_users:
                            success = await self.downgrade_user_to_free(user, db)
                            if success:
                                self.stats['downgraded'] += 1

                                # 发送通知
                                if self.notify:
                                    if await self.send_expiry_notification(user):
                                        self.stats['notified'] += 1

                        # 提交所有更改
                        await db.commit()
                        logger.info(f"\n✅ 已降级 {self.stats['downgraded']} 个用户到Free计划")
                    else:
                        logger.info("\n⚠️  [DRY RUN] 不会执行实际降级操作")

                self.stats['expired'] = len(expired_users)

                # 2. 检查即将到期的用户（发送提醒）
                soon_to_expire = await self.check_users_soon_to_expire(db, days_ahead=3)

                if soon_to_expire:
                    logger.info(f"\n⏰ 即将到期用户 (3天内): {len(soon_to_expire)} 个")
                    for user in soon_to_expire:
                        days_left = (user.trial_ends_at.replace(tzinfo=None) - datetime.utcnow()).days
                        logger.info(f"  - {user.email} (剩余 {days_left} 天)")

                        # TODO: 发送提醒邮件
                        if not self.dry_run and self.notify:
                            await self.send_expiry_notification(user)

                    if not self.dry_run:
                        await db.commit()

                # 3. 输出统计信息
                logger.info("\n" + "=" * 50)
                logger.info("任务执行完成")
                logger.info(f"检查用户数: {self.stats['checked']}")
                logger.info(f"已到期用户: {self.stats['expired']}")
                logger.info(f"已降级用户: {self.stats['downgraded']}")
                logger.info(f"已通知用户: {self.stats['notified']}")
                logger.info(f"错误数量: {self.stats['errors']}")
                logger.info("=" * 50)

            except Exception as e:
                logger.error(f"❌ 任务执行失败: {e}")
                await db.rollback()
                raise


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Trial用户到期检查脚本')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='只显示将要处理的用户，不实际执行'
    )
    parser.add_argument(
        '--notify',
        action='store_true',
        help='发送到期通知邮件 (需要配置邮件服务)'
    )

    args = parser.parse_args()

    checker = TrialExpiryChecker(
        dry_run=args.dry_run,
        notify=args.notify
    )

    await checker.run()


if __name__ == '__main__':
    asyncio.run(main())
