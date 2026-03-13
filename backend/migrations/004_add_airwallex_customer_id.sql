-- Migration: Add Airwallex Customer ID to users table
-- Date: 2026-03-13

-- Add airwallex_customer_id column to users table
ALTER TABLE users
ADD COLUMN airwallex_customer_id VARCHAR(255);

-- Create index for faster lookups
CREATE INDEX idx_users_airwallex_customer_id ON users(airwallex_customer_id);

-- Add comment
COMMENT ON COLUMN users.airwallex_customer_id IS 'Airwallex customer ID for recurring payments';
