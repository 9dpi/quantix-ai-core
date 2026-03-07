# 🎯 QUANTIX AI CORE: SNAPSHOT MANIFEST
**Version:** v4.0.3-stable (Pre-MT4 Integration)
**Date:** 2026-03-07
**Environment:** Local Windows PC

## 1. System State (The Baseline)
This snapshot captures the exact state of the Quantix AI Core before any code for Phase 2 (MT4 Auto-Execution) is introduced. The system currently acts as a pure Signal Generator (Telegram & Webhook).

### Active Configurations (`settings.py`):
*   **Confidence Threshold:** `0.75` (75%)
*   **TP Distance:** `0.00070` (Fixed 7.0 pips)
*   **SL Distance:** Dynamic (`0.7x - 1.0x ATR`), min `10.0 pips`.
*   **R:R Baseline:** ~ `1:0.7`

### Core Engine Status:
*   `continuous_analyzer.py` is fully stable with session-based refinement and hard safety guards preventing 0-pip targets.
*   Database (`fx_signals`) accurately reflects signal lifecycle states (PENDING, ACTIVE, CLOSED_TP, CLOSED_SL).

## 2. Purpose of Snapshot
This is a strict **Rollback Point**. 
The upcoming MT4 Integration (Phase 1) will introduce new API endpoints (`mt4_bridge_server.py` or modifications to `api/main.py`) and modify the signal payload structure to include UUIDs (`signal_id`), Risk amounts, and formatting for MetaTrader. 

If the MT4 integration introduces latency issues, database locks, or corrupted payloads during local testing, we will `git checkout v4.0.3-pre-mt4` to instantly restore the pristine Telegram-only generation capabilities.

---
*Snapshot captured by Antigravity AI prior to commencing Phase 1.*
