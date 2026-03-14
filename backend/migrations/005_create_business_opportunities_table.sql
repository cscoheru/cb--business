-- 005_create_business_opportunities_table.sql
-- 智能商机跟踪系统 - 商机表

-- 商机状态枚举
CREATE TYPE opportunity_status AS ENUM (
    'potential',    -- 发现期：初始发现的商机
    'verifying',    -- 验证期：正在采集数据验证
    'assessing',    -- 评估期：生成可行性报告
    'executing',    -- 执行期：用户开始执行
    'archived',     -- 归档期：已完成或放弃
    'ignored',      -- 忽略：AI判断不相关
    'failed'        -- 失败：验证失败
);

-- 商机类型枚举
CREATE TYPE opportunity_type AS ENUM (
    'product',      -- 产品机会
    'policy',       -- 政策机会
    'platform',     -- 平台机会
    'brand',        -- 品牌机会
    'industry',     -- 行业机会
    'region'        -- 地区机会
);

-- 商机表
CREATE TABLE business_opportunities (
    -- 基本信息
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status opportunity_status NOT NULL DEFAULT 'potential',
    opportunity_type opportunity_type NOT NULL,

    -- 商机要素（多维度JSONB）
    elements JSONB NOT NULL DEFAULT '{}',

    -- AI分析结果
    ai_insights JSONB NOT NULL DEFAULT '{}',
    confidence_score FLOAT NOT NULL DEFAULT 0.5,
    last_verification_at TIMESTAMP WITH TIME ZONE,

    -- 用户交互
    user_interactions JSONB DEFAULT '{}',

    -- 元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archived_at TIMESTAMP WITH TIME ZONE,
    archive_reason VARCHAR(500),

    -- 索引
    CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

-- 索引
CREATE INDEX idx_bo_status ON business_opportunities(status);
CREATE INDEX idx_bo_type ON business_opportunities(opportunity_type);
CREATE INDEX idx_bo_confidence ON business_opportunities(confidence_score);
CREATE INDEX idx_bo_created ON business_opportunities(created_at DESC);
CREATE INDEX idx_bo_updated ON business_opportunities(updated_at DESC);
CREATE INDEX idx_bo_elements ON business_opportunities USING GIN(elements);

-- 自动更新 updated_at
CREATE TRIGGER update_business_opportunities_updated_at
BEFORE UPDATE ON business_opportunities
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 注释
COMMENT ON TABLE business_opportunities IS '智能商机跟踪系统 - 商机表';
COMMENT ON COLUMN business_opportunities.status IS '商机状态：potential/verifying/assessing/executing/archived/ignored/failed';
COMMENT ON COLUMN business_opportunities.opportunity_type IS '商机类型：product/policy/platform/brand/industry/region';
COMMENT ON COLUMN business_opportunities.elements IS '商机要素JSON：{product, region, platform, policy, brand, industry}';
COMMENT ON COLUMN business_opportunities.ai_insights IS 'AI分析结果JSON：{why_opportunity, key_assumptions, verification_needs, data_requirements}';
COMMENT ON COLUMN business_opportunities.confidence_score IS 'AI评估的商机可信度：0.0-1.0';
COMMENT ON COLUMN business_opportunities.user_interactions IS '用户交互JSON：{views, saved, feedback, notes}';
