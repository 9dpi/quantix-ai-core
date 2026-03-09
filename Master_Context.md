# Quantix AI Master DNA (v4.1.4)

## 1. Overall Architecture
- **Cloud Core (Railway)**: 
    - `API`: FastAPI (Supabase backend) serving signals to local bridge.
    - `Analyzer`: Continuous market scanning (Binance primary / TwelveData fallback).
    - `Validator`: Real-time setup verification (Pepperstone data).
- **Local Bridge (Windows PC)**:
    - `auto_executor.py`: Polls Cloud API every 1s and triggers MT4.
- **Expert Advisor (EA)**:
    - `Signal_Genius.mq4`: Executes trades on MetaTrader 4.
- **Safety Layer**:
    - `Watchdog`: Monitors heartbeats of all services.
    - `Janitor`: Integrated into Analyzer loop for proactive signal cleanup.

## 2. Current Status
- [x] **Infrastructure**: Consolidated `start_railway_consolidated.py` successfully (Source priority: Binance).
- [x] **Signal Lifecycle**: Fixed DB constraint `chk_state_valid` by standardizing states (ENTRY_HIT for live signals).
- [x] **MT4 Optimization**: Relaxed execution parameters (Spread: 3.0p, Slippage: 5.0p) and dynamic `strategy_id` matching.
- [x] **Unlimited Flow**: Removed "1 signal per day" restriction (MAX_SIGNALS_PER_DAY: 9999).
- [x] **Resource Cleanup**: Janitor integrated into cycle for automatic stall prevention.

## 3. Tech Stack & Conventions
- **Languages**: Python 3.10+ (Backend), MQL4 (MT4 EA), Vanilla JS Dashboard.
- **DB**: Supabase (PostgreSQL). States: `ENTRY_HIT`, `TP_HIT`, `SL_HIT`, `CANCELLED`.
- **Style**: Loguru + Pydantic. Root: `d:/Automator_Prj/Quantix_AI_Core/backend`.

## 4. Core Logic / Classes
- **`ContinuousAnalyzer`**: Market execution for all signals >75% confidence.
- **`MT4 Bridge`**: `mt4.py` route handles polling (max_spread: 3.0, slippage: 5.0).
- **`Janitor`**: Self-cleans pipeline every 150m (ACTIVE) or 35m (WAITING).

## 5. Standard Operating Values
- **TP/SL**: Fixed **7.0 pips (TP)** / **12.0 pips (SL)** for institutional consistency.
- **Confidence Threshold**: 75% (Min Release).
- **Max Lots**: 0.20 (Safety Cap).

## 6. Next Steps
1. **Execution Audit**: Monitor MT4 callbacks for the next high-momentum move.
2. **Volatility Guard**: Watch for "Volatility Spike" rejections (>2.5x ATR) during news events.
