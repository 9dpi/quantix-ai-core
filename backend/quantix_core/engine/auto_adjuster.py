"""
AutoAdjuster — Phase 5.1: Intelligent Auto-Adjustment System
============================================================
Extends SpreadAdjuster with self-learning capabilities:

    1. Time-of-day matrix       → spread variance by hour/day
    2. Volatility multiplier    → ATR-based real-time scaling
    3. Historical learning      → decay-weighted ewma from validation_events
    4. Buffer recommendation    → persists to DB for cross-process access

Key differences vs SpreadAdjuster (Phase 3):
    - SpreadAdjuster : static safety_margin, session lookup table
    - AutoAdjuster   : LEARNS optimal margin from actual TP/SL miss patterns

Flow:
    1. Every cycle: fetch recent validation_events
    2. Compute miss rate per hour-of-day bucket
    3. Adjust multipliers via EMA smoothing
    4. Write learned config to fx_analysis_log (for persistence)
    5. next get_buffer() call picks up updated multipliers

Usage:
    adj = AutoAdjuster(db=db, feed=feed)
    adj.learn()                    # runs one learning cycle
    buf = adj.get_buffer("EURUSD") # uses freshly updated multipliers
    adj.schedule(interval=3600)    # background thread: learn every hour

    # Full report
    report = adj.get_learning_report()
"""

import os
import math
import threading
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

from loguru import logger
from quantix_core.engine.spread_adjuster import SpreadAdjuster, _PIP_SIZE, _DEFAULT_SPREAD_PIPS

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# 24-hour miss rate matrix: keys = UTC hour, values = learned multiplier
# Initialised from Phase 3 session table, then refined by learning
_INITIAL_HOUR_MULT = {h: 1.0 for h in range(24)}
_INITIAL_HOUR_MULT.update({
    7: 2.0, 8: 1.8,          # London open
    12: 1.8, 13: 1.5,        # NY open
    21: 1.3, 22: 1.3,        # NY close
})

# EMA smoothing factor: higher = faster learning, lower = more stable
ALPHA = 0.15

# ATR period (number of candles for volatility estimate)
ATR_PERIOD = 14

# Minimum events per bucket before trusting the learned multiplier
MIN_BUCKET_EVENTS = 5

# Strategy label persisted to DB
_STRATEGY_LABEL = "auto_adjuster_v1"


