-- ============================================
-- MIGRATION: v1 (Market Now) → v2 (Future Entry)
-- Date: 2026-01-30
-- COPY AND PASTE THIS ENTIRE FILE INTO SUPABASE SQL EDITOR
-- ============================================

-- PHASE 1: ADD NEW COLUMNS
ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS state VARCHAR(50) DEFAULT 'WAITING_FOR_ENTRY';
ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS entry_price DECIMAL(10, 5);
ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS entry_hit_at TIMESTAMPTZ;
ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS tp DECIMAL(10, 5);
ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS sl DECIMAL(10, 5);
ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS entry_low DECIMAL(10, 5);
ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS entry_high DECIMAL(10, 5);
ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS result VARCHAR(20);
ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS expiry_at TIMESTAMPTZ;
ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ;
ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS strength DECIMAL(5, 4);
ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS reward_risk_ratio DECIMAL(5, 2);
ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS strategy VARCHAR(50) DEFAULT 'Alpha v1';
ALTER TABLE fx_signals ADD COLUMN IF NOT EXISTS explainability TEXT;

-- PHASE 2: MIGRATE EXISTING DATA
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

UPDATE fx_signals 
SET entry_price = entry_low
WHERE entry_price IS NULL AND entry_low IS NOT NULL;

UPDATE fx_signals 
SET expiry_at = generated_at + INTERVAL '15 minutes'
WHERE expiry_at IS NULL AND state = 'WAITING_FOR_ENTRY';

-- PHASE 3: ADD INDEXES FOR PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_fx_signals_state ON fx_signals(state);
CREATE INDEX IF NOT EXISTS idx_fx_signals_expiry ON fx_signals(expiry_at) WHERE state = 'WAITING_FOR_ENTRY';
CREATE INDEX IF NOT EXISTS idx_fx_signals_entry_hit ON fx_signals(entry_hit_at);
CREATE INDEX IF NOT EXISTS idx_fx_signals_active ON fx_signals(state, generated_at DESC) WHERE state IN ('WAITING_FOR_ENTRY', 'ENTRY_HIT');

-- PHASE 4: ADD CONSTRAINTS
ALTER TABLE fx_signals ADD CONSTRAINT chk_state_valid CHECK (state IN ('CREATED', 'WAITING_FOR_ENTRY', 'ENTRY_HIT', 'TP_HIT', 'SL_HIT', 'CANCELLED'));
ALTER TABLE fx_signals ADD CONSTRAINT chk_result_valid CHECK (result IS NULL OR result IN ('PROFIT', 'LOSS', 'CANCELLED'));

-- PHASE 5: UPDATE LIFECYCLE TABLE
ALTER TABLE fx_signal_lifecycle ADD COLUMN IF NOT EXISTS state_from VARCHAR(50);
ALTER TABLE fx_signal_lifecycle ADD COLUMN IF NOT EXISTS state_to VARCHAR(50);

-- VERIFICATION: Check column additions
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'fx_signals'
ORDER BY ordinal_position;
