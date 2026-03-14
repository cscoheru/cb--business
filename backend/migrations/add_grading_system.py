"""
数据库迁移脚本：添加商机等级系统

为 business_opportunities 表添加基于C-P-I分数的动态等级系统
"""
import asyncio
from sqlalchemy import text
from config.database import engine


async def upgrade():
    """执行迁移"""
    async with engine.begin() as conn:
        # 1. 添加 grade 列（等级枚举）
        try:
            await conn.execute(text("""
                ALTER TABLE business_opportunities
                ADD COLUMN grade VARCHAR(20)
            """))
            print("✓ 添加 grade 列")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ grade 列已存在")
            else:
                raise

        # 2. 添加 grade_history 列（JSONB）
        try:
            await conn.execute(text("""
                ALTER TABLE business_opportunities
                ADD COLUMN grade_history JSONB DEFAULT '[]'::jsonb
            """))
            print("✓ 添加 grade_history 列")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ grade_history 列已存在")
            else:
                raise

        # 3. 添加 last_grade_change_at 列
        try:
            await conn.execute(text("""
                ALTER TABLE business_opportunities
                ADD COLUMN last_grade_change_at TIMESTAMP WITH TIME ZONE
            """))
            print("✓ 添加 last_grade_change_at 列")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ last_grade_change_at 列已存在")
            else:
                raise

        # 4. 添加 last_cpi_recalc_at 列
        try:
            await conn.execute(text("""
                ALTER TABLE business_opportunities
                ADD COLUMN last_cpi_recalc_at TIMESTAMP WITH TIME ZONE
            """))
            print("✓ 添加 last_cpi_recalc_at 列")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ last_cpi_recalc_at 列已存在")
            else:
                raise

        # 5. 添加 cpi_total_score 列（0-100范围）
        try:
            await conn.execute(text("""
                ALTER TABLE business_opportunities
                ADD COLUMN cpi_total_score FLOAT
            """))
            print("✓ 添加 cpi_total_score 列")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ cpi_total_score 列已存在")
            else:
                raise

        # 6. 添加 cpi_competition_score 列
        try:
            await conn.execute(text("""
                ALTER TABLE business_opportunities
                ADD COLUMN cpi_competition_score FLOAT
            """))
            print("✓ 添加 cpi_competition_score 列")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ cpi_competition_score 列已存在")
            else:
                raise

        # 7. 添加 cpi_potential_score 列
        try:
            await conn.execute(text("""
                ALTER TABLE business_opportunities
                ADD COLUMN cpi_potential_score FLOAT
            """))
            print("✓ 添加 cpi_potential_score 列")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ cpi_potential_score 列已存在")
            else:
                raise

        # 8. 添加 cpi_intelligence_gap_score 列
        try:
            await conn.execute(text("""
                ALTER TABLE business_opportunities
                ADD COLUMN cpi_intelligence_gap_score FLOAT
            """))
            print("✓ 添加 cpi_intelligence_gap_score 列")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ cpi_intelligence_gap_score 列已存在")
            else:
                raise

        # 9. 添加索引
        try:
            await conn.execute(text("""
                CREATE INDEX idx_business_opportunities_grade
                ON business_opportunities(grade)
            """))
            print("✓ 添加 grade 索引")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ grade 索引已存在")
            else:
                print(f"⚠ grade 索引创建失败: {e}")

        # 10. 添加 cpi_total_score 索引
        try:
            await conn.execute(text("""
                CREATE INDEX idx_business_opportunities_cpi_total_score
                ON business_opportunities(cpi_total_score)
            """))
            print("✓ 添加 cpi_total_score 索引")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ cpi_total_score 索引已存在")
            else:
                print(f"⚠ cpi_total_score 索引创建失败: {e}")

        # 11. 添加注释
        try:
            await conn.execute(text("""
                COMMENT ON COLUMN business_opportunities.grade IS '商机等级: lead(线索<60), normal(普通60-69), priority(重点70-84), landable(落地≥85)'
            """))
            await conn.execute(text("""
                COMMENT ON COLUMN business_opportunities.grade_history IS '等级变更历史记录，JSONB数组'
            """))
            await conn.execute(text("""
                COMMENT ON COLUMN business_opportunities.last_grade_change_at IS '最后等级变更时间'
            """))
            await conn.execute(text("""
                COMMENT ON COLUMN business_opportunities.last_cpi_recalc_at IS '最后CPI分数重算时间'
            """))
            await conn.execute(text("""
                COMMENT ON COLUMN business_opportunities.cpi_total_score IS 'C-P-I总分 (0-100)'
            """))
            await conn.execute(text("""
                COMMENT ON COLUMN business_opportunities.cpi_competition_score IS '竞争度分数 (40%权重)'
            """))
            await conn.execute(text("""
                COMMENT ON COLUMN business_opportunities.cpi_potential_score IS '增长潜力分数 (40%权重)'
            """))
            await conn.execute(text("""
                COMMENT ON COLUMN business_opportunities.cpi_intelligence_gap_score IS '信息差分数 (20%权重)'
            """))
            print("✓ 添加列注释")
        except Exception as e:
            print(f"⚠ 添加注释失败: {e}")

    print("\n✅ 迁移成功：business_opportunities 表已添加等级系统字段")
    print("\n等级说明:")
    print("  - lead (线索): < 60分，需进一步验证")
    print("  - normal (普通): 60-69分，保持关注")
    print("  - priority (重点): 70-84分，优先验证")
    print("  - landable (落地): ≥ 85分，可落地执行")


async def downgrade():
    """回滚迁移"""
    async with engine.begin() as conn:
        # 删除索引
        await conn.execute(text("""
            DROP INDEX IF EXISTS idx_business_opportunities_cpi_total_score
        """))
        await conn.execute(text("""
            DROP INDEX IF EXISTS idx_business_opportunities_grade
        """))

        # 删除列
        await conn.execute(text("""
            ALTER TABLE business_opportunities
            DROP COLUMN IF EXISTS cpi_intelligence_gap_score
        """))
        await conn.execute(text("""
            ALTER TABLE business_opportunities
            DROP COLUMN IF EXISTS cpi_potential_score
        """))
        await conn.execute(text("""
            ALTER TABLE business_opportunities
            DROP COLUMN IF EXISTS cpi_competition_score
        """))
        await conn.execute(text("""
            ALTER TABLE business_opportunities
            DROP COLUMN IF EXISTS cpi_total_score
        """))
        await conn.execute(text("""
            ALTER TABLE business_opportunities
            DROP COLUMN IF EXISTS last_cpi_recalc_at
        """))
        await conn.execute(text("""
            ALTER TABLE business_opportunities
            DROP COLUMN IF EXISTS last_grade_change_at
        """))
        await conn.execute(text("""
            ALTER TABLE business_opportunities
            DROP COLUMN IF EXISTS grade_history
        """))
        await conn.execute(text("""
            ALTER TABLE business_opportunities
            DROP COLUMN IF EXISTS grade
        """))

    print("✅ 回滚成功：business_opportunities 表已移除等级系统字段")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        print("开始回滚迁移...")
        asyncio.run(downgrade())
    else:
        print("开始执行迁移...")
        asyncio.run(upgrade())
