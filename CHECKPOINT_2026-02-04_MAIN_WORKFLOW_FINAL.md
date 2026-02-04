# 🏁 CHECKPOINT: Main Workflow - Quantix All-on-Cloud v3.0 (2026-02-04)

## 🏗️ Architecture Overview: All-on-Cloud
The system has been fully migrated from a Hybrid model to a **Full Cloud Architecture** on Railway. Local environment dependencies have been removed.

---

## 🛠️ The 3 Pillars: WHAT, WHEN, HOW

### 1. WHAT (Components)
*   **The Brain (Analyzer):** Runs on Railway. Fetches market data, calculates AI confidence, and creates signals.
*   **The Guard (Watcher):** Runs on Railway. Monitors active signals for entry/exit points (TP, SL, Expiry).
*   **The Database (Supabase):** Single Source of Truth (SSOT). All services sync data here via `fx_signals`.
*   **The Voice (Telegram/Web):** Telegram Bot for alerts and SignalGeniusAI.com for visualization.

### 2. WHEN (Lifecycle & Timing)
*   **Analyzer Pulse:** Every **120 seconds** (Optimized for TwelveData quota).
*   **Watcher Pulse:** Every **300 seconds** (Live monitoring cycle).
*   **Signal Window:** 15m (Validation) -> 30m (Monitoring) -> 45m (Total Max).
*   **Cooldown:** 30-minute hard gap between signal releases.

### 3. HOW (Technical Logic & Integrity)
*   **DB-First Atomic Updates:** Watcher updates the Database **BEFORE** notifying Telegram. 
    *   *Mechanism:* `UPDATE ... WHERE state = 'WAITING'`. 
    *   *Result:* Only one service can succeed. Zero spam.
*   **Global Hard Lock:** Analyzer checks `fx_signals` for any `PUBLISHED` or `ENTRY_HIT` records before releasing new ones. 
    *   *Result:* Ensures only one active trade/signal exists at a time across the entire system.
*   **Local Safeguard:** All code now contains a `LOCAL-MACHINE` detection. Local instances automatically disable Telegram outputs unless explicitly overridden.

---

## 📡 Channel Configuration
*   **Community Group:** `-1003211826302` (Public Signals & Result Replies).
*   **Admin Channel:** `7985984228` (System Health & Commands).
*   **Confidence Threshold:** **95%** (Only high-probability "Ultra Signals" are published).

---

## 🚀 Final Production State
*   **Local Machine:** 🔴 DECOMMISSIONED (Taskkilled).
*   **Railway Cloud:** 🟢 ACTIVE (3 Services: Analyzer, Watcher, API).
*   **Sync Status:** 🟢 PUSHED to `main` branch across all repos.

**Last Updated:** 2026-02-04 19:57 (GMT+7)
