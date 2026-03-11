#!/usr/bin/env python3
"""
手动刷新爬虫 - 快速获取新文章
运行方式: python3 scripts/refresh_articles.py
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from scheduler.tasks import execute_crawl, crawl_retail_dive, crawl_shopify_blog, crawl_cifnews, crawl_techcrunch
from config.database import AsyncSessionLocal
from models.article import Article
from sqlalchemy import select, func
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def refresh_all_sources():
    """刷新所有已启用的数据源"""
    sources = ["retail_dive", "shopify_blog", "cifnews", "techcrunch"]

    total_new = 0
    results = {}

    for source in sources:
        try:
            logger.info(f"🔄 开始刷新 {source}...")
            result = await execute_crawl(source)
            results[source] = result

            if result and result.get("new_count", 0) > 0:
                total_new += result["new_count"]
                logger.info(f"✅ {source}: 新增 {result['new_count']} 篇文章")
            else:
                logger.info(f"ℹ️ {source}: 无新文章")

        except Exception as e:
            logger.error(f"❌ {source}: 爬取失败 - {e}")
            results[source] = {"success": False, "error": str(e)}

    # 显示当前文章总数
    async with AsyncSessionLocal() as db:
        count = await db.execute(func.count(Article.id))
        total_articles = count.scalar() or 0

    print("\n" + "="*60)
    print(f"📊 爬取结果汇总")
    print("="*60)
    for source, result in results.items():
        if result.get("success"):
            new_count = result.get("new_count", 0)
            skipped = result.get("skipped", False)
            if skipped:
                print(f"  {source:20s} | ⏭️  最近已爬取，跳过")
            else:
                print(f"  {source:20s} | ✅ 新增 {new_count} 篇文章")
        else:
            error = result.get("error", "未知错误")
            print(f"  {source:20s} | ❌ {error}")

    print("-"*60)
    print(f"  📚 数据库文章总数: {total_articles} 篇")
    print("="*60)

    print("\n💡 提示:")
    print("  - 定时爬虫每30分钟自动运行")
    print("  - 刷新前端页面即可看到最新文章")
    print("  - 目前所有文章自动发布，无需审核")


async def check_article_count():
    """检查当前文章数量"""
    async with AsyncSessionLocal() as db:
        count = await db.execute(func.count(Article.id))
        total = count.scalar() or 0

        # 按来源统计
        source_count = await db.execute(
            select(Article.source, func.count(Article.id))
            .group_by(Article.source)
        )

        print(f"\n📚 当前数据库: {total} 篇文章\n")

        print("来源分布:")
        for row in source_count:
            print(f"  {row[0]:20s} | {row[1]:4} 篇")

        return total


async def main():
    """主函数 - 在单个事件循环中运行所有任务"""
    print("🔄 手动刷新爬虫")
    print("="*60)

    # 先显示当前状态
    await check_article_count()

    print("\n开始刷新所有数据源...\n")
    await refresh_all_sources()


if __name__ == "__main__":
    # 使用单个事件循环运行所有任务
    asyncio.run(main())
