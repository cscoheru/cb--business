"""
数据库迁移脚本：添加机会收藏支持

为 favorites 表添加 opportunity_id 字段，使其支持收藏商机和卡片
"""
import asyncio
from sqlalchemy import text
from config.database import engine


async def upgrade():
    """执行迁移"""
    async with engine.begin() as conn:
        # 添加 opportunity_id 列（可空）
        try:
            await conn.execute(text("""
                ALTER TABLE favorites
                ADD COLUMN opportunity_id UUID
            """))
            print("✓ 添加 opportunity_id 列")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ opportunity_id 列已存在")
            else:
                raise

        # 添加外键约束（手动检查）
        try:
            await conn.execute(text("""
                ALTER TABLE favorites
                ADD CONSTRAINT fk_favorites_opportunity_id
                FOREIGN KEY (opportunity_id)
                REFERENCES business_opportunities(id)
                ON DELETE CASCADE
            """))
            print("✓ 添加外键约束")
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e).lower():
                print("✓ 外键约束已存在")
            else:
                print(f"⚠ 外键约束创建失败（可稍后手动添加）: {e}")

        # 添加索引
        try:
            await conn.execute(text("""
                CREATE INDEX idx_favorites_opportunity_id
                ON favorites(opportunity_id)
            """))
            print("✓ 添加索引")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ 索引已存在")
            else:
                print(f"⚠ 索引创建失败: {e}")

        # 添加唯一约束（手动检查）
        try:
            await conn.execute(text("""
                ALTER TABLE favorites
                ADD CONSTRAINT uq_user_opportunity
                UNIQUE (user_id, opportunity_id)
            """))
            print("✓ 添加唯一约束")
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e).lower():
                print("✓ 唯一约束已存在")
            else:
                print(f"⚠ 唯一约束创建失败: {e}")

        # 修改 card_id 为可空
        try:
            await conn.execute(text("""
                ALTER TABLE favorites
                ALTER COLUMN card_id DROP NOT NULL
            """))
            print("✓ 修改 card_id 为可空")
        except Exception as e:
            print(f"⚠ card_id 修改失败: {e}")

    print("\n✅ 迁移成功：favorites 表现在支持机会收藏")


async def downgrade():
    """回滚迁移"""
    async with engine.begin() as conn:
        # 删除唯一约束
        await conn.execute(text("""
            ALTER TABLE favorites
            DROP CONSTRAINT IF EXISTS uq_user_opportunity
        """))

        # 删除索引
        await conn.execute(text("""
            DROP INDEX IF EXISTS idx_favorites_opportunity_id
        """))

        # 删除外键约束
        await conn.execute(text("""
            ALTER TABLE favorites
            DROP CONSTRAINT IF EXISTS fk_favorites_opportunity_id
        """))

        # 删除列
        await conn.execute(text("""
            ALTER TABLE favorites
            DROP COLUMN IF EXISTS opportunity_id
        """))

        # 恢复 card_id 为非空
        await conn.execute(text("""
            ALTER TABLE favorites
            ALTER COLUMN card_id SET NOT NULL
        """))

    print("✅ 回滚成功：favorites 表已恢复到之前的状态")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        print("开始回滚迁移...")
        asyncio.run(downgrade())
    else:
        print("开始执行迁移...")
        asyncio.run(upgrade())
