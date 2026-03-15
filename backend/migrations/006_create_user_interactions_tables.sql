-- migrations/006_create_user_interactions_tables.sql
-- 用户交互追踪表 - User Interaction Tracking Tables
-- 版本: 1.0
-- 创建日期: 2026-03-14

-- ========================================
-- 1. 用户交互事件表 (user_interactions)
-- ========================================
CREATE TABLE IF NOT EXISTS user_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 事件信息
    event_type VARCHAR(50) NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,

    -- 目标对象
    target_type VARCHAR(50),
    target_id UUID,

    -- 事件数据
    event_metadata JSONB DEFAULT '{}',
    properties JSONB DEFAULT '{}',

    -- 转化追踪
    session_id VARCHAR(100),
    funnel_stage VARCHAR(50),
    attribution JSONB DEFAULT '{}',

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- 索引
CREATE INDEX IF NOT EXISTS ix_user_interactions_user_id ON user_interactions(user_id);
CREATE INDEX IF NOT EXISTS ix_user_interactions_event_type ON user_interactions(event_type);
CREATE INDEX IF NOT EXISTS ix_user_interactions_category ON user_interactions(category);
CREATE INDEX IF NOT EXISTS ix_user_interactions_created_at ON user_interactions(created_at);
CREATE INDEX IF NOT EXISTS ix_user_interactions_user_event ON user_interactions(user_id, event_type);
CREATE INDEX IF NOT EXISTS ix_user_interactions_target ON user_interactions(target_type, target_id);
CREATE INDEX IF NOT EXISTS ix_user_interactions_funnel_stage ON user_interactions(funnel_stage);

-- ========================================
-- 2. 用户会话表 (user_sessions)
-- ========================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 会话信息
    session_id VARCHAR(100) UNIQUE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,

    -- 设备信息
    device_type VARCHAR(50),
    browser VARCHAR(50),
    os VARCHAR(50),
    ip_address VARCHAR(50),

    -- 来源追踪
    source VARCHAR(50),
    medium VARCHAR(50),
    campaign VARCHAR(100),
    referral_url TEXT,

    -- 会话统计
    page_views INTEGER DEFAULT 0,
    events_count INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,

    -- 转化漏斗
    funnel_stage VARCHAR(50),
    funnel_stages_visited JSONB DEFAULT '[]',

    -- 元数据
    meta_data JSONB DEFAULT '{}'
);

-- 索引
CREATE INDEX IF NOT EXISTS ix_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS ix_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS ix_user_sessions_started_at ON user_sessions(started_at);

-- ========================================
-- 3. 用户参与度表 (user_engagement)
-- ========================================
CREATE TABLE IF NOT EXISTS user_engagement (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 统计日期
    date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- 活跃度指标
    is_active BOOLEAN DEFAULT FALSE,
    session_count INTEGER DEFAULT 0,
    page_views INTEGER DEFAULT 0,
    events_count INTEGER DEFAULT 0,

    -- 功能使用
    cards_viewed INTEGER DEFAULT 0,
    opportunities_viewed INTEGER DEFAULT 0,
    favorites_count INTEGER DEFAULT 0,
    reports_generated INTEGER DEFAULT 0,
    searches_performed INTEGER DEFAULT 0,

    -- 参与度评分 (0-100)
    engagement_score FLOAT DEFAULT 0.0,
    activity_score FLOAT DEFAULT 0.0,
    depth_score FLOAT DEFAULT 0.0,
    growth_score FLOAT DEFAULT 0.0,

    -- 资产积累
    total_favorites INTEGER DEFAULT 0,
    total_reports INTEGER DEFAULT 0,
    total_days_active INTEGER DEFAULT 0,
    streak_days INTEGER DEFAULT 0,

    -- 转化指标
    trial_started BOOLEAN DEFAULT FALSE,
    trial_converted BOOLEAN DEFAULT FALSE,
    conversion_day INTEGER,

    -- 元数据
    meta_data JSONB DEFAULT '{}',

    -- 唯一约束
    UNIQUE(user_id, date)
);

