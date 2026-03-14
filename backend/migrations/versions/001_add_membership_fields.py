"""Add membership system fields

Revision ID: 001_add_membership_fields
Revises:
Create Date: 2026-03-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_add_membership_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add membership fields to users table
    op.add_column('users', sa.Column('registration_plan_choice', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('trial_reminder_shown', sa.TIMESTAMP(timezone=True), nullable=True))

    # Add locking fields to business_opportunities table
    op.add_column('business_opportunities', sa.Column('is_locked', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('business_opportunities', sa.Column('locked_at', sa.TIMESTAMP(timezone=True), nullable=True))

    # Create index for locked opportunities
    op.create_index(
        'idx_business_opportunities_locked',
        'business_opportunities',
        ['is_locked', 'user_id'],
        postgresql_where=sa.text('is_locked = TRUE')
    )

    # Create index for trial users
    op.create_index(
        'idx_users_trial_ends_at',
        'users',
        ['trial_ends_at'],
        postgresql_where=sa.text("plan_tier = 'trial'")
    )

    # Create daily_api_usage table for rate limiting
    op.create_table(
        'daily_api_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('usage_date', sa.Date(), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('call_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('user_id', 'usage_date', 'endpoint', name='uq_daily_api_usage_user_endpoint')
    )
    op.create_index(
        'idx_daily_api_usage_user_date',
        'daily_api_usage',
        ['user_id', 'usage_date']
    )

    # Create daily_card_views table for view tracking
    op.create_table(
        'daily_card_views',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('view_date', sa.Date(), nullable=False),
        sa.Column('card_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('view_count', sa.Integer(), server_default='1'),
        sa.Column('first_viewed_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()')),
        sa.UniqueConstraint('user_id', 'view_date', 'card_id', name='uq_daily_card_views_user_date_card')
    )
    op.create_index(
        'idx_daily_card_views_user_date',
        'daily_card_views',
        ['user_id', 'view_date']
    )


def downgrade():
    # Drop tables
    op.drop_index('idx_daily_card_views_user_date', table_name='daily_card_views')
    op.drop_table('daily_card_views')

    op.drop_index('idx_daily_api_usage_user_date', table_name='daily_api_usage')
    op.drop_table('daily_api_usage')

    # Drop indexes
    op.drop_index('idx_users_trial_ends_at', table_name='users')
    op.drop_index('idx_business_opportunities_locked', table_name='business_opportunities')

    # Remove columns
    op.drop_column('business_opportunities', 'locked_at')
    op.drop_column('business_opportunities', 'is_locked')

    op.drop_column('users', 'trial_reminder_shown')
    op.drop_column('users', 'registration_plan_choice')
