-- CB Business Database Schema
-- Database: crawler_db
-- Created: 2025-03-10

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- User Management Tables
-- ============================================

-- 用户表
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255),
  name VARCHAR(100),
  phone VARCHAR(20),
  avatar_url TEXT,
  plan_tier VARCHAR(20) DEFAULT 'free' CHECK (plan_tier IN ('free', 'pro', 'enterprise')),
  plan_status VARCHAR(20) DEFAULT 'active' CHECK (plan_status IN ('active', 'canceled', 'expired', 'suspended')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_login_at TIMESTAMP WITH TIME ZONE,
  region_preference VARCHAR(50),
  currency_preference VARCHAR(10) DEFAULT 'CNY'
);

-- 订阅表
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan_tier VARCHAR(20) NOT NULL CHECK (plan_tier IN ('free', 'pro', 'enterprise')),
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'canceled', 'expired', 'pending')),
  billing_cycle VARCHAR(10) CHECK (billing_cycle IN ('monthly', 'quarterly', 'annual')),
  amount DECIMAL(10,2),
  currency VARCHAR(10) DEFAULT 'CNY',
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  expires_at TIMESTAMP WITH TIME ZONE,
  canceled_at TIMESTAMP WITH TIME ZONE,
  auto_renew BOOLEAN DEFAULT TRUE,
  payment_method VARCHAR(50),
  external_subscription_id VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 支付记录表
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
  amount DECIMAL(10,2) NOT NULL,
  currency VARCHAR(10) DEFAULT 'CNY',
  payment_method VARCHAR(50) NOT NULL CHECK (payment_method IN ('wechat', 'alipay', 'stripe', 'paypal')),
  payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'processing', 'completed', 'failed', 'refunded')),
  transaction_id VARCHAR(255) UNIQUE,
  external_order_id VARCHAR(255),
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE
);

-- 用户使用记录表
CREATE TABLE user_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  usage_type VARCHAR(50) NOT NULL CHECK (usage_type IN ('api_call', 'article_view', 'opportunity_access', 'report_download', 'search_query')),
  quantity INTEGER DEFAULT 1,
  period_date DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- Content Tables
-- ============================================

-- 文章表（扩展原有结构）
CREATE TABLE articles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  summary TEXT,
  content TEXT,
  source VARCHAR(50),
  url TEXT UNIQUE,
  published_at TIMESTAMP WITH TIME ZONE,
  crawled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  region VARCHAR(50),
  country VARCHAR(50),
  platform VARCHAR(50),
  content_theme VARCHAR(20) CHECK (content_theme IN ('market_insight', 'policy_update', 'case_study', 'tutorial', 'news')),
  subcategory VARCHAR(50),
  tags TEXT[],
  risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
  opportunity_score DECIMAL(3,2),
  slug TEXT UNIQUE,
  meta_description TEXT,
  is_published BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 机会表
CREATE TABLE opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  region VARCHAR(50) NOT NULL,
  country VARCHAR(50),
  product_category VARCHAR(50),
  opportunity_type VARCHAR(50) CHECK (opportunity_type IN ('product', 'market', 'platform', 'niche')),
  title TEXT,
  description TEXT,
  opportunity_score DECIMAL(3,2),
  estimated_market_size BIGINT,
  competition_level VARCHAR(20) CHECK (competition_level IN ('low', 'medium', 'high', 'saturated')),
  growth_potential VARCHAR(20) CHECK (growth_potential IN ('low', 'moderate', 'high', 'explosive')),
  entry_difficulty INTEGER CHECK (entry_difficulty BETWEEN 1 AND 10),
  data_sources JSONB,
  valid_until TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 风险预警表
CREATE TABLE risk_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_type VARCHAR(50) CHECK (alert_type IN ('policy', 'tariff', 'platform', 'logistics', 'payment')),
  severity VARCHAR(20) CHECK (severity IN ('info', 'warning', 'critical')),
  title TEXT,
  description TEXT,
  affected_regions TEXT[],
  affected_platforms TEXT[],
  affected_categories TEXT[],
  mitigation_actions JSONB,
  source_url TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  resolved_at TIMESTAMP WITH TIME ZONE
);

-- 成本参考表
CREATE TABLE cost_references (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  region VARCHAR(50) NOT NULL,
  country VARCHAR(50),
  platform VARCHAR(50),
  cost_type VARCHAR(50) CHECK (cost_type IN ('platform_fee', 'shipping', 'storage', 'advertising', 'payment', 'tax', 'other')),
  cost_item TEXT,
  amount DECIMAL(10,2),
  currency VARCHAR(10),
  frequency VARCHAR(20) CHECK (frequency IN ('one_time', 'monthly', 'quarterly', 'annual', 'per_transaction', 'per_order')),
  effective_date TIMESTAMP WITH TIME ZONE,
  valid_until TIMESTAMP WITH TIME ZONE
);

-- ============================================
-- Indexes for Performance
-- ============================================

-- User indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_plan_tier ON users(plan_tier);
CREATE INDEX idx_users_plan_status ON users(plan_status);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Subscription indexes
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_expires_at ON subscriptions(expires_at);

-- Payment indexes
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(payment_status);
CREATE INDEX idx_payments_transaction_id ON payments(transaction_id);
CREATE INDEX idx_payments_created_at ON payments(created_at);

-- User usage indexes
CREATE INDEX idx_user_usage_user_date ON user_usage(user_id, period_date);
CREATE INDEX idx_user_usage_type ON user_usage(usage_type);

-- Article indexes
CREATE INDEX idx_articles_region ON articles(region);
CREATE INDEX idx_articles_theme ON articles(content_theme);
CREATE INDEX idx_articles_published ON articles(published_at DESC);
CREATE INDEX idx_articles_is_published ON articles(is_published);
CREATE INDEX idx_articles_slug ON articles(slug);
CREATE INDEX idx_articles_tags ON articles USING GIN(tags);

-- Opportunity indexes
CREATE INDEX idx_opportunities_region ON opportunities(region);
CREATE INDEX idx_opportunities_type ON opportunities(opportunity_type);
CREATE INDEX idx_opportunities_score ON opportunities(opportunity_score DESC);
CREATE INDEX idx_opportunities_valid ON opportunities(valid_until);

-- Risk alert indexes
CREATE INDEX idx_risk_alerts_active ON risk_alerts(is_active);
CREATE INDEX idx_risk_alerts_severity ON risk_alerts(severity);
CREATE INDEX idx_risk_alerts_regions ON risk_alerts USING GIN(affected_regions);

-- Cost reference indexes
CREATE INDEX idx_cost_references_region ON cost_references(region);
CREATE INDEX idx_cost_references_type ON cost_references(cost_type);
CREATE INDEX idx_cost_references_effective ON cost_references(effective_date);

-- ============================================
-- Functions for automatic timestamp updates
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Initial Data (Optional)
-- ============================================

-- Insert a default admin user (password: admin123 - CHANGE THIS!)
-- This is commented out for security. Uncomment and modify as needed.
/*
INSERT INTO users (email, password_hash, name, plan_tier, plan_status)
VALUES (
  'admin@cb-business.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aqLaKx8U9s0m',
  'System Admin',
  'enterprise',
  'active'
);
*/

-- ============================================
-- Grant permissions (if needed)
-- ============================================

-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- ============================================
-- Schema verification queries
-- ============================================

-- Verify all tables were created:
-- \dt

-- Verify indexes:
-- \di

-- Count tables:
-- SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
-- Expected: 8 tables

-- Count indexes:
-- SELECT count(*) FROM pg_indexes WHERE schemaname = 'public';
-- Expected: 25+ indexes
