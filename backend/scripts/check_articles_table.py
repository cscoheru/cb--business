#!/usr/bin/env python3
"""检查 articles 表结构"""
import asyncio
from sqlalchemy import text
from config.database import engine


async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'articles'
            ORDER BY ordinal_position;
        """))
        rows = result.fetchall()
        print("Articles table columns:")
        for row in rows:
            print(f"  {row[0]}: {row[1]}")


if __name__ == "__main__":
    asyncio.run(check())
