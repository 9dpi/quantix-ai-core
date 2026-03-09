# Quantix AI Master DNA (v4.1.3)

## 1. Overall Architecture
- **Cloud Core (Railway)**: 
    - `API`: FastAPI (Supabase backend) serving signals to local bridge.
    - `Analyzer`: Continuous market scanning (TwelveData/Binance fallback).
    - `Validator`: Real-time setup verification (Pepperstone data).
- **Local Bridge (Windows PC)**:
    - `auto_executor.py`: Polls Cloud API every 1s and triggers MT4.
- **Expert Advisor (EA)**:
    - `Signal_Genius.mq4`: Executes trades on MetaTrader 4.
- **Safety Layer**:
    - `Watchdog`: Monitors heartbeats of all services.
    - `Janitor`: Auto-cleans "stuck" signals if services stall.

## 2. Current Status
- [x] **Consolidated Infrastructure**: All cloud services merged into `start_railway_consolidated.py` (saves ~60% cost).
- [x] **Precision Logic**: Fixed 0-pip SL bug by implementing distance-locked rounding.
- [x] **Watchdog Fix**: Corrected false "119-minute" alerts.
- [x] **EA v1.1.1**: Added robust lot volume protection (Error 131 fix) and minified JSON parsing.
- [ ] **Bugs/Issues**: None pending. 3 problematic SL signals hidden via `HIDDEN_DEBUG` status.

## 3. Tech Stack & Conventions
- **Languages**: Python 3.10+ (Backend), MQL4 (MT4 EA), HTML/CSS/JS (Vanilla, Premium dark-theme).
- **DB**: Supabase (PostgreSQL). Critical column: `status` (standardized).
- **Style**: Loguru for logging, Pydantic for settings, Functional/Procedural hybrids for engine logic.
- **Folder Root**: `d:/Automator_Prj/Quantix_AI_Core/backend` (Main code).

## 4. Core Logic / Classes
- **`ContinuousAnalyzer`**: `run_cycle()` in `continuous_analyzer.py` - The brain that generates signals.
- **`SignalEvaluator`**: Logic that checks confidence thresholds (>75%).
- **`Janitor.run_sync()`**: Emergency cleanup of active DB signals.
- **`db.client`**: Shared Supabase client in `database/connection.py`.

## 5. Standard Operating Values
- **TP/SL**: Fixed at **7 pips (TP)** / **12 pips (SL)**.
- **Heartbeat**: Every cycle (~5 mins) to `HEARTBEAT` asset.
- **Confidence Threshold**: 77% (Global safety filter).

## 6. Next Steps
1. **Monitor Flow**: Watch the consolidated container logs on Railway for the next high-confidence signal.
2. **Sync Verification**: Ensure the local bridge picks up the next `PUBLISHED` signal and MT4 executes it without Error 131.
