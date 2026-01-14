-- Quantix AI Ingestion Tables
CREATE TABLE IF NOT EXISTS raw_ohlcv_csv (id UUID PRIMARY KEY, asset VARCHAR(10), timestamp TIMESTAMPTZ);
CREATE TABLE IF NOT EXISTS validated_ohlcv (id UUID PRIMARY KEY, asset VARCHAR(10), timestamp TIMESTAMPTZ);
CREATE TABLE IF NOT EXISTS learning_ohlcv (id UUID PRIMARY KEY, asset VARCHAR(10), timestamp TIMESTAMPTZ);
CREATE TABLE IF NOT EXISTS ingestion_audit_log (id UUID PRIMARY KEY, asset VARCHAR(10), status VARCHAR(20));

