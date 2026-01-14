-- Quantix AI Core Initial Schema
CREATE TABLE IF NOT EXISTS fx_signals (id UUID PRIMARY KEY, asset VARCHAR(10), direction VARCHAR(4), status VARCHAR(15));

