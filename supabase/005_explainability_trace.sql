-- Quantix AI Core - Explainability Trace Schema
-- Phase 3.1: Core Intelligence Layer - Self-Explaining AI

-- 1. Signal Explanations: High-level summary of AI reasoning per signal
CREATE TABLE IF NOT EXISTS signal_explanations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES trade_signals(id) ON DELETE CASCADE,
    
    asset VARCHAR(15),
    timeframe VARCHAR(10),
    
    final_confidence NUMERIC(5, 4),        -- e.g. 0.9600
    confidence_version VARCHAR(20),        -- e.g. 'v1.0-explain'
    
    summary TEXT,                          -- Human-readable summary for Dashboard UI
    explain_factors JSONB,                 -- Machine-readable detailed structure
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_explain_signal 
ON signal_explanations(signal_id);

-- 2. Explain Components: Granular scoring factors (Drill-down audit)
CREATE TABLE IF NOT EXISTS explain_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES trade_signals(id) ON DELETE CASCADE,
    
    component_type VARCHAR(20),      -- SESSION / PATTERN / VOLATILITY / OUTCOME / RISK
    component_key VARCHAR(50),       -- LONDON_NY, HH_HL, EXPANDING, etc
    
    description TEXT,                -- Human-readable description
    impact_score NUMERIC(5, 4),      -- Contribution to confidence (e.g. +0.12, -0.05)
    confidence_contribution NUMERIC(5, 4), -- Absolute contribution value
    
    evidence JSONB,                  -- Statistical backing (winrate, sample_size, etc.)
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_explain_component 
ON explain_components(signal_id, component_type);

-- RLS Enforcement
ALTER TABLE signal_explanations ENABLE ROW LEVEL SECURITY;
ALTER TABLE explain_components ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read explanations" ON signal_explanations FOR SELECT USING (true);
CREATE POLICY "Public read explain components" ON explain_components FOR SELECT USING (true);
