-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. ASSETS MASTER TABLE
-- Stores configuration for every symbol we want to track (Global & VN)
CREATE TABLE assets_master (
    symbol VARCHAR(20) PRIMARY KEY, -- e.g., 'VN30F1M', 'AAPL', 'BTC-USD'
    name VARCHAR(100),
    asset_type VARCHAR(20) NOT NULL CHECK (asset_type IN ('STOCK', 'FUTURE', 'CRYPTO', 'FOREX')),
    exchange VARCHAR(20), -- 'HOSE', 'NASDAQ', 'BINANCE'
    timezone VARCHAR(50) DEFAULT 'UTC', -- 'Asia/Ho_Chi_Minh', 'America/New_York'
    currency VARCHAR(5) DEFAULT 'USD',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. MARKET DATA RAW TABLE
-- Stores historical and real-time OHLCV data
CREATE TABLE market_data (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(20) REFERENCES assets_master(symbol),
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    open DECIMAL(18, 8),
    high DECIMAL(18, 8),
    low DECIMAL(18, 8),
    close DECIMAL(18, 8),
    volume DECIMAL(18, 8),
    source VARCHAR(50), -- 'yahoo', 'binance', 'polygon'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Prevent duplicate data for the same symbol at the same time
    UNIQUE(symbol, timestamp_utc)
);

-- Index for fast time-range queries
CREATE INDEX idx_market_data_symbol_time ON market_data(symbol, timestamp_utc DESC);

-- 3. AI SIGNALS TABLE
-- Stores the output of our AI models
CREATE TABLE ai_signals (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    symbol VARCHAR(20) REFERENCES assets_master(symbol),
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Forecast data
    predicted_close DECIMAL(18, 8),
    confidence_score DECIMAL(5, 2), -- 0.00 to 100.00
    signal_type VARCHAR(10) CHECK (signal_type IN ('LONG', 'SHORT', 'WATCH', 'HOLD')),
    
    -- Metadata
    model_version VARCHAR(50),
    is_published BOOLEAN DEFAULT FALSE, -- Gatekeeper: Only True signals show on Frontend
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. USERS TABLE (Simplified for MVP)
-- For "The Gatekeeper" functionality
CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_premium BOOLEAN DEFAULT FALSE,
    role VARCHAR(20) DEFAULT 'user', -- 'user', 'admin'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. INITIAL SEED DATA (Optional)
INSERT INTO assets_master (symbol, name, asset_type, exchange, timezone, currency) VALUES
('VN30F1M', 'VN30 Futures 1 Month', 'FUTURE', 'HSX', 'Asia/Ho_Chi_Minh', 'VND'),
('BTC-USD', 'Bitcoin USD', 'CRYPTO', 'BINANCE', 'UTC', 'USD'),
('AAPL', 'Apple Inc.', 'STOCK', 'NASDAQ', 'America/New_York', 'USD'),
('XAU-USD', 'Gold Spot', 'FOREX', 'GLOBAL', 'UTC', 'USD');
