-- 006_create_data_collection_tasks_table.sql
-- 智能商机跟踪系统 - 数据采集任务表

-- 任务状态枚举
CREATE TYPE collection_task_status AS ENUM (
    'pending',      -- 待执行
    'running',      -- 执行中
    'completed',    -- 已完成
    'failed',       -- 失败
    'cancelled'     -- 已取消
);

-- 任务优先级枚举
CREATE TYPE collection_task_priority AS ENUM (
    'high',         -- 高优先级
    'medium',       -- 中优先级
    'low'           -- 低优先级
);

-- 数据采集任务表
CREATE TABLE data_collection_tasks (
    -- 基本信息
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES business_opportunities(id) ON DELETE CASCADE,

    -- 任务定义
    task_type VARCHAR(100) NOT NULL,  -- product_search, review_monitoring, price_tracking等
    priority collection_task_priority NOT NULL DEFAULT 'medium',

    -- AI的需求
    ai_request JSONB NOT NULL,  -- AI提出的问题和需求
    expected_outcome JSONB,     -- AI期望的结果格式

    -- OpenClaw执行
    channel_name VARCHAR(100),  -- openclaw channel名称
    execution_params JSONB,     -- 传递给channel的参数

    -- 状态与结果
    status collection_task_status NOT NULL DEFAULT 'pending',
    result JSONB,               -- 采集结果
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- 时间跟踪
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- AI反馈
    ai_feedback JSONB,          -- AI对数据质量的反馈
    usefulness_score FLOAT,     -- 0-1, 数据对AI判断的帮助程度
    CONSTRAINT valid_usefulness CHECK (usefulness_score IS NULL OR (usefulness_score >= 0 AND usefulness_score <= 1))
);

-- 索引
CREATE INDEX idx_dct_opportunity ON data_collection_tasks(opportunity_id);
CREATE INDEX idx_dct_status ON data_collection_tasks(status);
CREATE INDEX idx_dct_priority ON data_collection_tasks(priority);
CREATE INDEX idx_dct_created ON data_collection_tasks(created_at DESC);
CREATE INDEX idx_dct_channel ON data_collection_tasks(channel_name);

-- 自动更新 updated_at (如果添加该字段)
-- CREATE TRIGGER update_data_collection_tasks_updated_at
-- BEFORE UPDATE ON data_collection_tasks
-- FOR EACH ROW
-- EXECUTE FUNCTION update_updated_at_column();

-- 注释
COMMENT ON TABLE data_collection_tasks IS '智能商机跟踪系统 - 数据采集任务表';
COMMENT ON COLUMN data_collection_tasks.opportunity_id IS '关联的商机ID';
COMMENT ON COLUMN data_collection_tasks.task_type IS '任务类型：product_search/review_monitoring/price_tracking/social_sentiment等';
COMMENT ON COLUMN data_collection_tasks.ai_request IS 'AI的数据需求JSON：{question, data_needed, constraints}';
COMMENT ON COLUMN data_collection_tasks.channel_name IS 'OpenClaw channel名称';
COMMENT ON COLUMN data_collection_tasks.result IS '采集结果JSON';
COMMENT ON COLUMN data_collection_tasks.usefulness_score IS 'AI评估的数据有用性：0.0-1.0';
