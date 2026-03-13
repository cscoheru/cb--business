-- 双轨运行监控表
-- 用于记录APScheduler和OpenClaw的数据对比结果

-- 1. 数据对比日志表
CREATE TABLE IF NOT EXISTS data_comparison_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    comparison_type VARCHAR(50) NOT NULL,  -- hourly, daily, weekly

    -- APScheduler指标
    aps_count INTEGER DEFAULT 0,
    aps_avg_score FLOAT DEFAULT 0,
    aps_success_rate FLOAT DEFAULT 0,

    -- OpenClaw指标
    oc_count INTEGER DEFAULT 0,
    oc_avg_score FLOAT DEFAULT 0,
    oc_success_rate FLOAT DEFAULT 0,

    -- 对比结果
    count_diff INTEGER DEFAULT 0,
    count_diff_pct FLOAT DEFAULT 0,
    score_diff FLOAT DEFAULT 0,
    consistency_score FLOAT DEFAULT 0,

    -- 数据质量
    duplicate_count INTEGER DEFAULT 0,
    data_freshness_minutes INTEGER DEFAULT 0,

    -- 状态
    status VARCHAR(20) DEFAULT 'unknown',  -- healthy, warning, critical
    notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 创建索引
CREATE INDEX IF NOT EXISTS idx_comparison_timestamp ON data_comparison_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_comparison_type ON data_comparison_log(comparison_type);
CREATE INDEX IF NOT EXISTS idx_comparison_status ON data_comparison_log(status);
CREATE INDEX IF NOT EXISTS idx_comparison_consistency ON data_comparison_log(consistency_score);

-- 3. 创建视图 - 最近24小时对比摘要
CREATE OR REPLACE VIEW v_comparison_summary_24h AS
SELECT
    comparison_type,
    COUNT(*) as comparison_count,
    AVG(consistency_score) as avg_consistency,
    AVG(aps_count) as avg_aps_count,
    AVG(oc_count) as avg_oc_count,
    AVG(count_diff_pct) as avg_count_diff_pct,
    SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy_count,
    SUM(CASE WHEN status = 'warning' THEN 1 ELSE 0 END) as warning_count,
    SUM(CASE WHEN status = 'critical' THEN 1 ELSE 0 END) as critical_count,
    MAX(timestamp) as latest_comparison
FROM data_comparison_log
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY comparison_type;

-- 4. 创建视图 - 数据质量趋势
CREATE OR REPLACE VIEW v_data_quality_trend AS
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    AVG(consistency_score) as avg_consistency,
    AVG(aps_count) as avg_aps_count,
    AVG(oc_count) as avg_oc_count,
    AVG(duplicate_count) as avg_duplicates,
    MAX(CASE WHEN status = 'critical' THEN 1 ELSE 0 END) as has_critical
FROM data_comparison_log
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

-- 5. 添加注释
COMMENT ON TABLE data_comparison_log IS '双轨运行数据对比日志 - 记录APScheduler和OpenClaw的数据质量对比结果';
COMMENT ON VIEW v_comparison_summary_24h IS '最近24小时对比摘要视图';
COMMENT ON VIEW v_data_quality_trend IS '数据质量趋势视图 (最近7天)';

-- 6. 创建清理函数 - 删除30天前的日志
CREATE OR REPLACE FUNCTION cleanup_old_comparison_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM data_comparison_log
    WHERE timestamp < NOW() - INTERVAL '30 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 7. 为现有数据添加source标记
-- 确保可以区分APScheduler和OpenClaw的数据
UPDATE articles
SET source = CASE
    WHEN source LIKE 'openclaw-%' THEN source
    WHEN source IS NULL OR source = '' THEN 'unknown'
    ELSE 'apscheduler-' || source
END
WHERE source NOT LIKE 'apscheduler-%'
  AND source NOT LIKE 'openclaw-%';

-- 8. 创建触发器 - 自动标记新文章来源
CREATE OR REPLACE FUNCTION tag_article_source()
RETURNS TRIGGER AS $$
BEGIN
    -- 如果source为空或未标记，添加默认标记
    IF NEW.source IS NULL OR NEW.source = '' THEN
        NEW.source := 'apscheduler-unknown';
    ELSIF NEW.source NOT LIKE 'apscheduler-%' AND NEW.source NOT LIKE 'openclaw-%' THEN
        NEW.source := 'apscheduler-' || NEW.source;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_tag_article_source ON articles;
CREATE TRIGGER trigger_tag_article_source
    BEFORE INSERT ON articles
    FOR EACH ROW
    EXECUTE FUNCTION tag_article_source();

-- 完成
SELECT 'Dual track monitoring tables created successfully' as status;
