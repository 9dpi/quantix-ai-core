# 🏁 CHECKPOINT: QUANTIX AI CORE – SYSTEM STATE (2026-03-11)
**Date:** 2026-03-11 08:10 (GMT+7)  
**Version:** v4.5.2 (Aggressive 2:1 R:R)  
**Status:** ✅ PRODUCTION  
**Branch:** `main` @ `653b729`  

---

## 🏗️ Architecture Overview

```
┌─────────────── Railway (Single Container) ───────────────┐
│  start_railway_consolidated.py (v4.1.3)                  │
│  ├── WEB:       FastAPI + Uvicorn (:$PORT)               │
│  ├── ANALYZER:  ContinuousAnalyzer (60s scan cycle)      │
│  └── VALIDATOR: Pepperstone price validator               │
├──────────────────────────────────────────────────────────-│
│  Auto-restart loop + DB audit logging per service        │
└──────────────────────────────────────────────────────────-┘
         │ API                           │ Supabase
         ▼                               ▼
┌─────────────────┐           ┌─────────────────────┐
│ Local Bridge    │           │ Supabase (PostgreSQL)│
│ auto_executor.py│◄──poll───│ fx_signals           │
│ (Windows PC)    │           │ fx_analysis_log      │
└────────┬────────┘           │ fx_signal_lifecycle  │
         │                    └─────────────────────┘
         ▼
┌──────────────────┐
│ Signal_Genius.mq4│
│ MetaTrader 4 EA  │
└──────────────────┘
```

---

## 📊 Trading Parameters (v4.5.2)

| Parameter | Value | Notes |
|---|---|---|
| **TP** | 10.0 pips | Aggressive scalping |
| **SL** | 5.0 pips | 2:1 Risk-Reward Ratio |
| **Min R:R** | 2.0 | Hard enforcement |
| **MIN_CONFIDENCE** | 0.85 (85%) | Release threshold |
| **MAX_LOT_SIZE_CAP** | 0.20 | Safety for 1:30 leverage (£1000) |
| **RISK_USD_PER_TRADE** | $50.0 | Institutional Risk Model |
| **MAX_SIGNALS_PER_DAY** | 8 | Anti-burst cap |
| **MIN_RELEASE_INTERVAL** | 90 min | Between consecutive signals |
| **MAX_CONSECUTIVE_LOSSES** | 3 | → Circuit Breaker triggers |
| **CIRCUIT_BREAKER_COOLDOWN** | 1.0 hour | v4.5.1: Reduced from 4h |
| **MONITOR_INTERVAL** | 60s | v4.3.0: High-speed scanning |
| **WATCHER_CHECK_INTERVAL** | 30s | v4.3.0: High-speed monitoring |
| **MAX_PENDING_DURATION** | 35 min | Entry window |
| **MAX_TRADE_DURATION** | 150 min | v3.8: Institutional audit |
| **HEALTH_REPORT_INTERVAL** | 120 min | Auto Telegram health reports |

---

## 🔄 Version History Since Last Checkpoint (2026-02-26)

| Commit | Version | Change |
|---|---|---|
| `653b729` | **v4.5.2** | Aggressive 2:1 R:R (TP=10p, SL=5p) + Telegram template update |
| `0c10839` | v4.5.1 | Fix directional bias + reduce CB cooldown to 1h |
| `56198d3` | v4.5.0 | "Safe-Guard" Rescue Pivot (MIN_RELEASE=90m, MAX_PER_DAY=8) |
| `5d4f1ae` | v4.4.1 | Deep refinement of core structure logic |
| `9f3cb44` | v4.4.0 | "Safety First" win rate optimizations |
| `f01af47` | v4.3.0 | High-speed execution (60s scan, 30s watcher) |
| `4d20778` | v4.2.1 | Interim TP/SL adjustment (7p/12p) |
| `998e4b7` | v4.2.0 | 2-hour automated system health reports |
| `3569626` | v4.1.9 | Schema sanitization fix (unblock signal flow) |
| `e913842` | v4.1.8 | Disable breakeven logic (prevent phantom stop-outs) |

