-- Migration: Add extra_data column to payments table
ALTER TABLE payments ADD COLUMN IF NOT EXISTS extra_data TEXT;