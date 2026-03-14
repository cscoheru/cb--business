"""
Migration 002: 添加商机与卡片/文章的关联字段

执行:
  alembic revision --autogenerate -m "add opportunity relations"
  alembic upgrade head
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_add_opportunity_relations'
down_revision = '001_add_membership_fields'
branch_labels = None
depends_on = None


def upgrade():
    """添加关联字段"""

    # 添加关联字段到 business_opportunities 表
    op.add_column('business_opportunities',
        sa.Column('card_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column('business_opportunities',
        sa.Column('article_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column('business_opportunities',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True)
    )

    # 创建外键约束
    op.create_foreign_key(
        'fk_bo_card_id',
        'business_opportunities', 'cards',
        ['card_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_bo_article_id',
        'business_opportunities', 'articles',
        ['article_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_bo_user_id',
        'business_opportunities', 'users',
        ['user_id'], ['id'],
        ondelete='SET NULL'
    )

    # 创建索引以提升查询性能
    op.create_index(
        'idx_bo_card_id',
        'business_opportunities',
        ['card_id']
    )
    op.create_index(
        'idx_bo_article_id',
        'business_opportunities',
        ['article_id']
    )
    op.create_index(
        'idx_bo_user_id',
        'business_opportunities',
        ['user_id']
    )


def downgrade():
    """移除关联字段"""

    # 删除索引
    op.drop_index('idx_bo_user_id', table_name='business_opportunities')
    op.drop_index('idx_bo_article_id', table_name='business_opportunities')
    op.drop_index('idx_bo_card_id', table_name='business_opportunities')

    # 删除外键
    op.drop_constraint('fk_bo_user_id', 'business_opportunities', type_='foreignkey')
    op.drop_constraint('fk_bo_article_id', 'business_opportunities', type_='foreignkey')
    op.drop_constraint('fk_bo_card_id', 'business_opportunities', type_='foreignkey')

    # 删除列
    op.drop_column('business_opportunities', 'user_id')
    op.drop_column('business_opportunities', 'article_id')
    op.drop_column('business_opportunities', 'card_id')