---

## 🧠 Key System Components

### 1. ContinuousAnalyzer (`continuous_analyzer.py` — 1148 lines)
- **Market Execution**: All signals >85% confidence released
- **Embedded Watcher**: Signal monitoring runs INSIDE the Analyzer process (eliminates standalone crash risk)
- **Multi-candle detection**: 5-candle confirmation for better accuracy
- **Circuit Breaker**: 3 consecutive losses → 1h cooldown
- **H1 Trend Alignment**: Multi-timeframe bias check
- **Integrated Janitor**: Self-cleans stuck signals per cycle
- **Health Report**: Auto-broadcasts comprehensive report every 2 hours

### 2. SignalWatcher (`signal_watcher.py` — 653 lines)
- **State Machine**: WAITING_FOR_ENTRY → ENTRY_HIT → TP_HIT / SL_HIT / TIME_EXIT / CANCELLED
- **Hit Detection Tolerance**: 0.2 pip buffer for spread/slippage compensation
- **Breakeven Logic**: Currently **DISABLED** (v4.1.8) to prevent phantom stop-outs
- **Multi-Source Fallover**: Binance primary → TwelveData fallback
- **Friday Cleanup**: Auto-cancels pending signals at market close

### 3. AutoAdjuster (`auto_adjuster.py` — Phase 5.1)
- **Self-learning** spread buffer adjuster
- 24-hour EMA-smoothed miss rate matrix
- ATR-based volatility multiplier (capped at 4×)
- Persists learned config to DB for cross-process access

### 4. MT4 Bridge (`mt4.py`)
- **strategy_id**: `Quantix_v4_SMC` (fixed)
- **Slippage**: 5.0 pips | **Max Spread**: 3.0 pips
- **Magic Number**: 900900
- Dual logging: Supabase + local JSON fallback

### 5. Consolidated Launcher (`start_railway_consolidated.py` v4.1.3)
- Single process running 3 services via threads
- Auto-restart loop with staggered start (2s)
- DB audit logging for every service event
- Cost-optimized: ~$2-3/month on Railway

---

## ✅ System Verification Checklist

- [x] **Binance Feed**: PRIMARY data source (live)
- [x] **TwelveData**: FALLBACK only (quota-safe)
- [x] **Supabase**: All signals + audit logs persisted
- [x] **Telegram**: Signal notifications + admin health reports
- [x] **MT4 Bridge**: Local executor → EA pipeline active
- [x] **Watchdog**: Service heartbeat monitoring
- [x] **Janitor**: Auto-cleanup of stale signals
- [x] **Circuit Breaker**: Loss-based protection active
- [x] **Frontend Fallback**: Railway API ↔ Supabase REST hybrid

---

## ⚙️ Feature Flags

| Flag | Status |
|---|---|
| `ENABLE_LIVE_SIGNAL` | ✅ ON |
| `ENABLE_BACKTEST` | ✅ ON |
| `ENABLE_LEARNING` | ✅ ON |
| `ENABLE_LAB_SIGNALS` | ✅ ON |
| `WATCHER_OBSERVE_MODE` | ❌ OFF (Live execution) |
| `QUANTIX_MODE` | INTERNAL |

---

## 🚀 Next Steps
1. **Monitor v4.5.2 R:R performance**: Track TP/SL hit rates with aggressive 2:1 ratio
2. **Execution Audit**: Verify MT4 callbacks for signal accuracy
3. **Volatility Guard**: Watch for extreme ATR rejections during news events
4. **Consider**: Re-evaluating breakeven logic with refined parameters

---
*Checkpoint created at 2026-03-11 08:10 (GMT+7) — consolidating all changes from v4.1.3 through v4.5.2*
