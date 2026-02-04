# CHECKPOINT 2026-02-04: SINGLE SOURCE OF TRUTH & ANTI-SPAM ARCHITECTURE

## 🎯 Objective
Eliminate duplicate telegram notifications and ensure system stability by implementing a strict "Single Source of Truth" architecture with aggressive zombie cleanup.

## 🛠Key Implementations

### 1. Global Hard Lock (Anti-Burst)
- **Constraint:** Only ONE active signal (`WAITING_FOR_ENTRY` or `ENTRY_HIT`) allowed system-wide.
- **Enforcement:** `ContinuousAnalyzer` checks Database before generating any new signal.
- **Fail-safe:** If an active signal exists, new opportunities are deferred.

### 2. Atomic Notification Guard
- **Mechanism:** `SignalWatcher` now checks for a valid `telegram_message_id` before sending ANY notification (Entry, TP, SL, Expired).
- **Rule:** 
  - If `telegram_message_id` exists: Send Reply Notification (Correct).
  - If `telegram_message_id` is NULL: Do NOT send Telegram. Log internally only.
- **Benefit:** Prevents internal/duplicate signals from spamming the Telegram channel as "new" messages without context.

### 3. Aggressive Zombie Cleanup
- **Problem:** Old worker processes or stuck instances were pumping "Zombie" signals (Internal signals with no TG ID) into the DB, blocking legitimate signals.
- **Solution:** `ContinuousAnalyzer` now runs a "Nuke Protocol" every cycle (2 mins).
- **Logic:** Any `WAITING` signal older than 2 minutes with NO Telegram ID is instantly `CANCELLED` (Result: `CANCELLED_ZOMBIE`).
- **Result:** Keeps the pipeline clear for fresh, legitimate signals.

### 4. Service Decoupling
- **API Server:** Now strictly Passive (Read-Only). All background workers removed.
- **Analyzer:** Specialized Worker for Signal Generation & Public Release.
- **Watcher:** Specialized Worker for Lifecycle Management & Replies.
- **Separation:** Prevents "Split Brain" issues where API server and Workers compete to process signals.

## ⚙️ Configuration Snapshot
- **Analyzer Interval:** 120s (2 mins) - Optimized for 800 req/day quota.
- **Watcher Interval:** 240s (4 mins).
- **Telegram Chat ID:** `-1003211826302` (Community).
- **API Key:** TwelveData Key verified & active.

## 🚀 Deployment Status
- **Local:** All python processes killed.
- **Cloud (Railway):** Deployed with strict 1-replica configuration per worker.
- **Database:** Cleaned of all stuck pending signals.

## 📝 Action Items for Next Cycle
- Monitor Telegram for the next valid signal reply chain.
- Ensure Railway variables `TWELVE_DATA_API_KEY` are consistent across services.
- **Do NOT** manually restart local workers to avoid "Zombie" regression.
