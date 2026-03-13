#!/usr/bin/env python3
"""
双轨运行数据对比监控脚本

每小时执行一次，对比APScheduler和OpenClaw的数据质量和一致性。

使用方法:
    python backend/scripts/dual_track_monitor.py

输出:
    - 控制台报告
    - 数据库日志记录
    - 可选的Webhook通知
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func, and_, text
from config.database import AsyncSessionLocal, engine
from models.article import Article
from models.card import Card
from services.notification_service import send_monitoring_report

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DualTrackMonitor:
    """双轨运行监控器"""

    def __init__(self):
        self.now = datetime.now()
        self.one_hour_ago = self.now - timedelta(hours=1)
        self.two_hours_ago = self.now - timedelta(hours=2)
        self.twenty_four_hours_ago = self.now - timedelta(hours=24)

    async def get_ap_scheduler_stats(self):
        """获取APScheduler统计数据"""
        async with AsyncSessionLocal() as db:
            # 文章统计
            article_result = await db.execute(
                select(
                    func.count(Article.id).label('total_count'),
                    func.count(
                        func.nullif(Article.is_processed, False)
                    ).label('processed_count'),
                    func.avg(Article.opportunity_score).label('avg_score'),
                    func.max(Article.crawled_at).label('latest_update')
                ).where(
                    Article.crawled_at >= self.one_hour_ago
                )
            )
            article_stats = article_result.first()

            # Cards统计
            card_result = await db.execute(
                select(
                    func.count(Card.id).label('total_count'),
                    func.count(
                        func.nullif(Card.amazon_data.isnot(None), False)
                    ).label('with_products'),
                    func.max(Card.created_at).label('latest_update')
                ).where(
                    Card.created_at >= self.one_hour_ago
                )
            )
            card_stats = card_result.first()

            return {
                'articles': {
                    'total': article_stats.total_count or 0,
                    'processed': article_stats.processed_count or 0,
                    'avg_score': float(article_stats.avg_score or 0),
                    'latest_update': article_stats.latest_update
                },
                'cards': {
                    'total': card_stats.total_count or 0,
                    'with_products': card_stats.with_products or 0,
                    'latest_update': card_stats.latest_update
                }
            }

    async def get_openclaw_stats(self):
        """获取OpenClaw统计数据"""
        async with AsyncSessionLocal() as db:
            # OpenClaw文章统计
            article_result = await db.execute(
                select(
                    func.count(Article.id).label('total_count'),
                    func.count(
                        func.nullif(Article.is_processed, False)
                    ).label('processed_count'),
                    func.avg(Article.opportunity_score).label('avg_score'),
                    func.max(Article.crawled_at).label('latest_update')
                ).where(
                    and_(
                        Article.source == 'openclaw-rss',
                        Article.crawled_at >= self.one_hour_ago
                    )
                )
            )
            article_stats = article_result.first()

            return {
                'articles': {
                    'total': article_stats.total_count or 0,
                    'processed': article_stats.processed_count or 0,
                    'avg_score': float(article_stats.avg_score or 0),
                    'latest_update': article_stats.latest_update
                }
            }

    async def check_data_freshness(self):
        """检查数据新鲜度"""
        async with AsyncSessionLocal() as db:
            # 检查最新数据时间
            result = await db.execute(
                select(
                    func.max(Article.crawled_at).label('latest_article'),
                    func.max(Card.created_at).label('latest_card')
                )
            )
            stats = result.first()

            now = datetime.now()
            article_age = (now.replace(tzinfo=None) - stats.latest_article.replace(tzinfo=None)).total_seconds() / 60 if stats.latest_article else 999
            card_age = (now.replace(tzinfo=None) - stats.latest_card.replace(tzinfo=None)).total_seconds() / 60 if stats.latest_card else 999

            return {
                'article_age_minutes': int(article_age),
                'card_age_minutes': int(card_age),
                'status': 'fresh' if max(article_age, card_age) < 120 else 'stale'
            }

    async def check_duplicates(self):
        """检查重复数据"""
        async with AsyncSessionLocal() as db:
            # 检查过去24小时的文章重复
            result = await db.execute(
                select(
                    Article.link,
                    func.count(Article.id).label('count')
                )
                .where(
                    and_(
                        Article.crawled_at >= self.twenty_four_hours_ago,
                        Article.link.isnot(None)
                    )
                )
                .group_by(Article.link)
                .having(func.count(Article.id) > 1)
            )
            duplicates = result.all()

            duplicate_links = [row.link for row in duplicates]

            return {
                'duplicate_count_24h': len(duplicate_links),
                'duplicate_links': duplicate_links[:10],  # 最多返回10个
                'status': 'ok' if len(duplicate_links) < 5 else 'warning'
            }

    async def check_database_health(self):
        """检查数据库健康状态"""
        try:
            async with AsyncSessionLocal() as db:
                # 测试查询
                await db.execute(
                    select(func.count()).select_from(Article)
                )
                return {'status': 'healthy', 'message': 'Database responsive'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': str(e)}

    def calculate_consistency_score(self, aps_stats, oc_stats):
        """计算一致性评分"""
        # 文章数量一致性
        aps_articles = aps_stats['articles']['total']
        oc_articles = oc_stats['articles']['total']

        if aps_articles == 0 and oc_articles == 0:
            count_score = 1.0
        elif aps_articles == 0 or oc_articles == 0:
            count_score = 0.5
        else:
            ratio = min(aps_articles, oc_articles) / max(aps_articles, oc_articles)
            count_score = ratio

        # 评分一致性
        aps_score = aps_stats['articles']['avg_score']
        oc_score = oc_stats['articles']['avg_score']

        if aps_score == 0 and oc_score == 0:
            score_diff_score = 1.0
        else:
            score_diff = abs(aps_score - oc_score)
            score_diff_score = max(0, 1 - score_diff)

        # 综合评分
        consistency = (count_score * 0.7 + score_diff_score * 0.3)
        return consistency

    async def generate_report(self):
        """生成完整的监控报告"""
        logger.info("开始生成双轨运行监控报告...")

        # 收集各项指标
        aps_stats = await self.get_ap_scheduler_stats()
        oc_stats = await self.get_openclaw_stats()
        freshness = await self.check_data_freshness()
        duplicates = await self.check_duplicates()
        db_health = await self.check_database_health()

        # 计算一致性评分
        consistency_score = self.calculate_consistency_score(aps_stats, oc_stats)

        # 计算数据完整性
        aps_completeness = (
            aps_stats['articles']['processed'] / aps_stats['articles']['total']
            if aps_stats['articles']['total'] > 0 else 0
        )
        oc_completeness = (
            oc_stats['articles']['processed'] / oc_stats['articles']['total']
            if oc_stats['articles']['total'] > 0 else 0
        )

        # 综合健康评分
        health_score = (
            consistency_score * 0.4 +
            aps_completeness * 0.3 +
            oc_completeness * 0.3
        )

        # 确定整体状态
        if health_score > 0.8 and duplicates['duplicate_count_24h'] < 5:
            overall_status = 'healthy'
        elif health_score > 0.6 and duplicates['duplicate_count_24h'] < 20:
            overall_status = 'warning'
        else:
            overall_status = 'critical'

        report = {
            'timestamp': self.now.isoformat(),
            'monitoring_period': {
                'start': self.one_hour_ago.isoformat(),
                'end': self.now.isoformat()
            },
            'apscheduler': {
                'articles_last_hour': aps_stats['articles']['total'],
                'articles_processed': aps_stats['articles']['processed'],
                'avg_opportunity_score': round(aps_stats['articles']['avg_score'], 3),
                'latest_update': aps_stats['articles']['latest_update'].isoformat() if aps_stats['articles']['latest_update'] else None,
                'cards_last_hour': aps_stats['cards']['total'],
                'cards_with_products': aps_stats['cards']['with_products']
            },
            'openclaw': {
                'articles_last_hour': oc_stats['articles']['total'],
                'articles_processed': oc_stats['articles']['processed'],
                'avg_opportunity_score': round(oc_stats['articles']['avg_score'], 3),
                'latest_update': oc_stats['articles']['latest_update'].isoformat() if oc_stats['articles']['latest_update'] else None
            },
            'comparison': {
                'count_diff': oc_stats['articles']['total'] - aps_stats['articles']['total'],
                'count_diff_pct': round(
                    ((oc_stats['articles']['total'] - aps_stats['articles']['total']) /
                     max(aps_stats['articles']['total'], 1)) * 100, 1
                ) if aps_stats['articles']['total'] > 0 else 0,
                'score_diff': round(oc_stats['articles']['avg_score'] - aps_stats['articles']['avg_score'], 3),
                'consistency_score': round(consistency_score, 3),
                'data_completeness': {
                    'apscheduler': round(aps_completeness, 3),
                    'openclaw': round(oc_completeness, 3)
                }
            },
            'data_quality': {
                'article_age_minutes': freshness['article_age_minutes'],
                'card_age_minutes': freshness['card_age_minutes'],
                'duplicate_count_24h': duplicates['duplicate_count_24h'],
                'duplicate_sample': duplicates['duplicate_links'][:5]
            },
            'health': {
                'database': db_health['status'],
                'overall_status': overall_status,
                'health_score': round(health_score, 3),
                'consistency_score': round(consistency_score, 3)
            }
        }

        return report

    def print_report(self, report):
        """打印报告到控制台"""
        print("\n" + "=" * 60)
        print(f"双轨运行监控报告 - {report['timestamp']}")
        print("=" * 60)

        print("\n【数据采集对比】(过去1小时)")
        print(f"  APScheduler:")
        print(f"    文章数: {report['apscheduler']['articles_last_hour']}")
        print(f"    已处理: {report['apscheduler']['articles_processed']}")
        print(f"    平均评分: {report['apscheduler']['avg_opportunity_score']}")
        print(f"    Cards: {report['apscheduler']['cards_last_hour']}")

        print(f"\n  OpenClaw:")
        print(f"    文章数: {report['openclaw']['articles_last_hour']}")
        print(f"    已处理: {report['openclaw']['articles_processed']}")
        print(f"    平均评分: {report['openclaw']['avg_opportunity_score']}")

        print("\n【对比分析】")
        print(f"  数量差异: {report['comparison']['count_diff']:+d} ({report['comparison']['count_diff_pct']:+.1f}%)")
        print(f"  评分差异: {report['comparison']['score_diff']:+.3f}")
        print(f"  一致性评分: {report['comparison']['consistency_score']:.1%}")
        print(f"  数据完整性:")
        print(f"    APScheduler: {report['comparison']['data_completeness']['apscheduler']:.1%}")
        print(f"    OpenClaw: {report['comparison']['data_completeness']['openclaw']:.1%}")

        print("\n【数据质量】")
        print(f"  最新文章: {report['data_quality']['article_age_minutes']}分钟前")
        print(f"  最新Card: {report['data_quality']['card_age_minutes']}分钟前")
        print(f"  24h重复数: {report['data_quality']['duplicate_count_24h']}")

        print("\n【健康状态】")
        status_emoji = {
            'healthy': '✅',
            'warning': '⚠️ ',
            'critical': '❌'
        }
        emoji = status_emoji.get(report['health']['overall_status'], '❓')
        print(f"  {emoji} 整体状态: {report['health']['overall_status'].upper()}")
        print(f"  健康评分: {report['health']['health_score']:.1%}")
        print(f"  数据库: {report['health']['database']}")

        print("\n" + "=" * 60)

        # 打印警告信息
        if report['health']['overall_status'] == 'warning':
            print("⚠️  警告:")
            if report['data_quality']['duplicate_count_24h'] > 5:
                print(f"   - 发现 {report['data_quality']['duplicate_count_24h']} 个重复文章")
            if report['comparison']['consistency_score'] < 0.7:
                print(f"   - 数据一致性较低 ({report['comparison']['consistency_score']:.1%})")

        elif report['health']['overall_status'] == 'critical':
            print("❌ 严重问题:")
            if report['data_quality']['article_age_minutes'] > 120:
                print(f"   - 数据过时 ({report['data_quality']['article_age_minutes']}分钟前)")
            if report['health']['database'] != 'healthy':
                print(f"   - 数据库异常")

    async def save_to_database(self, report):
        """保存报告到数据库"""
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    text("""
                        INSERT INTO data_comparison_log (
                            timestamp, comparison_type,
                            aps_count, aps_avg_score, aps_success_rate,
                            oc_count, oc_avg_score, oc_success_rate,
                            count_diff, count_diff_pct, score_diff,
                            consistency_score, status, notes
                        ) VALUES (
                            :timestamp, 'hourly',
                            :aps_count, :aps_avg_score, :aps_success_rate,
                            :oc_count, :oc_avg_score, :oc_success_rate,
                            :count_diff, :count_diff_pct, :score_diff,
                            :consistency_score, :status, :notes
                        )
                    """),
                    {
                        'timestamp': self.now,
                        'aps_count': report['apscheduler']['articles_last_hour'],
                        'aps_avg_score': report['apscheduler']['avg_opportunity_score'],
                        'aps_success_rate': report['comparison']['data_completeness']['apscheduler'],
                        'oc_count': report['openclaw']['articles_last_hour'],
                        'oc_avg_score': report['openclaw']['avg_opportunity_score'],
                        'oc_success_rate': report['comparison']['data_completeness']['openclaw'],
                        'count_diff': report['comparison']['count_diff'],
                        'count_diff_pct': report['comparison']['count_diff_pct'] / 100,
                        'score_diff': report['comparison']['score_diff'],
                        'consistency_score': report['comparison']['consistency_score'],
                        'status': report['health']['overall_status'],
                        'notes': f"Duplicates: {report['data_quality']['duplicate_count_24h']}"
                    }
                )
            logger.info("报告已保存到数据库")
        except Exception as e:
            logger.error(f"保存报告失败: {e}")


async def main():
    """主函数"""
    monitor = DualTrackMonitor()

    try:
        # 生成报告
        report = await monitor.generate_report()

        # 打印报告
        monitor.print_report(report)

        # 保存到数据库
        await monitor.save_to_database(report)

        # 发送通知 (仅在WARNING或CRITICAL状态时)
        if report['health']['overall_status'] in ['warning', 'critical']:
            logger.info("Sending notification due to warning/critical status...")
            await send_monitoring_report(report)
        elif report['health']['overall_status'] == 'healthy':
            # 健康状态也发送通知（可以用于确认系统正常运行）
            # 只在每天的第一次运行时发送（例如凌晨0点）
            current_hour = datetime.now().hour
            if current_hour == 0:
                await send_monitoring_report(report)

        # 根据状态决定退出码
        if report['health']['overall_status'] == 'healthy':
            return 0
        elif report['health']['overall_status'] == 'warning':
            return 1
        else:
            return 2

    except Exception as e:
        logger.error(f"监控失败: {e}", exc_info=True)
        return 3


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
