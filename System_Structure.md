# Quantix AI Core - System Structure Overview

## 🏗️ Architecture Philosophy: Distributed Intelligence & Transparency
Quantix AI Core is an **Institutional-Grade Market Intelligence Engine** designed with the **5W1H Transparency Framework** (Who, What, Where, When, Why, How). It uses a distributed micro-services architecture for maximum uptime and verifiable decision-making.

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
    *   **Integrated Watchdog (v3.8)**: Analyzer monitors the health of the Watcher service every 120 minutes. If Watcher is stale (>30m), it triggers Janitor healing and broadcasts a critical Telegram alert.
    *   **Anti-Burst Rule**: Maintains a strict 20-minute cooldown and global active signal lock.
    *   **Strategy v3.8 (Market Regime Hunter)**: 
        *   **Dynamic Entry**: All signals (>=80% confidence) now utilize **Market Execution** (Market Order) to ensure zero entry miss-rate. Pending FVG orders are only used as fallback in low-liquidity states.
        *   **5W1H Metadata**: Every signal caches detailed "Intelligence Reasoning" including session context, ATR volatility, and exact technical "Why" labels.
        *   **Watcher Health (v3.8.1)**: Analyzer performs a cross-process check on the Watcher every **120 minutes**. If the Watcher pulse is missing, Analyzer triggers an immediate restart command.
        *   **Dead-Zone Filter**: Blocks Sunday open, Asia low-liquidity, and Rollover hours (21:00-23:00 UTC).
*   **Confidence Gate**: Institutional threshold set to **80%** minimum for release.

### 3. Signal Watcher (`start_railway_watcher.py`)
*   **Role**: Real-time monitor for active signal results.
*   **Frequency**: High-speed (60s checks).
*   **Cycle**:
    *   `WAITING_FOR_ENTRY`: Tracks price to detect the exact entry touch (FVG Re-entry).
    *   **SL Invalidation**: Automatically cancels pending signals if price touches SL level before Entry.
    *   `ENTRY_HIT`: Monitors Take Profit (TP), Stop Loss (SL), or **150m (2.5h)** Duration Timeout. 
    *   **Retroactive Audit (v3.8)**: An automated cleaning layer verifies historical 'Expired' signals against Binance price data to recover missing Win/Loss events.
    *   **Breakeven Lock**: Automatically moves SL to entry (Risk-Free) once price completes 70% of distance to TP.
    *   **Resilience Protocol (v3.8.1)**: Watcher is now monitored by the Analyzer; failure to update the heartbeat for >30m triggers an automated system reboot.
    *   Atomic Transitions: Uses DB-level checks to prevent duplicate Telegram notifications.

### 4. Institutional Validator (`start_railway_validator.py`)
*   **Role**: Independent "Audit" layer.
*   **Feed**: Uses a separate Pepperstone/Binance feed to cross-verify prices.
*   **Verification**: Logs discrepancies into `validation_events` to detect "Gaps" or "Slippage".

### 5. Watchdog & Active Healing (`start_railway_watchdog.py`)
*   **Role**: System self-preservation.
*   **Frequency**: Heartbeat Check every 5 minutes.
*   **Armored Launcher (v3.8)**: Now includes an auto-restart loop (max 50 retries) and DB-logged restart events, ensuring the watchdog itself stays online even if the process crashes.
*   **Active Healing**: If any worker stalls for >15 mins, Watchdog automatically runs `Janitor.run_sync()` to release stuck signals and broadcasts a critical alert to Admin.

---

## 🧠 The Engine Components (`backend/quantix_core/engine/`)

### `StructureEngineV1` (SMC Tier)
Translates OHLCV data into market states using:
1.  **Market Structure (BOS)**: Detects shifting dominance.
2.  **Liquidity Sweep**: Detects session high/low manipulation (Asian Range Sweep).
3.  **FVG Identification**: Locates Fair Value Gaps for high-precision entries.

### `ConfidenceRefiner` (v3.7 Session-Aware Strategy)
Applies a weighted scoring model (Target: 90% Win Rate):
1.  **Structure (30%)**: Patterns & FVG quality.
2.  **Session (25%)**: Timing (London/NY Open alignment).
3.  **Volatility (20%)**: ATR-based dynamic risk validation.
4.  **Trend Alignment (25%)**: Cross-verification of M15 with H1 direction.
5.  **Session-Aware R:R (v3.7)**: Optimized for Win Rate with session-based TP/SL distance (PEAK=1.0x ATR, HIGH=0.8x, LOW=0.5x).
6.  **5W1H Reasoning (v3.8)**: Full transparency on decision-making:
        *   **WHY**: Technical labels (Structure, FVG, Confidence, ATR, Session weighting).
        *   **HOW**: Data source validation and execution method.
7.  **Duration (v3.8)**: Tightened to **150 minutes** for capital efficiency.

### `Janitor` & `EntryCalculator`
*   **Janitor**: Specialized fail-safe for cleaning stuck signals (>35m WAITING, >180m ACTIVE).
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
**Version**: 3.8.1 (Transparency & Intelligence Enabled)  
**Status**: Production Hardened / Intelligence Modal Active  
**Active Healing**: Enabled (Analyzer-to-Watcher Monitoring)
