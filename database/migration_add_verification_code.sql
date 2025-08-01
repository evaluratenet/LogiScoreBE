-- Migration: Add verification code fields to users table
-- Run this in your Supabase SQL Editor

-- Add verification code columns
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS verification_code VARCHAR(6),
ADD COLUMN IF NOT EXISTS verification_code_expires TIMESTAMP WITH TIME ZONE;

-- Create index for verification code lookups
CREATE INDEX IF NOT EXISTS idx_users_verification_code ON users(verification_code);

-- Create index for verification code expiry
CREATE INDEX IF NOT EXISTS idx_users_verification_code_expires ON users(verification_code_expires); 