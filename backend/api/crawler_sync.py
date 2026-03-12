# api/crawler_sync.py
"""同步版本的爬虫 API - 用于解决连接问题"""
from fastapi import APIRouter, Query
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/crawler-sync", tags=["crawler-sync"])

# 数据库连接配置
DB_CONFIG = {
    "host": "postgres",
    "port": 5432,
    "database": "cbdb",
    "user": "cbuser",
    "password": os.getenv("POSTGRES_PASSWORD", "k8VmK8PvqAFlEdirpJVJNo8DPe2bVlYPtV6xea+DlQ=")
}


def get_db_connection():
    """获取同步数据库连接"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


@router.get("/articles")
async def get_articles_sync(
    region: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """获取文章列表（同步版本）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 构建查询条件
        conditions = ["is_processed = true"]
        params = []

        if region:
            conditions.append("region = %s")
            params.append(region)
        if country:
            conditions.append("country = %s")
            params.append(country)

        where_clause = " AND ".join(conditions)

        # 计算总数
        count_query = f"SELECT COUNT(*) as total FROM articles WHERE {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]

        # 获取文章
        offset = (page - 1) * per_page
        query = f"""
            SELECT id, title, summary, link, source, language, content_theme,
                   region, country, platform, published_at, created_at, opportunity_score
            FROM articles
            WHERE {where_clause}
            ORDER BY published_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([per_page, offset])

        cursor.execute(query, params)
        articles = cursor.fetchall()

        cursor.close()
        conn.close()

        # 转换为响应格式
        article_list = []
        for article in articles:
            article_list.append({
                "id": str(article["id"]),
                "title": article["title"] or "",
                "summary": article["summary"] or "",
                "full_content": "",
                "link": article["link"] or "",
                "source": article["source"] or "",
                "language": article["language"] or "",
                "content_theme": article["content_theme"],
                "region": article["region"],
                "country": article["country"],
                "platform": article["platform"],
                "published_at": article["published_at"].isoformat() if article["published_at"] else None,
                "created_at": article["created_at"].isoformat() if article["created_at"] else None,
                "opportunity_score": article["opportunity_score"]
            })

        return {
            "articles": article_list,
            "total": total,
            "page": page,
            "per_page": per_page
        }

    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        return {
            "articles": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "error": str(e)
        }


@router.get("/stats")
async def get_stats_sync():
    """获取统计信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 总文章数
        cursor.execute("SELECT COUNT(*) as total FROM articles WHERE is_processed = true")
        total = cursor.fetchone()["total"]

        # 按地区统计
        cursor.execute("""
            SELECT region, COUNT(*) as count
            FROM articles
            WHERE is_processed = true AND region IS NOT NULL
            GROUP BY region
        """)
        by_region = {row["region"]: row["count"] for row in cursor.fetchall()}

        # 最新文章时间
        cursor.execute("SELECT MAX(published_at) as latest FROM articles")
        latest = cursor.fetchone()["latest"]

        cursor.close()
        conn.close()

        return {
            "total_articles": total,
            "by_region": by_region,
            "latest_published_at": latest.isoformat() if latest else None
        }

    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {"error": str(e)}
