#!/usr/bin/env python3
"""
数据库迁移脚本：添加文章相关表
"""
import asyncio
from sqlalchemy import text
from config.database import engine


async def migrate():
    """执行迁移"""
    async with engine.begin() as conn:
        # 创建 articles 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS articles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR(500) NOT NULL,
                summary TEXT,
                full_content TEXT,
                link VARCHAR(1000) UNIQUE NOT NULL,
                source VARCHAR(100) NOT NULL,
                language VARCHAR(10) DEFAULT 'zh',
                content_theme VARCHAR(50),
                region VARCHAR(50),
                platform VARCHAR(50),
                tags TEXT,
                risk_level VARCHAR(20),
                opportunity_score FLOAT,
                author VARCHAR(200),
                published_at TIMESTAMP WITH TIME ZONE,
                crawled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                is_processed BOOLEAN DEFAULT FALSE,
                is_published BOOLEAN DEFAULT FALSE
            );
        """))

        # 创建 article_tags 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS article_tags (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                tag VARCHAR(100) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))

        # 创建 crawl_logs 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS crawl_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                source VARCHAR(100) NOT NULL,
                status VARCHAR(20) NOT NULL,
                articles_count INTEGER DEFAULT 0,
                error_message TEXT,
                started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                completed_at TIMESTAMP WITH TIME ZONE
            );
        """))

        # 创建索引 - 单独执行每个
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_articles_link ON articles(link);"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_articles_is_processed ON articles(is_processed);"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at DESC);"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_article_tags_article_id ON article_tags(article_id);"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_article_tags_tag ON article_tags(tag);"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_crawl_logs_source ON crawl_logs(source);"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_crawl_logs_started_at ON crawl_logs(started_at DESC);"
        ))

        print("✅ Articles tables migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
