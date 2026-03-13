-- Migration: Create Airwallex payment tables
-- These tables support Airwallex payment gateway integration

-- Airwallex Payment Intents table
-- Tracks payment intents created in Airwallex
CREATE TABLE IF NOT EXISTS airwallex_payment_intents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID REFERENCES payments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    airwallex_intent_id VARCHAR(255) UNIQUE NOT NULL,  -- Airwallex payment intent ID
    merchant_order_id VARCHAR(255) UNIQUE NOT NULL,     -- Our internal order ID
    amount_minor INTEGER NOT NULL,                      -- Amount in fen (1 CNY = 100 fen)
    currency VARCHAR(10) DEFAULT 'CNY',
    status VARCHAR(50) DEFAULT 'requires_payment_method',
    client_token TEXT,                                  -- Token for frontend checkout
    description TEXT,
    return_url TEXT,
    metadata JSONB,                                     -- {plan_tier, billing_cycle, etc}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Airwallex Webhook Events table
-- Logs all webhook events for debugging and idempotency
CREATE TABLE IF NOT EXISTS airwallex_webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(255) UNIQUE NOT NULL,              -- Airwallex event ID
    event_type VARCHAR(100) NOT NULL,                   -- payment_intent.succeeded, etc
    status VARCHAR(50) DEFAULT 'pending',               -- pending, processed, failed
    payload JSONB NOT NULL,                             -- Full webhook payload
    signature TEXT,                                     -- Signature from header
    timestamp TIMESTAMP WITH TIME ZONE,                 -- Event timestamp
    processed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_airwallex_intents_payment_id ON airwallex_payment_intents(payment_id);
CREATE INDEX IF NOT EXISTS idx_airwallex_intents_user_id ON airwallex_payment_intents(user_id);
CREATE INDEX IF NOT EXISTS idx_airwallex_intents_aw_id ON airwallex_payment_intents(airwallex_intent_id);
CREATE INDEX IF NOT EXISTS idx_airwallex_intents_merchant_id ON airwallex_payment_intents(merchant_order_id);
CREATE INDEX IF NOT EXISTS idx_airwallex_intents_status ON airwallex_payment_intents(status);
CREATE INDEX IF NOT EXISTS idx_airwallex_intents_created_at ON airwallex_payment_intents(created_at);

CREATE INDEX IF NOT EXISTS idx_airwallex_webhooks_event_id ON airwallex_webhook_events(event_id);
CREATE INDEX IF NOT EXISTS idx_airwallex_webhooks_event_type ON airwallex_webhook_events(event_type);
CREATE INDEX IF NOT EXISTS idx_airwallex_webhooks_status ON airwallex_webhook_events(status);
CREATE INDEX IF NOT EXISTS idx_airwallex_webhooks_created_at ON airwallex_webhook_events(created_at);

-- Add comments
COMMENT ON TABLE airwallex_payment_intents IS 'Airwallex payment intent tracking';
COMMENT ON COLUMN airwallex_payment_intents.amount_minor IS 'Amount in minor units (fen for CNY)';
COMMENT ON COLUMN airwallex_payment_intents.merchant_order_id IS 'Unique order ID from our system';
COMMENT ON COLUMN airwallex_payment_intents.airwallex_intent_id IS 'Payment intent ID from Airwallex';

COMMENT ON TABLE airwallex_webhook_events IS 'Airwallex webhook event log for idempotency and debugging';
COMMENT ON COLUMN airwallex_webhook_events.event_id IS 'Unique event ID from Airwallex';
COMMENT ON COLUMN airwallex_webhook_events.payload IS 'Full webhook payload as JSONB';
