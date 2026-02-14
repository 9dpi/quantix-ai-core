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
*   **Two-Phase Signal Creation (v3.0):** 
    *   **Phase 1 (PREPARE):** Signal record created in DB with state `PREPARED` (Invisible to Watcher/UI).
    *   **Phase 2 (NOTIFY):** Signal pushed to Telegram. Success yields a `message_id`.
    *   **Phase 3 (COMMIT):** Atomic promotion to `WAITING_FOR_ENTRY` ONLY if `message_id` is present.
    *   *Result:* Guaranteed 1:1 mapping between Database and Telegram. Zero Zombies.
*   **DB-First Atomic Status Updates:** Watcher updates the Database **BEFORE** notifying Telegram for TP/SL hits. 
    *   *Mechanism:* `UPDATE ... WHERE state = 'WAITING_FOR_ENTRY'`. 
    *   *Result:* Only one service can succeed. Zero duplicate notifications.
*   **Global Hard Lock (User-Facing Only):** Analyzer checks `fx_signals` for any `WAITING_FOR_ENTRY` or `ENTRY_HIT` records. `PREPARED` signals are ignored by the lock.
    *   *Result:* One active trade at a time, but Telegram failures don't block the next cycle.
*   **Local Safeguard:** All code now contains a `LOCAL-MACHINE` detection. Local instances automatically disable Telegram outputs unless explicitly overridden.

---

## 📡 Channel Configuration
*   **Community Group:** `-1003211826302` (Public Signals & Result Replies).
*   **Admin Channel:** `7985984228` (System Health & Commands).
*   **Confidence Threshold:** **90%** (Signals >= 0.90 are promoted to Public Release).

---

## 🚀 Final Production State
*   **Local Machine:** 🔴 DECOMMISSIONED (Taskkilled).
*   **Railway Cloud:** 🟢 ACTIVE (3 Services: Analyzer, Watcher, API).
*   **Sync Status:** 🟢 PUSHED to `main` branch across all repos.

**Last Updated:** 2026-02-04 19:57 (GMT+7)
