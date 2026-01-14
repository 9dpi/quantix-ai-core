-- Quantix AI Core - 3-Tier Candle Ingestion Schema
-- Handles Raw, Validated, and Learning data tiers

-- 1. Raw Tier: Audit trail of all CSV uploads
CREATE TABLE IF NOT EXISTS raw_ohlcv_csv (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset VARCHAR(15) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(18, 10) NOT NULL,
    high DECIMAL(18, 10) NOT NULL,
    low DECIMAL(18, 10) NOT NULL,
    close DECIMAL(18, 10) NOT NULL,
    volume DECIMAL(18, 10),
    candle_type VARCHAR(20), -- NORMAL, NO_ACTIVITY, etc.
    source VARCHAR(50),      -- e.g., 'csv_upload'
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(asset, timeframe, timestamp, source)
);

-- 2. Validated Tier: Filtered high-quality data
CREATE TABLE IF NOT EXISTS validated_ohlcv (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset VARCHAR(15) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(18, 10) NOT NULL,
    high DECIMAL(18, 10) NOT NULL,
    low DECIMAL(18, 10) NOT NULL,
    close DECIMAL(18, 10) NOT NULL,
    volume DECIMAL(18, 10),
    candle_type VARCHAR(20),
    session VARCHAR(20),     -- LONDON, NY, etc.
    day_of_week VARCHAR(15),
    learning_weight DECIMAL(5, 2) DEFAULT 1.0,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(asset, timeframe, timestamp)
);

-- 3. Learning Tier: High-confidence data for Quantix AI
CREATE TABLE IF NOT EXISTS learning_ohlcv (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset VARCHAR(15) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(18, 10) NOT NULL,
    high DECIMAL(18, 10) NOT NULL,
    low DECIMAL(18, 10) NOT NULL,
    close DECIMAL(18, 10) NOT NULL,
    volume DECIMAL(18, 10),
    session VARCHAR(20),
    day_of_week VARCHAR(15),
    learning_weight DECIMAL(5, 2),
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    rebuilt_at TIMESTAMPTZ,
    UNIQUE(asset, timeframe, timestamp)
);

-- 4. Ingestion Audit Log
CREATE TABLE IF NOT EXISTS ingestion_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset VARCHAR(15),
    timeframe VARCHAR(10),
    source VARCHAR(50),
    total_rows INTEGER,
    tradable_count INTEGER,
    non_tradable_count INTEGER,
    avg_learning_weight DECIMAL(5, 2),
    status VARCHAR(20),
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE raw_ohlcv_csv ENABLE ROW LEVEL SECURITY;
ALTER TABLE validated_ohlcv ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_ohlcv ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingestion_audit_log ENABLE ROW LEVEL SECURITY;

-- Public read policies (Internal Alpha)
CREATE POLICY "Public read raw" ON raw_ohlcv_csv FOR SELECT USING (true);
CREATE POLICY "Public read validated" ON validated_ohlcv FOR SELECT USING (true);
CREATE POLICY "Public read learning" ON learning_ohlcv FOR SELECT USING (true);
CREATE POLICY "Public read audit" ON ingestion_audit_log FOR SELECT USING (true);
