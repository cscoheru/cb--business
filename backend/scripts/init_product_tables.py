#!/usr/bin/env python3
"""初始化产品数据表"""

import asyncio
import logging
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from config.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_products_table():
    """创建products表"""
    sql = """
    CREATE TABLE IF NOT EXISTS products (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        title VARCHAR(500) NOT NULL,
        description TEXT,
        category VARCHAR(100),
        subcategory VARCHAR(100),
        tags JSONB,
        price FLOAT NOT NULL,
        original_price FLOAT,
        currency VARCHAR(10) DEFAULT 'USD',
        price_range VARCHAR(50),
        platform VARCHAR(50) NOT NULL,
        country VARCHAR(10),
        platform_product_id VARCHAR(200),
        shop_id VARCHAR(100),
        rank INTEGER,
        sold_count INTEGER DEFAULT 0,
        rating FLOAT,
        reviews_count INTEGER DEFAULT 0,
        trend_rank INTEGER,
        trend_direction VARCHAR(10),
        trend_days_on_list INTEGER DEFAULT 0,
        image_url TEXT,
        product_url TEXT,
        source VARCHAR(100),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        opportunity_score FLOAT,
        difficulty_score FLOAT,
        profit_margin FLOAT,
        ai_insights JSONB
    );
    """

    async with engine.begin() as conn:
        await conn.execute(text(sql))
        logger.info("✅ products table created")

        # 创建索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_platform ON products(platform);",
            "CREATE INDEX IF NOT EXISTS idx_products_country ON products(country);",
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);",
            "CREATE INDEX IF NOT EXISTS idx_products_sold_count ON products(sold_count);",
        ]

        for idx_sql in indexes:
            await conn.execute(text(idx_sql))

        logger.info(f"✅ Created {len(indexes)} indexes for products table")


async def create_product_reviews_table():
    """创建product_reviews表"""
    sql = """
    CREATE TABLE IF NOT EXISTS product_reviews (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        product_id UUID,
        platform VARCHAR(50) NOT NULL,
        country VARCHAR(10),
        platform_review_id VARCHAR(200),
        rating INTEGER,
        title VARCHAR(500),
        content TEXT,
        translated_content TEXT,
        author_name VARCHAR(200),
        author_verified BOOLEAN DEFAULT FALSE,
        review_date TIMESTAMP WITH TIME ZONE,
        helpful_count INTEGER DEFAULT 0,
        media_urls JSONB,
        sentiment FLOAT,
        sentiment_label VARCHAR(20),
        keywords JSONB,
        topics JSONB,
        pain_points JSONB,
        mentioned_features JSONB,
        tags JSONB,
        source VARCHAR(100),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """

    async with engine.begin() as conn:
        await conn.execute(text(sql))
        logger.info("✅ product_reviews table created")

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_reviews_product ON product_reviews(product_id);",
            "CREATE INDEX IF NOT EXISTS idx_reviews_platform ON product_reviews(platform);",
            "CREATE INDEX IF NOT EXISTS idx_reviews_country ON product_reviews(country);",
            "CREATE INDEX IF NOT EXISTS idx_reviews_rating ON product_reviews(rating);",
        ]

        for idx_sql in indexes:
            await conn.execute(text(idx_sql))

        logger.info(f"✅ Created {len(indexes)} indexes for product_reviews table")


async def create_product_review_summaries_table():
    """创建product_review_summaries表"""
    sql = """
    CREATE TABLE IF NOT EXISTS product_review_summaries (
        product_id UUID PRIMARY KEY,
        total_reviews INTEGER DEFAULT 0,
        average_rating FLOAT,
        rating_distribution JSONB,
        sentiment_score FLOAT,
        positive_ratio FLOAT,
        negative_ratio FLOAT,
        top_keywords JSONB,
        top_topics JSONB,
        top_pain_points JSONB,
        vs_competitors JSONB,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """

    async with engine.begin() as conn:
        await conn.execute(text(sql))
        logger.info("✅ product_review_summaries table created")


async def create_product_tables():
    """创建所有产品相关表"""
    try:
        await create_products_table()
        await create_product_reviews_table()
        await create_product_review_summaries_table()

        logger.info("=" * 50)
        logger.info("🎉 All product tables created successfully!")
        logger.info("=" * 50)

        return {
            "success": True,
            "message": "Product tables created successfully",
            "tables": ["products", "product_reviews", "product_review_summaries"]
        }

    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    asyncio.run(create_product_tables())