class AutoAdjuster(SpreadAdjuster):
    """
    Self-learning spread buffer adjuster.

    Inherits get_buffer() / adjust_tp_sl() / analyze() from SpreadAdjuster,
    but replaces the static session multiplier table with a 24-bucket
    EMA-smoothed learned matrix updated from real validation_events.
    """

    def __init__(self, db=None, feed=None, safety_margin: float = 1.5):
        super().__init__(db=db, feed=feed, safety_margin=safety_margin)

        # Learned multiplier per hour-of-day (persists in memory; also written to DB)
        self._hour_multipliers: Dict[int, float] = dict(_INITIAL_HOUR_MULT)

        # ATR-based volatility estimate (updated each learn cycle)
        self._current_atr_pips: float = 5.0
        self._atr_mult:          float = 1.0

        # Thread lock for thread-safe updates
        self._lock = threading.Lock()

        # Tracking
        self._learn_cycles = 0
        self._last_learned_at: Optional[datetime] = None

        # Load persisted config from DB if available
        self._load_persisted_config()

    # ------------------------------------------------------------------
    # Override: session multiplier from learned matrix instead of lookup
    # ------------------------------------------------------------------

    def _get_session_multiplier(self) -> Tuple[str, float]:
        """Return the LEARNED multiplier for the current UTC hour."""
        now  = datetime.now(timezone.utc)
        hour = now.hour
        with self._lock:
            mult = self._hour_multipliers.get(hour, 1.0) * self._atr_mult
        return f"learned_h{hour:02d}", round(min(mult, 4.0), 3)  # cap at 4×

    # ------------------------------------------------------------------
    # Public: learning API
    # ------------------------------------------------------------------

    def learn(self, lookback_hours: int = 48) -> Dict:
        """
        Run one learning cycle. Reads validation_events from the last
        `lookback_hours` and updates hour-bucket multipliers via EMA.

        Returns a summary dict.
        """
        if not self.db:
            return {"error": "No DB connection — cannot learn."}

        try:
            since = (
                datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
            ).isoformat()

            rows = (
                self.db.client.table("validation_events")
                .select("is_discrepancy, check_type, created_at, validator_candle")
                .gte("created_at", since)
                .execute()
            ).data or []

        except Exception as e:
            return {"error": f"DB fetch failed: {e}"}

        if not rows:
            return {"warning": "No validation events in lookback window."}

        # Bucket events by UTC hour
        buckets: Dict[int, List[bool]] = {h: [] for h in range(24)}
        spreads: List[float] = []

        for row in rows:
            ts_str = row.get("created_at", "")
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                hour = ts.hour
            except Exception:
                continue

            is_disc = row.get("is_discrepancy", False)
            buckets[hour].append(is_disc)

            # Collect spread data for ATR proxy
            candle = row.get("validator_candle") or {}
            bid, ask = candle.get("bid"), candle.get("ask")
            if bid and ask:
                pip = 0.0001
                spreads.append((ask - bid) / pip)

        # Update multipliers via EMA per bucket
        updates: Dict[int, float] = {}
        with self._lock:
            for hour, events in buckets.items():
                if len(events) < MIN_BUCKET_EVENTS:
                    continue  # Not enough data to trust

                miss_rate   = sum(events) / len(events)
                # Target multiplier: 1.0 (0% miss) → 3.0 (100% miss)
                target_mult = 1.0 + (miss_rate * 2.0)
                # EMA update
                old_mult = self._hour_multipliers[hour]
                new_mult = (ALPHA * target_mult) + ((1 - ALPHA) * old_mult)
                self._hour_multipliers[hour] = round(new_mult, 4)
                updates[hour] = new_mult

            # ATR proxy: use 95th percentile spread as volatility indicator
            if spreads:
                sorted_s = sorted(spreads)
                p95 = sorted_s[int(len(sorted_s) * 0.95)]
                baseline = _DEFAULT_SPREAD_PIPS.get("EURUSD", 0.3)
                # ATR multiplier: if spread is > 2× baseline, boost buffer
                self._current_atr_pips = p95
                self._atr_mult = max(1.0, min(p95 / baseline / 2.0, 2.0))

        self._learn_cycles += 1
        self._last_learned_at = datetime.now(timezone.utc)

        summary = {
            "cycles":          self._learn_cycles,
            "learned_at":      self._last_learned_at.isoformat(),
            "events_processed": len(rows),
            "buckets_updated": len(updates),
            "atr_pips":        round(self._current_atr_pips, 3),
            "atr_mult":        round(self._atr_mult, 3),
            "top_risk_hours":  self._top_risk_hours(n=3),
        }

        logger.info(
            f"[AutoAdjuster] Learn cycle #{self._learn_cycles} done. "
            f"{len(updates)} buckets updated. "
            f"ATR={self._current_atr_pips:.2f}pips (×{self._atr_mult:.2f})"
        )

        # Persist to DB
        self._persist_config(summary)
        return summary

    def schedule(self, interval: int = 3600):
        """
        Start a background thread that calls learn() every `interval` seconds.
        Safe to call once during startup.
        """
        def _loop():
            while True:
                try:
                    self.learn()
                except Exception as e:
                    logger.error(f"[AutoAdjuster] Background learn failed: {e}")
                threading.Event().wait(interval)

        t = threading.Thread(target=_loop, daemon=True, name="AutoAdjuster-Learn")
        t.start()
        logger.info(f"[AutoAdjuster] Background learning scheduled every {interval}s")

    def get_learning_report(self) -> Dict:
        """Return a human-readable summary of the current learned state."""
        with self._lock:
            hour_table = dict(self._hour_multipliers)

        top_risk   = self._top_risk_hours(n=5)
        low_risk   = sorted(hour_table.items(), key=lambda x: x[1])[:3]

        return {
            "strategy":         _STRATEGY_LABEL,
            "learn_cycles":     self._learn_cycles,
            "last_learned_at":  self._last_learned_at.isoformat() if self._last_learned_at else None,
            "atr_pips":         round(self._current_atr_pips, 3),
            "atr_multiplier":   round(self._atr_mult, 3),
            "hour_multipliers": {f"{h:02d}:00": round(v, 4) for h, v in hour_table.items()},
            "top_risk_hours":   [{"hour": f"{h:02d}:00", "multiplier": round(m, 4)} for h, m in top_risk],
            "low_risk_hours":   [{"hour": f"{h:02d}:00", "multiplier": round(m, 4)} for h, m in low_risk],
            "recommendation":   (
                "✅ Learning stable — multipliers within normal range."
                if max(hour_table.values()) < 3.0 else
                "⚠️ Some hours showing high miss rate. Consider reducing position size at risk hours."
            ),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _top_risk_hours(self, n: int = 3) -> List[Tuple[int, float]]:
        """Return the N hours with the highest learned multiplier."""
        with self._lock:
            items = sorted(self._hour_multipliers.items(), key=lambda x: x[1], reverse=True)
        return items[:n]

    def _persist_config(self, summary: Dict):
        """Write learned config summary to fx_analysis_log for cross-process access."""
        if not self.db:
            return
        try:
            import json
            self.db.client.table("fx_analysis_log").insert({
                "timestamp":  self._last_learned_at.isoformat(),
                "asset":      "AUTO_ADJUSTER",
                "price":      self._current_atr_pips,
                "direction":  "LEARN_CYCLE",
                "confidence": self._atr_mult,
                "status":     "ONLINE",
                "strength":   self._learn_cycles,
                "refinement": json.dumps(summary, ensure_ascii=False)[:2000],
            }).execute()
        except Exception as e:
            logger.debug(f"[AutoAdjuster] Persist failed (non-critical): {e}")

    def _load_persisted_config(self):
        """Try to restore the previous learned state from DB on startup."""
        if not self.db:
            return
        try:
            rows = (
                self.db.client.table("fx_analysis_log")
                .select("confidence, strength, price, created_at")
                .eq("asset", "AUTO_ADJUSTER")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            ).data or []

            if rows:
                r = rows[0]
                self._atr_mult       = float(r.get("confidence", 1.0))
                self._current_atr_pips = float(r.get("price", 5.0))
                self._learn_cycles   = int(r.get("strength", 0))
                logger.info(
                    f"[AutoAdjuster] Restored from DB — "
                    f"cycles={self._learn_cycles} atr={self._current_atr_pips:.2f}pips"
                )
        except Exception:
            pass  # Silent fail — defaults are fine
