-- 🧹 CLEAN ALL TEST/MOCK DATA FROM DATABASE
-- Run this to ensure ONLY real production data exists

-- Step 1: Delete all test signals with old fake prices
DELETE FROM ai_signals 
WHERE symbol = 'EURUSD=X' 
AND (
    predicted_close < 1.10  -- Old 2024 prices (market is now ~1.16)
    OR signal_status = 'WAITING' -- Remove stale waiting signals
    OR created_at < NOW() - INTERVAL '7 days' -- Remove old signals
);

-- Step 2: Verify clean state
SELECT 
    COUNT(*) as total_signals,
    MAX(created_at) as latest_signal,
    MAX(current_price) as latest_price
FROM ai_signals 
WHERE symbol = 'EURUSD=X';

-- Expected: 0 signals (clean slate for production)
