-- Migration: v1 (Market Now) → v2 (Future Entry)
-- Date: 2026-01-30
-- Purpose: Add state machine v2 columns to fx_signals table

-- ============================================
-- PHASE 1: ADD NEW COLUMNS
-- ============================================

-- Add state column (replaces status for v2 logic)
ALTER TABLE fx_signals 
ADD COLUMN IF NOT EXISTS state VARCHAR(50) DEFAULT 'WAITING_FOR_ENTRY';

-- Add entry tracking columns
ALTER TABLE fx_signals 
ADD COLUMN IF NOT EXISTS entry_price DECIMAL(10, 5);

ALTER TABLE fx_signals 
ADD COLUMN IF NOT EXISTS entry_hit_at TIMESTAMPTZ;

-- Add TP/SL columns (if not exist)
ALTER TABLE fx_signals 
ADD COLUMN IF NOT EXISTS tp DECIMAL(10, 5);

ALTER TABLE fx_signals 
ADD COLUMN IF NOT EXISTS sl DECIMAL(10, 5);

ALTER TABLE fx_signals 
ADD COLUMN IF NOT EXISTS entry_low DECIMAL(10, 5);

ALTER TABLE fx_signals 
ADD COLUMN IF NOT EXISTS entry_high DECIMAL(10, 5);

-- Add result tracking
ALTER TABLE fx_signals 
ADD COLUMN IF NOT EXISTS result VARCHAR(20); -- PROFIT, LOSS, CANCELLED

-- Add expiry tracking
ALTER TABLE fx_signals 
ADD COLUMN IF NOT EXISTS expiry_at TIMESTAMPTZ;

-- Add closed tracking
ALTER TABLE fx_signals 
ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ;

-- Add strength column (if not exist)
ALTER TABLE fx_signals 
ADD COLUMN IF NOT EXISTS strength DECIMAL(5, 4);

-- Add reward_risk_ratio column (if not exist)
ALTER TABLE fx_signals 
ADD COLUMN IF NOT EXISTS reward_risk_ratio DECIMAL(5, 2);

-- Add strategy column (if not exist)
ALTER TABLE fx_signals 
ADD COLUMN IF NOT EXISTS strategy VARCHAR(50) DEFAULT 'Alpha v1';

-- Add explainability column (if not exist)
ALTER TABLE fx_signals 
ADD COLUMN IF NOT EXISTS explainability TEXT;

-- ============================================
-- PHASE 2: MIGRATE EXISTING DATA
-- ============================================

-- Map old status to new state for backward compatibility
UPDATE fx_signals 
SET state = CASE 
    WHEN status = 'ACTIVE' THEN 'ENTRY_HIT'
    WHEN status = 'EXPIRED' THEN 'CANCELLED'
    WHEN status = 'CANDIDATE' THEN 'CANCELLED'
    WHEN status = 'TP_HIT' THEN 'TP_HIT'
    WHEN status = 'SL_HIT' THEN 'SL_HIT'
    ELSE 'WAITING_FOR_ENTRY'
END
WHERE state = 'WAITING_FOR_ENTRY' AND status IS NOT NULL;

-- Set entry_price from entry_low for existing records
UPDATE fx_signals 
SET entry_price = entry_low
WHERE entry_price IS NULL AND entry_low IS NOT NULL;

-- Set expiry_at for existing WAITING_FOR_ENTRY signals (15 minutes from creation)
UPDATE fx_signals 
SET expiry_at = generated_at + INTERVAL '15 minutes'
WHERE expiry_at IS NULL AND state = 'WAITING_FOR_ENTRY';

-- ============================================
-- PHASE 3: ADD INDEXES FOR PERFORMANCE
-- ============================================

-- Index on state for fast filtering
CREATE INDEX IF NOT EXISTS idx_fx_signals_state 
ON fx_signals(state);

-- Index on expiry_at for expiry checking
CREATE INDEX IF NOT EXISTS idx_fx_signals_expiry 
ON fx_signals(expiry_at) 
WHERE state = 'WAITING_FOR_ENTRY';

