#!/usr/bin/env python3
"""检查 articles 表数据"""
import asyncio
from sqlalchemy import text
from config.database import engine


async def check():
    async with engine.begin() as conn:
        # 检查articles表数据量
        result = await conn.execute(text("SELECT COUNT(*) FROM articles;"))
        count = result.scalar()
        print(f"Articles count: {count}")

        # 检查crawl_logs表是否存在
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'crawl_logs'
            );
        """))
        crawl_logs_exists = result.scalar()
        print(f"Crawl logs table exists: {crawl_logs_exists}")

        # 检查article_tags表是否存在
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'article_tags'
            );
        """))
        article_tags_exists = result.scalar()
        print(f"Article tags table exists: {article_tags_exists}")


if __name__ == "__main__":
    asyncio.run(check())
