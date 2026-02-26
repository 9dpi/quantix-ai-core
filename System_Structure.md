# Quantix AI Core - System Structure Overview

## 🏗️ Architecture Philosophy: Distributed Intelligence
Quantix AI Core is designed as a **Institutional-Grade Market Intelligence Engine** using a distributed micro-services architecture. Instead of a monolithic app, the system is split into specialized "Workers" that communicate via a shared **Supabase** database layer.

---

## 🛰️ Core Services (Railway Procfile Workers)

### 1. Web / API (`start_railway_web.py`)
*   **Role**: Exposes the REST interface for external clients and the Dashboard.
*   **Framework**: FastAPI.
*   **Endpoints**:
    *   `/signals`: Retrieval of active and historical signals.
    *   `/lab`: Advanced telemetry for AI self-learning.
    *   `/admin`: System-wide control and unblocking.
    *   `/public`: Restricted API for 3rd party integrations.

### 2. Signal Analyzer (`start_railway_analyzer.py`)
*   **Role**: The "Brain" of the system.
*   **Frequency**: Every 5 minutes (Optimized for M15 timeframe).
*   **Logic**:
    *   Fetches market data (TwelveData primary, Binance fallback).
    *   Runs `StructureEngineV1` to identify bullish/bearish setups.
    *   Calculates `ConfidenceRefiner` scores.
    *   Triggers "Janitor" cleanup at the start of every cycle.
    *   **Anti-Burst Rule**: Maintains a strict 30-minute cooldown and global active signal lock.

### 3. Signal Watcher (`start_railway_watcher.py`)
*   **Role**: Real-time monitor for active signal results.
*   **Frequency**: High-speed (60s checks).
*   **Cycle**:
    *   `WAITING_FOR_ENTRY`: Tracks price to detect the exact entry touch.
    *   `ENTRY_HIT`: Monitors for Take Profit (TP), Stop Loss (SL), or 90m Time Timeout.
    *   Atomic Transitions: Uses DB-level checks to prevent duplicate Telegram notifications.

### 4. Institutional Validator (`start_railway_validator.py`)
*   **Role**: Independent "Audit" layer.
*   **Feed**: Uses a separate Pepperstone/Binance feed to cross-verify prices.
*   **Verification**: Logs discrepancies into `validation_events` to detect "Gaps" or "Slippage".

### 5. Watchdog & Active Healing (`start_railway_watchdog.py`)
*   **Role**: System self-preservation.
*   **Heartbeat Check**: Monitors every 5 minutes.
*   **Active Healing**: If any worker stalls for >15 mins, Watchdog automatically runs `Janitor.run_sync()` to release stuck signals and broadcasts a critical alert to Admin.

---

## 🧠 The Engine Components (`backend/quantix_core/engine/`)

### `StructureEngineV1`
High-speed technical analysis engine that translates raw OHLCV data into market states (Bullish, Bearish, Sideways) using pattern identification primitives.

### `ConfidenceRefiner`
Applies a weighted scoring model based on:
1.  **Structure**: Raw pattern strength.
2.  **Session**: Timing (London/NY Open alignment).
3.  **Volatility**: ATR-based risk validation.
4.  **Historical**: Weighted average of previous similar patterns.

### `Janitor`
A specialized fail-safe module designed to:
*   Cancel signals kẹt (stuck) in `WAITING` state > 35m.
*   Close signals kẹt in `ENTRY_HIT` state > 90m (Market Timeout).

---

## 📊 Database Schema (Supabase)
*   `fx_signals`: Immutable record of all generated calls.
*   `fx_analysis_log`: System-wide heartbeat and detailed analysis telemetry.
*   `fx_signal_validation`: Verification data for validator service.
*   `validation_events`: Log of price discrepancies and audit trails.

---

## 📡 Integrations
*   **Data Feeds**: TwelveData (Primary Institutional), Binance (Fallback & High-Speed).
*   **Notifications**: Telegram Bot (v2) with threaded command listening (`/status`, `/unblock`).
*   **Persistence**: Supabase REST API (PostgreSQL).

---

## 📁 Repository Map
```text
Quantix_AI_Core/
├── backend/
│   ├── quantix_core/
│   │   ├── api/          # FastAPI Routes & Main App
│   │   ├── config/       # Environment & Settings
│   │   ├── database/     # Supabase Connection Wrapper
│   │   ├── engine/       # Core Logic (Analyzer, Watcher, Watchdog, Janitor)
│   │   ├── feeds/        # Data Feed Adapters
│   │   ├── notifications/# Telegram Logic
│   │   └── utils/        # Market Hours, Calculators
├── dashboard/            # HTML/JS Visualization
├── Procfile              # Railway Worker Definitions
└── start_railway_*.py    # Micro-service launchers
```

---
**Version**: 3.2 (Stable)  
**Status**: Production Ready  
**Active Healing**: Enabled
