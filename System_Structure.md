# Quantix AI Core - System Structure Overview

## 🏗️ Architecture Philosophy: Distributed Intelligence
Quantix AI Core is designed as a **Institutional-Grade Market Intelligence Engine** using a distributed micro-services architecture. Instead of a monolithic app, the system is split into specialized "Workers" that communicate via a shared **Supabase** database layer.

---

## 🛰️ Core Services (Railway Procfile Workers)

### 1. Web / API (`start_railway_web.py`)
*   **Role**: Exposes the REST interface for external clients and the Dashboard.
*   **Security**: Restricted CORS (Production domains only), Bearer Token Auth for public routes.
*   **Framework**: FastAPI.
*   **Endpoints**:
    *   `/signals`: Retrieval of active and historical signals.
    *   `/lab`: Advanced telemetry for AI self-learning.
    *   `/admin`: System-wide control and unblocking.
    *   `/public`: Restricted API for 3rd party integrations.

### 2. Signal Analyzer (`start_railway_analyzer.py`)
*   **Role**: The "Brain" of the system.
*   **Frequency**: Every 5 minutes (Optimized for M15 timeframe).
*   **Logic (SMC-Lite M15 Architecture)**:
    *   **BOS Detection**: Identifies Bullish/Bearish Break of Structure with body-close confirmation.
    *   **FVG-Based Entry**: Calculates entry at Fair Value Gaps for optimized Reward/Risk.
    *   **Anti-Burst Rule**: Maintains a strict 30-minute cooldown and global active signal lock.
*   **Confidence Gate**: Institutional threshold set to **80%** minimum for signal release.

### 3. Signal Watcher (`start_railway_watcher.py`)
*   **Role**: Real-time monitor for active signal results.
*   **Frequency**: High-speed (60s checks).
*   **Cycle**:
    *   `WAITING_FOR_ENTRY`: Tracks price to detect the exact entry touch (FVG Re-entry).
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

### `StructureEngineV1` (SMC Tier)
Translates OHLCV data into market states using:
1.  **Market Structure (BOS)**: Detects shifting dominance.
2.  **Liquidity Sweep**: Detects session high/low manipulation (Asian Range Sweep).
3.  **FVG Identification**: Locates Fair Value Gaps for high-precision entries.

### `ConfidenceRefiner`
Applies a weighted scoring model (Target: >80% Win Rate):
1.  **Structure (30%)**: Patterns & FVG quality.
2.  **Session (25%)**: Timing (London/NY Open alignment).
3.  **Volatility (20%)**: ATR-based dynamic risk validation.
4.  **Trend Alignment (25%)**: Cross-verification of M15 with H1 direction.

### `Janitor` & `EntryCalculator`
*   **Janitor**: Specialized fail-safe for cleaning stuck signals (>35m WAITING, >90m ACTIVE).
*   **EntryCalculator**: Dynamic calculation of entry points based on **Fair Value Gaps (FVG)** instead of fixed offsets.

---

## 📊 Database & Security (Hardened)

### Security Standard
*   **Row Level Security (RLS)**: Enabled on all Supabase tables.
*   **Credential Management**: Zero hardcoded keys. All secrets stored in Railway Environment Variables.
*   **Network**: Restricted CORS to production origins. 

### Tables
*   `fx_signals`: Immutable record of all calls.
*   `fx_analysis_log`: System-wide heartbeat and detailed telemetry.
*   `fx_signal_validation`: Verification data for validator service.

---

## 📁 Repository Map
```text
Quantix_AI_Core/
├── backend/
│   ├── quantix_core/
│   │   ├── api/          # FastAPI & CORS Security
│   │   ├── config/       # Env & Logic Thresholds (80%)
│   │   ├── database/     # Supabase Connection Wrapper
│   │   ├── engine/       # SMC Logic (BOS, FVG, Liquidity)
│   │   ├── feeds/        # Multi-source data failover
│   │   └── utils/        # Market Hours, FVG Calculators
├── dashboard/            # HTML/JS (Anon-Key Restricted)
├── Procfile              # Railway Worker Definitions
└── start_railway_*.py    # Micro-service launchers
```

---
**Version**: 3.5 (Institutional SMC-Lite)  
**Status**: Production Hardened  
**Active Healing**: Enabled
