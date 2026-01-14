-- Quantix AI Core - Initial Schema for Signals and Lifecycle

-- 1. Signals Table
CREATE TABLE IF NOT EXISTS fx_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset VARCHAR(15) NOT NULL,
    direction VARCHAR(10) NOT NULL, -- BUY, SELL
    timeframe VARCHAR(10) NOT NULL,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    ai_confidence DECIMAL(5, 4),
    confidence_grade VARCHAR(5),    -- A+, A, B, etc.
    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, EXPIRED, INVALIDATED, TP_HIT, SL_HIT
    disclaimer TEXT DEFAULT 'Internal research signal. Not financial advice.'
);

-- 2. Signal Validation
CREATE TABLE IF NOT EXISTS fx_signal_validation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES fx_signals(id),
    rule_name VARCHAR(50),
    is_passed BOOLEAN,
    details JSONB
);

-- 3. Signal Lifecycle tracking
CREATE TABLE IF NOT EXISTS fx_signal_lifecycle (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES fx_signals(id),
    event_type VARCHAR(30),
    event_time TIMESTAMPTZ DEFAULT NOW(),
    previous_status VARCHAR(20),
    new_status VARCHAR(20)
);

-- Enable RLS
ALTER TABLE fx_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE fx_signal_validation ENABLE ROW LEVEL SECURITY;
ALTER TABLE fx_signal_lifecycle ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Public read signals" ON fx_signals FOR SELECT USING (true);
CREATE POLICY "Public read validation" ON fx_signal_validation FOR SELECT USING (true);
CREATE POLICY "Public read lifecycle" ON fx_signal_lifecycle FOR SELECT USING (true);
