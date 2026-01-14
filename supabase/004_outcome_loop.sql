-- Quantix AI Core - Outcome Feedback Loop Schema
-- Phase 2: From Prediction to Behavioral Memory

-- 1. Signal Registry: Track every issued signal
CREATE TABLE IF NOT EXISTS trade_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset VARCHAR(15) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    direction VARCHAR(10) NOT NULL, -- BUY / SELL
    entry_low NUMERIC(18, 10) NOT NULL,
    entry_high NUMERIC(18, 10) NOT NULL,
    tp NUMERIC(18, 10) NOT NULL,
    sl NUMERIC(18, 10) NOT NULL,
    
    confidence NUMERIC(5, 4),    -- confidence at time of signal
    signal_context JSONB,       -- session, pattern, regime, etc
    
    issued_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    
    status VARCHAR(20) DEFAULT 'OPEN', -- OPEN / HIT_TP / HIT_SL / EXPIRED
    resolved_at TIMESTAMPTZ,
    
    reward_risk_ratio NUMERIC(5, 2)
);

CREATE INDEX IF NOT EXISTS idx_signal_asset_time 
ON trade_signals(asset, timeframe, issued_at);

-- 2. Trade Outcome Scoring: Forex-grade R-multiple tracking
CREATE TABLE IF NOT EXISTS trade_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES trade_signals(id) ON DELETE CASCADE,
    outcome VARCHAR(20),         -- HIT_TP / HIT_SL / EXPIRED
    r_multiple NUMERIC(5, 2),    -- +1.4 / -1.0 / 0
    duration_minutes INTEGER,
    resolved_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Confidence Adjustment: Bayesian-style learning trail
CREATE TABLE IF NOT EXISTS confidence_adjustments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset VARCHAR(15),
    timeframe VARCHAR(10),
    pattern_hash VARCHAR(64),
    
    prior_confidence NUMERIC(5, 4),
    outcome VARCHAR(20),
    r_multiple NUMERIC(5, 2),
    
    adjusted_confidence NUMERIC(5, 4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Pattern Memory: Long-term statistical behavior
CREATE TABLE IF NOT EXISTS pattern_stats (
    pattern_hash VARCHAR(64) PRIMARY KEY,
    asset VARCHAR(15),
    timeframe VARCHAR(10),
    
    total_signals INTEGER DEFAULT 0,
    win_count INTEGER DEFAULT 0,
    loss_count INTEGER DEFAULT 0,
    expectancy NUMERIC(10, 4) DEFAULT 0,
    avg_r_win NUMERIC(5, 2) DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS Enforcement
ALTER TABLE trade_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE trade_outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE confidence_adjustments ENABLE ROW LEVEL SECURITY;
ALTER TABLE pattern_stats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read signals" ON trade_signals FOR SELECT USING (true);
CREATE POLICY "Public read outcomes" ON trade_outcomes FOR SELECT USING (true);
CREATE POLICY "Public read adjustments" ON confidence_adjustments FOR SELECT USING (true);
CREATE POLICY "Public read patterns" ON pattern_stats FOR SELECT USING (true);
