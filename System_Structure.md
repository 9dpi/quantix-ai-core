# Quantix AI Core - System Structure Overview

## 🏗️ Architecture Philosophy: Distributed Intelligence & Observability
Quantix AI Core is an **Institutional-Grade Market Intelligence Engine** designed with the **5W1H Transparency Framework** (Who, What, Where, When, Why, How). It uses a distributed micro-services architecture for maximum uptime and **Unified Observability (Sniffer v3.8.2)**.

---

## 🛰️ Core Services (Railway Procfile Workers)

### 1. Web / API (`start_railway_web.py`)
*   **Role**: Exposes the REST interface for external clients and the Dashboard.
*   **Domain**: `https://quantixapiserver-production.up.railway.app`
*   **Security**: Restricted CORS (Production domains only), Bearer Token Auth for public routes.
*   **Framework**: FastAPI on Port 8000/8080.
*   **Observability**: Integrated **HTTP Sniffer** logs all incoming requests and local health status (Self-Ping) to Supabase as `UVICORN_LOG`.

### 2. Signal Analyzer (`start_railway_analyzer.py`)
*   **Role**: The "Brain" of the system.
*   **Logic**: SMC-Lite M15 (BOS, FVG detection, Asian Range Sweep).
*   **Observability**: **Launcher Sniffer** captures all process output to DB (`ANALYZER_LOG`).
*   **Integrated Watchdog**: Performs cross-process health checks on the Watcher every 120 minutes.

### 3. Signal Watcher (`start_railway_watcher.py`)
*   **Role**: Real-time monitor (60s checks) for ENTRY, TP, SL, and Duration Timeouts.
*   **Observability**: **Launcher Sniffer** captures task output to DB (`WATCHER_LOG`).
*   **Atomic Transitions**: Uses DB-level checks to prevent duplicate Telegram notifications.

### 4. Institutional Validator (`start_railway_validator.py`)
*   **Role**: Independent "Audit" layer cross-verifying signals with Pepperstone/Binance feeds.
*   **Observability**: Captured to DB via `VALIDATOR_LOG`.

### 5. Watchdog & Active Healing (`start_railway_watchdog.py`)
*   **Role**: System self-preservation and Telegram alerting.
*   **Active Healing**: Automatically runs `Janitor` to clear stuck signals if heartbeats stall for >15 min.
*   **Observability**: Captured to DB via `WATCHDOG_LOG`.

---

## 🔬 Unified Observability System (v3.8.5)
The system now implements a **Sniffer-Chain Architecture**:
*   **Process Sniffers**: Custom launchers wrap every service in a `subprocess.Popen` pipe, streaming `stdout/stderr` directly to `fx_analysis_log` in Supabase.
*   **Internal Health Monitor**: The `backend/internal_health_check.py` tool probes DB logs to reconstruct service state without needing Railway Dashboard access.
*   **Self-Ping**: The Web server performs an internal loopback request to verify networking success independently.

---

## 🧠 The Engine Components (`backend/quantix_core/engine/`)
1.  **`StructureEngineV1`**: Market Structure (BOS), FVG Identification.
2.  **`ConfidenceRefiner`**: Weighted scoring model (Structure, Session, Volatility, Trend).
3.  **`ConfidenceGate`**: Institutional threshold set to **80%** minimum for release.
4.  **`5W1H Metadata`**: Full transparency logic attached to every signal record.

---

## 📁 Repository Map
```text
Quantix_AI_Core/
├── backend/
│   ├── quantix_core/
│   │   ├── api/          # FastAPI & Route handlers
│   │   ├── engine/       # SMC Logic & Watchdog/Janitor
│   │   ├── database/     # Supabase SDK Wrapper
│   │   └── utils/        # Market Hours & Performance calculators
├── dashboard/            # HTML/JS (Dashboard UI)
├── Procfile              # Railway Distributed Process Definitions
└── start_railway_*.py    # Observability-enabled Launchers (v3.8.5)
```

---
**Version**: 3.8.5 (Unified Observability Enabled)  
**Status**: Production Stabilized / All Services Sniffed  
**API Endpoint**: `quantixapiserver-production.up.railway.app`
