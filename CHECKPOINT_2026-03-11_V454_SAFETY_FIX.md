# CHECKPOINT: v4.5.4 Safety Fix — 2026-03-11 18:08 UTC+7

## Summary
Restored critical safety limits after Irfan reported "big losses" despite 2:1 R:R configuration.

## Root Cause Analysis
| Issue | Impact |
|---|---|
| Daily Signal Cap **disabled** (`# REMOVED - Unlimited flow`) | 19 signals fired on Mar 10 (limit should be 8) |
| Old TP/SL config persisted on some signals | TP=7p / SL=12p (inverted 1:1.7 ratio) instead of TP=10p / SL=5p |
| EA `RiskPercent = 2.0%` × 19 trades | Up to 38% account exposure in 1 day |

## Fixes Applied (commit `1505e3c`)
- [x] **Restored `MAX_SIGNALS_PER_DAY = 8`** in `check_release_gate()` — `continuous_analyzer.py`
- [x] **Confirmed `settings.py`**: `TP_PIPS=10.0`, `SL_PIPS=5.0`, `MIN_RR=2.0`
- [x] **Pushed to Railway** — auto-deploy from `main` branch

## Current Configuration (v4.5.4)
```
TP_PIPS           = 10.0        # 10 pips Take Profit
SL_PIPS           = 5.0         # 5 pips Stop Loss (2:1 R:R)
MIN_CONFIDENCE    = 0.75        # 75% threshold
MAX_SIGNALS_PER_DAY = 8         # RESTORED (was disabled)
MIN_RELEASE_INTERVAL = 90 min   # Cooldown between signals
CIRCUIT_BREAKER   = 3 losses → 1h cooldown
MTF_PENALTY       = 0.85x       # Soft penalty for H1 misalignment
```

## System Architecture (Active Agents)
1. **Analyzer Agent** — Scans M15 every 60s, generates signals
2. **Watcher Agent** — Monitors TP/SL/Entry hit on active signals
3. **Watchdog + Janitor** — Health monitoring & stuck-signal cleanup
4. **AutoAdjuster** — Self-learning from past trade outcomes (EMA matrix)
5. **MT4 Bridge (EA)** — Executes on Pepperstone via Signal_Genius.mq4

## Directional Bias Investigation (Resolved)
- **Finding**: 100% BUY on Mar 10-11 is market-driven (H1 trend = BULLISH)
- **Not a bug**: MTF filter correctly penalizes counter-trend SELL signals
- **SELL logic**: Confirmed working (active SELL signals found on Mar 9)

## Recommendation for Irfan
- Consider reducing EA `RiskPercent` from 2.0% to 1.0%
- Max daily risk: 8 signals × 1% = 8% drawdown cap

## Next Steps
- [ ] Monitor Railway deployment health after v4.5.4
- [ ] Verify next signal uses correct TP=10p / SL=5p
- [ ] Track win/loss ratio over 24-48 hours
