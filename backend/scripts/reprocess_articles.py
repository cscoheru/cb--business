#!/usr/bin/env python3
"""
重新处理现有文章 - 更新区域和主题分类
使用改进的 MockAIProcessor 重新分析所有 region='global' 的文章
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from config.database import async_session_maker
from models.article import Article
from crawler.processors.ai_processor import MockAIProcessor


async def reprocess_articles():
    """重新处理所有 global 区域的文章"""
    processor = MockAIProcessor()

    async with async_session_maker() as db:
        # 查找所有 region='global' 的文章
        result = await db.execute(
            select(Article).where(Article.region == 'global')
        )
        articles = result.scalars().all()

        print(f"找到 {len(articles)} 篇需要重新分类的文章")

        updated_count = 0
        for article in articles:
            # 重新分析文章
            article_data = {
                "title": article.title,
                "summary": article.summary or "",
                "full_content": article.full_content or "",
                "source": article.source
            }

            analysis = await processor.analyze_article(article_data)

            # 更新字段
            article.region = analysis.get("region", "global")
            article.content_theme = analysis.get("content_theme", "guide")
            article.platform = analysis.get("platform", "other")
            article.risk_level = analysis.get("risk_level", "low")
            article.opportunity_score = analysis.get("opportunity_score", 0.5)

            # 更新标签
            import json
            article.tags = json.dumps(analysis.get("tags", ["跨境电商"]))

            updated_count += 1

            if updated_count % 10 == 0:
                print(f"已处理 {updated_count}/{len(articles)} 篇文章...")

        # 提交更改
        await db.commit()
        print(f"\n✅ 成功更新 {updated_count} 篇文章!")


if __name__ == "__main__":
    asyncio.run(reprocess_articles())
