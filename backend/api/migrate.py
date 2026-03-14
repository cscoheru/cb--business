# api/migrate.py
"""数据库迁移API - 用于执行migrations"""

from fastapi import APIRouter, HTTPException, Depends
import logging
from sqlalchemy import text
from config.database import AsyncSessionLocal, get_db
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/migrate", tags=["migration"])

@router.post("/execute")
async def execute_migrations(
    admin_key: str = None,
    db: AsyncSessionLocal = Depends(get_db)
):
    """
    执行数据库迁移

    创建business_opportunities和data_collection_tasks表

    Args:
        admin_key: 管理员密钥（用于简单验证）

    Returns:
        迁移结果
    """
    # 简单的admin验证
    if admin_key != settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    results = {
        "business_opportunities": "pending",
        "data_collection_tasks": "pending"
    }

    try:
        # 读取migration文件
        import os
        from pathlib import Path

        migrations_dir = Path(__file__).parent.parent / "migrations"

        # 执行business_opportunities表
        business_opps_migration = (migrations_dir / "005_create_business_opportunities_table.sql")
        if business_opps_migration.exists():
            logger.info("执行business_opportunities表migration...")
            sql_content = business_opps_migration.read_text()

            await db.execute(text(sql_content))
            await db.commit()
            results["business_opportunities"] = "completed"
            logger.info("✅ business_opportunities表创建成功")

        # 执行data_collection_tasks表
        tasks_migration = (migrations_dir / "006_create_data_collection_tasks_table.sql")
        if tasks_migration.exists():
            logger.info("执行data_collection_tasks表migration...")
            sql_content = tasks_migration.read_text()

            await db.execute(text(sql_content))
            await db.commit()
            results["data_collection_tasks"] = "completed"
            logger.info("✅ data_collection_tasks表创建成功")

        return {
            "success": True,
            "results": results,
            "message": "数据库迁移完成"
        }

    except Exception as e:
        logger.error(f"迁移失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