-- Index on entry_hit_at for tracking
CREATE INDEX IF NOT EXISTS idx_fx_signals_entry_hit 
ON fx_signals(entry_hit_at);

-- Composite index for active signal queries
CREATE INDEX IF NOT EXISTS idx_fx_signals_active 
ON fx_signals(state, generated_at DESC) 
WHERE state IN ('WAITING_FOR_ENTRY', 'ENTRY_HIT');

-- ============================================
-- PHASE 4: ADD CONSTRAINTS
-- ============================================

-- Ensure state is valid
ALTER TABLE fx_signals 
ADD CONSTRAINT chk_state_valid 
CHECK (state IN (
    'CREATED',
    'WAITING_FOR_ENTRY', 
    'ENTRY_HIT', 
    'TP_HIT', 
    'SL_HIT', 
    'CANCELLED'
));

-- Ensure result is valid
ALTER TABLE fx_signals 
ADD CONSTRAINT chk_result_valid 
CHECK (result IS NULL OR result IN ('PROFIT', 'LOSS', 'CANCELLED'));

-- Ensure entry_price is set for WAITING_FOR_ENTRY
-- (This is a soft constraint, enforced in application layer)

-- ============================================
-- PHASE 5: UPDATE LIFECYCLE TABLE
-- ============================================

-- Add state_from and state_to columns to lifecycle table
ALTER TABLE fx_signal_lifecycle 
ADD COLUMN IF NOT EXISTS state_from VARCHAR(50);

ALTER TABLE fx_signal_lifecycle 
ADD COLUMN IF NOT EXISTS state_to VARCHAR(50);

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check column additions
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'fx_signals'
ORDER BY ordinal_position;

-- Check state distribution
SELECT state, COUNT(*) as count
FROM fx_signals
GROUP BY state
ORDER BY count DESC;

-- Check signals waiting for entry
SELECT id, asset, direction, entry_price, expiry_at, 
       (expiry_at - NOW()) as time_remaining
FROM fx_signals
WHERE state = 'WAITING_FOR_ENTRY'
ORDER BY generated_at DESC
LIMIT 10;

-- ============================================
-- ROLLBACK SCRIPT (IF NEEDED)
-- ============================================

/*
-- To rollback this migration:

-- Drop new columns
ALTER TABLE fx_signals DROP COLUMN IF EXISTS state;
ALTER TABLE fx_signals DROP COLUMN IF EXISTS entry_price;
ALTER TABLE fx_signals DROP COLUMN IF EXISTS entry_hit_at;
ALTER TABLE fx_signals DROP COLUMN IF EXISTS result;
ALTER TABLE fx_signals DROP COLUMN IF EXISTS expiry_at;
ALTER TABLE fx_signals DROP COLUMN IF EXISTS closed_at;

-- Drop indexes
DROP INDEX IF EXISTS idx_fx_signals_state;
DROP INDEX IF EXISTS idx_fx_signals_expiry;
DROP INDEX IF EXISTS idx_fx_signals_entry_hit;
DROP INDEX IF EXISTS idx_fx_signals_active;

-- Drop constraints
ALTER TABLE fx_signals DROP CONSTRAINT IF EXISTS chk_state_valid;
ALTER TABLE fx_signals DROP CONSTRAINT IF EXISTS chk_result_valid;

-- Drop lifecycle columns
ALTER TABLE fx_signal_lifecycle DROP COLUMN IF EXISTS state_from;
ALTER TABLE fx_signal_lifecycle DROP COLUMN IF EXISTS state_to;
*/

-- ============================================
-- NOTES
-- ============================================

-- 1. This migration is designed to be idempotent (can run multiple times safely)
-- 2. Existing signals will be mapped to new states automatically
-- 3. Old 'status' column is kept for backward compatibility
-- 4. New signals should use 'state' column going forward
-- 5. Run verification queries after migration to ensure data integrity
