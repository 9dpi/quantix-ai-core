# QUANTIX AI - LIFECYCLE TIMING & ROTATION POLICY

## 🔄 The Signal Rotation Cycle

The system enforces strict time limits on every signal to ensure capital efficiency and constant opportunity flow. A signal creates a "lock" on the system, preventing new signals until the current one is resolved.

This resolution is guaranteed to happen within a maximum timeframe due to our **Auto-Exit Protocols**:

### 1. Waiting Phase (Pre-Entry)
*   **Maximum Duration:** `15 Minutes`
*   **Logic:** Once a signal is published, the market has 15 minutes to trigger the entry price.
*   **Outcome A:** Price hits Entry -> Signal becomes **ACTIVE** (Phase 2).
*   **Outcome B:** Time runs out -> Signal is **CANCELLED** (`EXPIRED`).
    *   *System Action:* Lock is released immediately. Ready for new signal.

### 2. Active Phase (Post-Entry)
*   **Maximum Duration:** `30 Minutes`
*   **Logic:** Once a trade is active, it is monitored for a maximum of 30 minutes to result in a Win or Loss.
*   **Outcome A:** Price hits TP or SL -> Signal is **CLOSED** (`WIN/LOSS`).
*   **Outcome B:** Time runs out (30m) -> Signal is **FORCE CLOSED** (`TIME_EXIT`).
    *   *System Action:* Logic closes trade at current market price. Lock is released. Ready for new signal.

## ⏱️ Total Maximum Cycle Time
In the absolute worst-case scenario (signal triggers entry at minute 14, then runs for full 30 minutes), a single signal cycle can last maximum:
**45 Minutes**

After this period, the system is **guaranteed** to be free and scanning for the next opportunity.
