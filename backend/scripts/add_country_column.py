#!/usr/bin/env python3
"""
添加 country 列到 articles 表

使用方法:
    python scripts/add_country_column.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from config.database import AsyncSessionLocal


async def add_country_column():
    """添加 country 列到 articles 表"""

    async with AsyncSessionLocal() as session:
        try:
            # 检查 country 列是否已存在
            check_sql = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'articles'
                AND column_name = 'country';
            """

            result = await session.execute(text(check_sql))
            exists = result.first()

            if exists:
                print("✓ country 列已存在，跳过添加")
                return

            # 添加 country 列
            add_sql = """
                ALTER TABLE articles
                ADD COLUMN country VARCHAR(10);
            """

            await session.execute(text(add_sql))
            await session.commit()

            print("✓ 成功添加 country 列到 articles 表")

            # 为已有数据设置默认 country 值（基于 region 推断）
            update_sql = """
                UPDATE articles
                SET country = CASE
                    WHEN region = 'southeast_asia' THEN
                        CASE
                            WHEN title ILIKE '%泰国%' OR title ILIKE '%Thailand%' OR title ILIKE '%Shopee泰国%' THEN 'th'
                            WHEN title ILIKE '%越南%' OR title ILIKE '%Vietnam%' OR title ILIKE '%Lazada越南%' THEN 'vn'
                            WHEN title ILIKE '%马来西亚%' OR title ILIKE '%Malaysia%' OR title ILIKE '%TikTok马来西亚%' THEN 'my'
                            ELSE 'th'  -- 默认泰国
                        END
                    WHEN region = 'north_america' THEN 'us'
                    WHEN region = 'latin_america' THEN
                        CASE
                            WHEN title ILIKE '%巴西%' OR title ILIKE '%Brazil%' OR title ILIKE '%Mercadolivre%' THEN 'br'
                            WHEN title ILIKE '%墨西哥%' OR title ILIKE '%Mexico%' THEN 'mx'
                            ELSE 'br'  -- 默认巴西
                        END
                    ELSE NULL
                END
                WHERE country IS NULL;
            """

            await session.execute(text(update_sql))
            await session.commit()

            print("✓ 成功更新已有数据的 country 值")

            # 创建索引
            index_sql = """
                CREATE INDEX IF NOT EXISTS idx_articles_country
                ON articles(country);
            """

            await session.execute(text(index_sql))
            await session.commit()

            print("✓ 成功创建 country 列索引")

        except Exception as e:
            await session.rollback()
            print(f"✗ 迁移失败: {e}")
            raise


if __name__ == "__main__":
    print("开始数据库迁移: 添加 country 列")
    asyncio.run(add_country_column())
    print("迁移完成!")
