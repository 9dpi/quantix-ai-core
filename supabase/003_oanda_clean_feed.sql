-- OANDA Clean Feed Schema v1 (FROZEN)
-- Single source of truth for market data
-- Append-only, replay-safe, auditable

CREATE TABLE IF NOT EXISTS market_candles_v1 (
    id BIGSERIAL PRIMARY KEY,

    -- Provider identification
    provider TEXT NOT NULL,               -- "oanda"
    instrument TEXT NOT NULL,             -- "EUR_USD"
    timeframe TEXT NOT NULL,              -- "H1", "H4"

    -- Candle data (UTC)
    timestamp TIMESTAMPTZ NOT NULL,       -- candle OPEN time (UTC)

    -- OHLC (5 decimal precision for FX)
    open NUMERIC(10,5) NOT NULL,
    high NUMERIC(10,5) NOT NULL,
    low  NUMERIC(10,5) NOT NULL,
    close NUMERIC(10,5) NOT NULL,

    -- Volume
    volume BIGINT,
    
    -- Completeness flag (CRITICAL)
    complete BOOLEAN NOT NULL,

    -- Audit trail
    source_id TEXT NOT NULL,              -- unique id from provider
    ingested_at TIMESTAMPTZ DEFAULT now(),

    -- Constraints
    UNIQUE (provider, instrument, timeframe, timestamp),
    
    -- Integrity check
    CHECK (low <= open AND open <= high),
    CHECK (low <= close AND close <= high),
    CHECK (low <= high)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_candles_lookup 
    ON market_candles_v1 (provider, instrument, timeframe, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_candles_complete 
    ON market_candles_v1 (provider, instrument, timeframe, complete, timestamp DESC);

-- Comments for documentation
COMMENT ON TABLE market_candles_v1 IS 'Clean market data feed v1 - append-only, replay-safe';
COMMENT ON COLUMN market_candles_v1.complete IS 'Only complete=true candles are usable by Feature Engine';
COMMENT ON COLUMN market_candles_v1.timestamp IS 'Candle OPEN time in UTC - immutable';
COMMENT ON COLUMN market_candles_v1.source_id IS 'Provider unique ID for deduplication and audit';
