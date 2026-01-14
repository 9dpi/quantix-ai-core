-- ============================================================================
-- QUANTIX AI CORE v3.2 - CONTINUOUS LEARNING SCHEMA
-- ============================================================================
-- This schema implements the 3-layer memory architecture:
-- 1. market_candles_clean (Validated market data)
-- 2. signal_outcomes (Learning source - proven results)
-- 3. learning_memory (The brain - pattern intelligence)
-- ============================================================================

-- ============================================================================
-- LAYER 1: CLEAN MARKET MEMORY
-- ============================================================================
-- Only candles that pass the Forex-grade Quality Gate are stored here
-- This is NOT a data lake - it's a curated memory of tradable moments

CREATE TABLE IF NOT EXISTS market_candles_clean (
    time TIMESTAMPTZ NOT NULL,
    asset VARCHAR(10) NOT NULL,
    timeframe VARCHAR(5) NOT NULL,
    open DECIMAL(10, 5) NOT NULL,
    high DECIMAL(10, 5) NOT NULL,
    low DECIMAL(10, 5) NOT NULL,
    close DECIMAL(10, 5) NOT NULL,
    volume INTEGER DEFAULT 0,
    spread DECIMAL(6, 5),
    session VARCHAR(20), -- 'london', 'newyork', 'overlap', 'asia'
    quality_score DECIMAL(3, 2) DEFAULT 1.0, -- 0.0 to 1.0
    high_impact_news BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, asset, timeframe)
);

CREATE INDEX idx_candles_asset_time ON market_candles_clean(asset, time DESC);
CREATE INDEX idx_candles_session ON market_candles_clean(session) WHERE session IN ('london', 'newyork', 'overlap');

COMMENT ON TABLE market_candles_clean IS 'Forex-grade validated candles. Only data that passed Quality Gate.';
COMMENT ON COLUMN market_candles_clean.quality_score IS 'Composite score: spread + range + volume + session validity';
COMMENT ON COLUMN market_candles_clean.high_impact_news IS 'Binary flag: learning disabled during high-impact news';

-- ============================================================================
-- LAYER 2: SIGNAL OUTCOMES (Learning Source)
-- ============================================================================
-- This is where Quantix LEARNS from. Not from candles, but from RESULTS.

