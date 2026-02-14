-- Create validation_events table for Self-Learning
-- This table stores independent observations from the Validation Layer

CREATE TABLE IF NOT EXISTS validation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Correlation
    signal_id TEXT NOT NULL,
    asset TEXT NOT NULL,
    
    -- Source Data
    feed_source TEXT NOT NULL,          -- e.g., "binance_us_proxy"
    validator_price NUMERIC NOT NULL,   -- The "Real" Price found by Validator
    validator_candle JSONB,             -- Full candle data (OHLC) for deep learning
    
    -- Comparison
    check_type TEXT NOT NULL,           -- "ENTRY", "TP", "SL"
    main_system_state TEXT NOT NULL,    -- What the Main System thought (e.g., WAITING)
    
    -- The Verdict
    is_discrepancy BOOLEAN DEFAULT FALSE,
    discrepancy_type TEXT,              -- "ENTRY_DELAY", "PRICE_SLIPPAGE", etc.
    
    -- Metadata
    latency_ms INTEGER,                 -- Network latency tracking
    meta_data JSONB                     -- Extra context for AI Model
);

-- Index for fast retrieval during learning phase
CREATE INDEX IF NOT EXISTS idx_validation_signal ON validation_events(signal_id);
CREATE INDEX IF NOT EXISTS idx_validation_discrepancy ON validation_events(is_discrepancy);
CREATE INDEX IF NOT EXISTS idx_validation_created ON validation_events(created_at);

-- Comments
COMMENT ON TABLE validation_events IS 'Ground Truth data captured by Independent Validation Layer for AI Self-Learning';
