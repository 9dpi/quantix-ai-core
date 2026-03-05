# 📋 Quantix AI Core - Daily Audit Checklist (v3.8.5 Standard)
**Last Audit Date:** 2026-03-05  
**Auditor:** Antigravity (Assistant)
**System Status:** 🟢 PRODUCTION STABILIZED

---

## 🏥 1. Institutional Infrastructure Health
| Service | Status | Heartbeat | Observability (Sniffer) |
| :--- | :--- | :--- | :--- |
| **API Server** | 🟢 OK | < 1m | `UVICORN_LOG`: Active (HTTP 200) |
| **Analyzer** | 🟢 OK | < 5m | `ANALYZER_LOG`: Cycle processing |
| **Watcher** | 🟢 OK | < 1m | `WATCHER_LOG`: Real-time monitoring |
| **Validator** | 🟢 OK | < 5m | `VALIDATOR_LOG`: Price verifying |
| **Watchdog** | 🟢 OK | < 5m | `WATCHDOG_LOG`: System safe |

---

## 🔬 2. Observability & Sniffer Audit
### ✅ Live Log Verification:
Run the following command to verify all cloud services are communicating:
`python backend/internal_health_check.py`

- [ ] **UVICORN_LOG**: Verify 200 OK responses from Gateway.
- [ ] **ANALYZER_LOG**: Ensure "Starting analysis cycle" appears every 5m.
- [ ] **WATCHER_LOG**: Confirm price polling is active for open signals.
- [ ] **DB Connectivity**: Pulse Age < 5.0 mins for all primary assets.

---

## 🚀 3. Strategy v3.8 Institutional Audit
### ✅ Execution Protocol:
1.  **Market-Only Entry**:
    *   [ ] Signals (Conf >= 80%) MUST execute as Market Orders (Zero Miss Policy).
2.  **5W1H Metadata Check**:
    *   [ ] Verify `intelligence_reasoning` field exists for all today's signals.
3.  **Capital Efficiency**:
    *   [ ] **Duration Lock**: Ensure signals close at exactly **150 minutes** (v3.8 limit) if TP/SL not hit.
4.  **Risk-Free Protocol**:
    *   [ ] **Breakeven**: SL must move to Entry at **70%** distance to TP.

---

## 🎯 4. Signal Intelligence Snapshot
**Target Win Rate: 90%**

| Asset | Result | Confidence | 5W1H Reasoning | Note |
| :--- | :--- | :--- | :--- | :--- |
| EURUSD | ... | 82% | Structure: BOS, Session: NY | ... |

---

## 🛡️ 5. Survivability & Resilience
### ✅ Fail-safe Verification:
- **API Domain**: `https://quantixapiserver-production.up.railway.app` (Verified).
- **Auto-Restarts**: Audit `fx_analysis_log` for `AUTO_RESTART_ATTEMPT` entries.
- **Janitor Cleanup**: Verify no signals are stuck in `WAITING` state > 35m.
- **Critical Alerts**: Admin Telegram must receive heartbeat "System Stabilized" after deployment recovery.

---
### 🛠️ Audit Toolbox (CLI)
*   **Full Health**: `python backend/internal_health_check.py`
*   **Signals Check**: `python backend/check_signals.py`
*   **Log Sniffer**: `python backend/clean_crash.py`

*End of Report. System is operating within v3.8.5 Institutional Parameters.*
