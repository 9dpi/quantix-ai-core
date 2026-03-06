# 🌌 Quantix AI Core - Master Architecture v3.8.7
*The Single Source of Truth for Institutional Intelligence & Execution*

---

## 🏗️ 1. Architecture Philosophy
Quantix is designed as a **Distributed Market Intelligence Engine** operating on the **5W1H Transparency Framework** (Who, What, Where, When, Why, How). 

### Core Pillars:
1.  **Distributed Intelligence**: Micro-services running independently on Railway Cloud.
2.  **Institutional Validation**: Cross-verification of data via Binance & TwelveData feeds.
3.  **Unified Observability**: Global audit system with remote Telegram control.
4.  **Embedded Atomicity**: Integrated Watcher tasks within the Analyzer to prevent race conditions.

---

## 🛰️ 2. Distributed Service Map (Railway Ecosystem)

| Service | Script | Role | Observability Key |
| :--- | :--- | :--- | :--- |
| **API Server** | `start_railway_web.py` | Signal broadcast & Client sync | `UVICORN_LOG` |
| **Analyzer** | `start_railway_analyzer.py` | Brain + **Embedded Watcher** (v3.8) | `ANALYZER_LOG` |
| **Watcher** | `start_railway_watcher.py` | Standalone Monitor (Legacy Redundancy) | `WATCHER_LOG` |
| **Validator** | `start_railway_validator.py` | Discrepancy & Feed audit (Binance) | `VALIDATOR_LOG` |
| **Watchdog** | `start_railway_watchdog.py` | Active Healing (Janitor) & System Safety | `WATCHDOG_LOG` |

---

## 📊 3. End-to-End Signal Pipeline

```mermaid
graph TD
    A[Market Data: Binance/12Data] -->|T0: 300s Cycle| B(Analyzer Brain)
    B -->|Neural Reasoning 5W1H| C{Confidence Gate}
    C -->|< 70%| D[Drop: Lab Candidate]
    C -->|>= 70%| E[Release: PUBLISHED]
    E -->|Embedded Watcher| F[Supabase: fx_signals]
    F -->|Webhook| G[Telegram: Active Signal]
    G -->|Admin Interaction| H[Telegram: Remote audit]
    F -->|Sync| I[Dashboard: Live Control]
    I -->|Market Exit| J[Janitor: State Lockdown]
```

---

## 🧠 4. Strategy & Trading Rules (Institutional v3.8.7)

### Signal Release Logic:
*   **Confidence Threshold**: **70% (0.70)**.
*   **Asset**: EURUSD (M15 Primary).
*   **Refinement**: Neural weighted scoring (Structure + Session + Volatility).

### Dynamic Risk Management:
*   **Risk-Free Protocol**: Move SL to Entry (Breakeven) when price reaches **70%** toward TP.
*   **Max Pending**: 35 minutes (Entry window).
*   **Max Duration**: **150 minutes** (Redefined from 180m for institutional scalping).
*   **Entry Strategy**: Market Execution prioritized for confidence > 80% or FVG Proximity.

---

## 🔬 5. Global Observability & Control
### Remote Admin Commands (Telegram):
Admin can control the production engine directly from mobile:
*   `/audit`: Triggers a comprehensive global health check (Online + DB integrity).
*   `/unblock`: Manually triggers the Janitor to release stuck signals/pipelines.
*   `/status`: Checks real-time pulse of all worker instances.

### Audit Tooling:
*   `audit.bat`: Local/PC command for deep diagnostic reports.
*   `backend/audit_online.py`: External verify via Public API Gateway.

---

## 📁 6. Repository Ecosystem
The project is split into two specialized repositories:
1.  **`Quantix_AI_Core`**: The "Backend/Brain" containing analysis logic, database wrappers, and service launchers.
2.  **`quantix-live-execution`**: The "Frontend/Terminal" focused on real-time signal display and execution visualization.

---
**Version**: 3.8.7 | **Build**: 2026-03-05-UTC  
*Document verified 2026-03-05 by Antigravity AI.*

