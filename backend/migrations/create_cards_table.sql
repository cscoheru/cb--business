-- 创建cards表
CREATE TABLE IF NOT EXISTS cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    analysis JSONB NOT NULL,
    amazon_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    is_published BOOLEAN DEFAULT FALSE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_cards_created_at ON cards(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cards_category ON cards(category);
CREATE INDEX IF NOT EXISTS idx_cards_published ON cards(is_published, published_at);

-- 添加注释
COMMENT ON TABLE cards IS '每日信息卡片表';
COMMENT ON COLUMN cards.category IS '产品分类: wireless_earbuds, smart_plugs, fitness_trackers';
COMMENT ON COLUMN cards.content IS '卡片完整内容 (JSON)';
COMMENT ON COLUMN cards.analysis IS 'AI分析结果 (JSON)';
COMMENT ON COLUMN cards.amazon_data IS '原始Amazon数据 (JSON)';
COMMENT ON COLUMN cards.views IS '浏览次数';
COMMENT ON COLUMN cards.likes IS '收藏次数';
