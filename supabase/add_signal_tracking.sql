-- Thêm cột để lưu trạng thái Signal
ALTER TABLE ai_signals 
ADD COLUMN IF NOT EXISTS signal_status VARCHAR(20) DEFAULT 'WAITING',
ADD COLUMN IF NOT EXISTS entry_price DECIMAL(18, 8),
ADD COLUMN IF NOT EXISTS sl_price DECIMAL(18, 8),
ADD COLUMN IF NOT EXISTS tp1_price DECIMAL(18, 8),
ADD COLUMN IF NOT EXISTS tp2_price DECIMAL(18, 8),
ADD COLUMN IF NOT EXISTS current_price DECIMAL(18, 8),
ADD COLUMN IF NOT EXISTS last_checked_at TIMESTAMP WITH TIME ZONE;

-- Index để query nhanh hơn
CREATE INDEX IF NOT EXISTS idx_signal_status ON ai_signals(signal_status);
CREATE INDEX IF NOT EXISTS idx_symbol_status ON ai_signals(symbol, signal_status);

-- Comment để giải thích
COMMENT ON COLUMN ai_signals.signal_status IS 'WAITING | ENTRY_HIT | TP1_HIT | TP2_HIT | SL_HIT';
