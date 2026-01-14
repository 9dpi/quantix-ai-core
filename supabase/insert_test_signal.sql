-- Bước 1: Thêm EUR/USD vào bảng assets_master (nếu chưa có)
INSERT INTO assets_master (symbol, name, asset_type, exchange, timezone, currency)
VALUES ('EURUSD=X', 'EUR/USD Forex Pair', 'FOREX', 'GLOBAL', 'UTC', 'USD')
ON CONFLICT (symbol) DO NOTHING;

-- Bước 2: Tạo tín hiệu EUR/USD mẫu để test Price Watchdog
INSERT INTO ai_signals (
    symbol, 
    timestamp_utc,
    signal_type, 
    predicted_close, 
    confidence_score, 
    is_published,
    signal_status,
    entry_price,
    sl_price,
    tp1_price,
    tp2_price
) VALUES (
    'EURUSD=X',
    NOW(),       -- Timestamp hiện tại
    'LONG',
    1.0520,      -- Entry price
    92,          -- AI Confidence
    TRUE,
    'WAITING',   -- Trạng thái ban đầu
    1.0520,      -- Entry
    1.0490,      -- Stop Loss
    1.0562,      -- Take Profit 1
    1.0604       -- Take Profit 2
);

-- Bước 3: Kiểm tra kết quả
SELECT * FROM ai_signals WHERE symbol = 'EURUSD=X' ORDER BY created_at DESC LIMIT 1;