-- 索引
CREATE INDEX IF NOT EXISTS ix_user_engagement_user_id ON user_engagement(user_id);
CREATE INDEX IF NOT EXISTS ix_user_engagement_date ON user_engagement(date);
CREATE INDEX IF NOT EXISTS ix_user_engagement_user_date ON user_engagement(user_id, date);
CREATE INDEX IF NOT EXISTS ix_user_engagement_is_active ON user_engagement(is_active);
CREATE INDEX IF NOT EXISTS ix_user_engagement_engagement_score ON user_engagement(engagement_score);

-- ========================================
-- 4. 转化事件表 (conversion_events)
-- ========================================
CREATE TABLE IF NOT EXISTS conversion_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 转化信息
    conversion_type VARCHAR(50) NOT NULL,
    conversion_stage VARCHAR(50) NOT NULL,
    conversion_value FLOAT,

    -- 事件详情
    event_data JSONB DEFAULT '{}',
    attribution JSONB DEFAULT '{}',

    -- 时间戳
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- 试用相关
    trial_days_used INTEGER,
    trial_assets JSONB
);

-- 索引
CREATE INDEX IF NOT EXISTS ix_conversion_events_user_id ON conversion_events(user_id);
CREATE INDEX IF NOT EXISTS ix_conversion_events_conversion_type ON conversion_events(conversion_type);
CREATE INDEX IF NOT EXISTS ix_conversion_events_occurred_at ON conversion_events(occurred_at);

-- ========================================
-- 5. 触发器：自动更新商机表的用户交互字段
-- ========================================
CREATE OR REPLACE FUNCTION update_opportunity_user_interactions()
RETURNS TRIGGER AS $$
BEGIN
    -- 当用户收藏机会时，自动更新 business_opportunities.user_interactions
    IF NEW.event_type IN ('favorite_card', 'favorite_opportunity') THEN
        UPDATE business_opportunities
        SET user_interactions = jsonb_set(
            COALESCE(user_interactions, '{}'),
            '{saved}',
            'true'::jsonb
        )
        WHERE id = NEW.target_id;

    -- 当用户查看机会时，增加浏览计数
    ELSIF NEW.event_type = 'view_opportunity' THEN
        UPDATE business_opportunities
        SET user_interactions = jsonb_set(
            COALESCE(user_interactions, '{}'),
            '{views}',
            COALESCE((user_interactions->>'views')::int, 0) + 1
        )
        WHERE id = NEW.target_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_opportunity_interactions
    AFTER INSERT ON user_interactions
    FOR EACH ROW
    WHEN (NEW.target_type = 'opportunity')
    EXECUTE FUNCTION update_opportunity_user_interactions();

-- ========================================
-- 6. 视图：用户行为分析视图
-- ========================================
CREATE OR REPLACE VIEW user_behavior_analysis AS
SELECT
    u.id AS user_id,
    u.email,
    u.created_at AS registration_date,

    -- 最近活动
    MAX(ui.created_at) AS last_activity_at,
    COUNT(ui.id) AS total_events,

    -- 参与度指标
    COUNT(DISTINCT CASE WHEN ui.event_type = 'view_card' THEN ui.target_id END) AS cards_viewed,
    COUNT(DISTINCT CASE WHEN ui.event_type = 'favorite_card' THEN ui.target_id END) AS favorites_count,
    COUNT(DISTINCT CASE WHEN ui.event_type = 'generate_report' THEN ui.target_id END) AS reports_generated,

    -- 当前漏斗阶段
    (SELECT funnel_stage FROM user_interactions
     WHERE user_id = u.id
     ORDER BY created_at DESC
     LIMIT 1) AS current_funnel_stage,

    -- 是否转化
    EXISTS(SELECT 1 FROM conversion_events WHERE user_id = u.id AND conversion_type = 'subscription') AS is_subscribed

FROM users u
LEFT JOIN user_interactions ui ON u.id = ui.user_id
GROUP BY u.id, u.email, u.created_at;

-- ========================================
-- 完成
-- ========================================
-- 验证表创建
DO $$
BEGIN
    RAISE NOTICE '✅ User Interaction Tracking Tables created successfully';
    RAISE NOTICE '   - user_interactions: 追踪用户事件';
    RAISE NOTICE '   - user_sessions: 追踪用户会话';
    RAISE NOTICE '   - user_engagement: 用户参与度统计';
    RAISE NOTICE '   - conversion_events: 转化事件记录';
    RAISE NOTICE '   - user_behavior_analysis: 行为分析视图';
END $$;
