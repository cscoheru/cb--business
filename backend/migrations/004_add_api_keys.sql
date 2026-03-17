-- Migration: Add API Keys for Public API
-- Version: 004
-- Date: 2026-03-17
-- Description: Creates api_keys and api_usage tables for third-party developer access

-- ============================================================================
-- 1. Create api_keys table
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Key information
    key_hash VARCHAR(64) UNIQUE NOT NULL,        -- SHA256 hash of the key
    key_prefix VARCHAR(12) NOT NULL,              -- Display prefix "cb_live_abc..."
    name VARCHAR(100) NOT NULL,                   -- "Production Key"

    -- Subscription tier
    tier VARCHAR(20) NOT NULL DEFAULT 'developer', -- developer, business, enterprise

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,          -- Subscription expiry

    -- Rate limits
    rate_limit_per_minute INTEGER NOT NULL DEFAULT 60,
    rate_limit_per_day INTEGER NOT NULL DEFAULT 1000,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Comments
COMMENT ON TABLE api_keys IS 'API Keys for third-party developer access';
COMMENT ON COLUMN api_keys.key_hash IS 'SHA256 hash of the API key (key itself not stored)';
COMMENT ON COLUMN api_keys.key_prefix IS 'First 12 chars of key for display purposes';
COMMENT ON COLUMN api_keys.tier IS 'Subscription tier: developer, business, enterprise';

-- ============================================================================
-- 2. Create api_usage table
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,

    -- Request info
    endpoint VARCHAR(100) NOT NULL,               -- /orchestrator/analyze
    method VARCHAR(10) NOT NULL,                  -- POST, GET
    status_code INTEGER NOT NULL,                 -- 200, 429, 500

    -- Performance
    response_time_ms INTEGER,
    tokens_used INTEGER DEFAULT 0,                -- AI tokens consumed
    error_message VARCHAR(500),

    -- Metadata
    ip_address VARCHAR(45),                       -- IPv6 max 45 chars
    user_agent VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Comments
COMMENT ON TABLE api_usage IS 'API usage statistics for billing and rate limiting';
COMMENT ON COLUMN api_usage.tokens_used IS 'AI tokens consumed (for LLM-based endpoints)';

-- ============================================================================
-- 3. Create indexes
-- ============================================================================

-- API Keys indexes
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);
CREATE INDEX IF NOT EXISTS idx_api_keys_tier ON api_keys(tier);

-- API Usage indexes (optimized for common queries)
CREATE INDEX IF NOT EXISTS idx_api_usage_key_date ON api_usage(api_key_id, created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_status ON api_usage(status_code);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON api_usage(created_at);

-- Partial index for active keys (faster lookups)
CREATE INDEX IF NOT EXISTS idx_api_keys_active_lookup
    ON api_keys(key_hash)
    WHERE is_active = TRUE;

-- ============================================================================
-- 4. Create trigger for updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_api_keys_updated_at ON api_keys;
CREATE TRIGGER update_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 5. Create test API key for admin user (optional)
-- ============================================================================

DO $$
DECLARE
    admin_user_id UUID;
BEGIN
    -- Find admin user
    SELECT id INTO admin_user_id FROM users WHERE is_admin = TRUE LIMIT 1;

    IF admin_user_id IS NOT NULL THEN
        INSERT INTO api_keys (
            user_id,
            key_hash,
            key_prefix,
            name,
            tier,
            is_active,
            rate_limit_per_minute,
            rate_limit_per_day
        ) VALUES (
            admin_user_id,
            'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
            'cb_live_te',
            'Test Development Key',
            'developer',
            TRUE,
            60,
            1000
        ) ON CONFLICT (key_hash) DO NOTHING;

        RAISE NOTICE 'Created test API key for admin user: %', admin_user_id;
    ELSE
        RAISE NOTICE 'No admin user found, skipping test key creation';
    END IF;
END $$;

-- ============================================================================
-- 6. Verification
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'api_keys') THEN
        RAISE NOTICE '✅ api_keys table created successfully';
    ELSE
        RAISE EXCEPTION '❌ api_keys table not found';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'api_usage') THEN
        RAISE NOTICE '✅ api_usage table created successfully';
    ELSE
        RAISE EXCEPTION '❌ api_usage table not found';
    END IF;
END $$;
