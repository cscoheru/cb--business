-- Migration: Fix user_id type in subscriptions and user_usage tables
-- This migration changes user_id from VARCHAR to UUID to match the users table

-- Fix subscriptions table
ALTER TABLE subscriptions
ALTER COLUMN user_id TYPE UUID USING user_id::UUID;

-- Fix user_usage table
ALTER TABLE user_usage
ALTER COLUMN user_id TYPE UUID USING user_id::UUID;

-- Fix payments table
ALTER TABLE payments
ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