CREATE TABLE IF NOT EXISTS signal_outcomes (
    signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset VARCHAR(10) NOT NULL,
    timeframe VARCHAR(5) NOT NULL,
    direction VARCHAR(4) NOT NULL CHECK (direction IN ('BUY', 'SELL')),
    
    -- Entry context
    entry_price DECIMAL(10, 5) NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL,
    session VARCHAR(20),
    volatility_state VARCHAR(20), -- 'low', 'normal', 'high', 'extreme'
    
    -- Exit levels
    tp_price DECIMAL(10, 5) NOT NULL,
    sl_price DECIMAL(10, 5) NOT NULL,
    
    -- Outcome (THE TRUTH)
    result VARCHAR(10) CHECK (result IN ('TP', 'SL', 'EXPIRED', 'PENDING')),
    exit_price DECIMAL(10, 5),
    exit_time TIMESTAMPTZ,
    pips DECIMAL(6, 1),
    duration_minutes INTEGER,
    
    -- Pattern context (for learning)
    pattern_hash VARCHAR(64), -- Hash of the pattern that generated this signal
    confidence_at_entry DECIMAL(3, 2), -- What was the confidence when signal was generated
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_outcomes_asset ON signal_outcomes(asset, entry_time DESC);
CREATE INDEX idx_outcomes_pattern ON signal_outcomes(pattern_hash) WHERE result IN ('TP', 'SL');
CREATE INDEX idx_outcomes_result ON signal_outcomes(result);

COMMENT ON TABLE signal_outcomes IS 'Proven results. Quantix learns from this, not from raw candles.';
COMMENT ON COLUMN signal_outcomes.pattern_hash IS 'Links to learning_memory. Identifies which pattern generated this signal.';
COMMENT ON COLUMN signal_outcomes.result IS 'TP = Win, SL = Loss, EXPIRED = Timeout, PENDING = Still active';

-- ============================================================================
-- LAYER 3: LEARNING MEMORY (The Brain)
-- ============================================================================
-- This is where Quantix stores its intelligence about patterns

CREATE TABLE IF NOT EXISTS learning_memory (
    pattern_hash VARCHAR(64) PRIMARY KEY,
    asset VARCHAR(10) NOT NULL,
    timeframe VARCHAR(5) NOT NULL,
    
    -- Context (when this pattern works)
    session VARCHAR(20),
    volatility_state VARCHAR(20),
    
    -- Performance stats
    total_signals INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    total_losses INTEGER DEFAULT 0,
    total_expired INTEGER DEFAULT 0,
    win_rate DECIMAL(4, 3), -- e.g., 0.625 = 62.5%
    avg_pips_win DECIMAL(6, 1),
    avg_pips_loss DECIMAL(6, 1),
    
    -- Confidence adjustment (THE LEARNING PART)
    confidence_weight DECIMAL(3, 2) DEFAULT 1.0, -- Multiplier: 0.5 to 1.5
    last_adjustment TIMESTAMPTZ,
    adjustment_reason TEXT,
    
    -- Memory decay
    last_signal_time TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memory_asset ON learning_memory(asset, win_rate DESC);
CREATE INDEX idx_memory_active ON learning_memory(is_active) WHERE is_active = true;
CREATE INDEX idx_memory_session ON learning_memory(session, win_rate DESC);

COMMENT ON TABLE learning_memory IS 'Pattern intelligence. Quantix brain. Updated after each signal outcome.';
COMMENT ON COLUMN learning_memory.confidence_weight IS 'Learning adjustment: <1.0 = reduce confidence, >1.0 = boost confidence';
COMMENT ON COLUMN learning_memory.is_active IS 'False if pattern has not been seen for >30 days (memory decay)';

-- ============================================================================
-- HELPER FUNCTION: Update Learning Memory After Outcome
-- ============================================================================

CREATE OR REPLACE FUNCTION update_learning_memory()
RETURNS TRIGGER AS $$
DECLARE
    v_win_rate DECIMAL(4, 3);
    v_sample_size INTEGER;
    v_new_weight DECIMAL(3, 2);
BEGIN
    -- Only update when outcome is finalized (not PENDING)
    IF NEW.result IN ('TP', 'SL', 'EXPIRED') THEN
        
        -- Upsert learning memory
        INSERT INTO learning_memory (
            pattern_hash, asset, timeframe, session, volatility_state,
            total_signals, total_wins, total_losses, total_expired,
            last_signal_time
        ) VALUES (
            NEW.pattern_hash, NEW.asset, NEW.timeframe, NEW.session, NEW.volatility_state,
            1,
            CASE WHEN NEW.result = 'TP' THEN 1 ELSE 0 END,
            CASE WHEN NEW.result = 'SL' THEN 1 ELSE 0 END,
            CASE WHEN NEW.result = 'EXPIRED' THEN 1 ELSE 0 END,
            NEW.exit_time
        )
        ON CONFLICT (pattern_hash) DO UPDATE SET
            total_signals = learning_memory.total_signals + 1,
            total_wins = learning_memory.total_wins + CASE WHEN NEW.result = 'TP' THEN 1 ELSE 0 END,
            total_losses = learning_memory.total_losses + CASE WHEN NEW.result = 'SL' THEN 1 ELSE 0 END,
            total_expired = learning_memory.total_expired + CASE WHEN NEW.result = 'EXPIRED' THEN 1 ELSE 0 END,
            last_signal_time = NEW.exit_time,
            updated_at = NOW();
        
        -- Calculate new win rate and sample size
        SELECT 
            CASE WHEN total_signals > 0 THEN total_wins::DECIMAL / total_signals ELSE 0 END,
            total_signals
        INTO v_win_rate, v_sample_size
        FROM learning_memory
        WHERE pattern_hash = NEW.pattern_hash;
        
        -- Apply learning rules (Explainable AI)
        v_new_weight := 1.0;
        
        -- Rule 1: Poor performance with sufficient data → reduce confidence
        IF v_win_rate < 0.45 AND v_sample_size >= 30 THEN
            v_new_weight := 0.7;
        END IF;
        
        -- Rule 2: Strong performance in overlap session → boost confidence
        IF v_win_rate > 0.60 AND v_sample_size >= 20 AND NEW.session = 'overlap' THEN
            v_new_weight := 1.2;
        END IF;
        
        -- Rule 3: Extreme volatility → penalize
        IF NEW.volatility_state = 'extreme' THEN
            v_new_weight := v_new_weight * 0.8;
        END IF;
        
        -- Update confidence weight
        UPDATE learning_memory
        SET 
            win_rate = v_win_rate,
            confidence_weight = v_new_weight,
            last_adjustment = NOW(),
            adjustment_reason = format('Win rate: %s%%, Sample: %s', ROUND(v_win_rate * 100, 1), v_sample_size),
            updated_at = NOW()
        WHERE pattern_hash = NEW.pattern_hash;
        
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to signal_outcomes
DROP TRIGGER IF EXISTS trigger_update_learning ON signal_outcomes;
CREATE TRIGGER trigger_update_learning
    AFTER INSERT OR UPDATE OF result ON signal_outcomes
    FOR EACH ROW
    EXECUTE FUNCTION update_learning_memory();

COMMENT ON FUNCTION update_learning_memory() IS 'Auto-learning: Updates pattern intelligence after each signal outcome';

-- ============================================================================
-- HELPER FUNCTION: Memory Decay (Weekly cleanup)
-- ============================================================================

CREATE OR REPLACE FUNCTION decay_old_patterns()
RETURNS INTEGER AS $$
DECLARE
    v_decayed_count INTEGER;
BEGIN
    UPDATE learning_memory
    SET 
        is_active = false,
        updated_at = NOW()
    WHERE 
        is_active = true
        AND last_signal_time < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS v_decayed_count = ROW_COUNT;
    
    RETURN v_decayed_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION decay_old_patterns() IS 'Deactivates patterns not seen in 30+ days. Run weekly.';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
