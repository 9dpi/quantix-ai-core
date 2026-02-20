"""
SpreadAdjuster — Phase 3: Dynamic Spread Buffer Engine
======================================================
Calculates and applies real-time spread buffers to TP/SL levels
based on live and historical Pepperstone spread data.

Design principles:
  - Time-aware    : Spread widens dramatically during news / session opens
  - Volatility-aware : ATR-based multiplier when market is choppy
  - Asymmetric    : BUY and SELL require different buffer directions
  - Data-driven   : Learns from validation_events table in Supabase

Integration points:
  - signal_watcher.py      → apply buffer before TP/SL touch detection
  - run_pepperstone_validator.py → use accurate spread when logging
  - Phase 3.3 A/B testing  → compare buffered vs non-buffered accuracy

Usage:
    adjuster = SpreadAdjuster()

    # Get recommended buffer for right now
    buf = adjuster.get_buffer("EURUSD")

    # Adjust TP / SL before touch check
    adjusted_tp, adjusted_sl = adjuster.adjust_tp_sl(
        tp=1.08500, sl=1.08200, direction="BUY"
    )

    # Full report
    report = adjuster.analyze()
"""

import os
import statistics
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, List

from loguru import logger


# ---------------------------------------------------------------------------
# Constants & session time windows (UTC)
# ---------------------------------------------------------------------------

# Forex session windows where spread temporarily widens
_SPREAD_SESSIONS = {
    "london_open":  (7, 8),    # 07:00–08:00 UTC — high spread
    "ny_open":      (12, 13),  # 12:00–13:00 UTC — high spread
    "ny_close":     (21, 22),  # 21:00–22:00 UTC — moderate volatility
    "pre_weekend":  (21, 22),  # Friday-specific; handled separately
}

# Multipliers applied during high-volatility windows
_SESSION_MULTIPLIERS = {
    "london_open": 2.0,
    "ny_open":     1.8,
    "ny_close":    1.3,
    "normal":      1.0,
}

# Asset-specific pip scale (EURUSD = 0.0001 = 1 pip)
_PIP_SIZE = {
    "EURUSD": 0.0001,
    "GBPUSD": 0.0001,
    "AUDUSD": 0.0001,
    "USDJPY": 0.01,
    "USDCAD": 0.0001,
}

# Default spread assumption when no live data available (pips)
_DEFAULT_SPREAD_PIPS = {
    "EURUSD": 0.3,
    "GBPUSD": 0.5,
    "AUDUSD": 0.5,
    "USDJPY": 0.3,
    "USDCAD": 0.5,
}

# Safety margin (multiply the spread to get the buffer)
_SAFETY_MARGIN = 1.5


class SpreadAdjuster:
    """
    Dynamically adjusts TP/SL levels based on current broker spread.

    Phase 3 implementation:
    - Uses live spread data from feed.get_price()
    - Falls back to historical average if no live feed available
    - Applies session-time multiplier for high-volatility windows
    - Exposes .analyze() for the spread impact report
    """

    def __init__(
        self,
        db=None,
        feed=None,
        safety_margin: float = _SAFETY_MARGIN,
    ):
        """
        Args:
            db   : SupabaseConnection instance (for historical spread lookup)
            feed : BaseFeed instance (for real-time spread)
            safety_margin : Multiplier applied to spread → buffer (default 1.5)
        """
        self.db            = db
        self.feed          = feed
        self.safety_margin = safety_margin

        # Runtime spread cache: {symbol: (pips, timestamp)}
        self._spread_cache: Dict[str, Tuple[float, datetime]] = {}
        self._cache_ttl_seconds = 30  # Refresh live spread every 30s

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_buffer(self, symbol: str = "EURUSD") -> Dict:
        """
        Return the recommended buffer for this moment.

        Returns dict:
            spread_pips   : raw spread in pips
            buffer_pips   : recommended buffer after safety margin
            buffer_price  : buffer in price units
            session       : active session name
            multiplier    : session multiplier applied
            source        : "live_feed" | "historical_avg" | "default"
        """
        symbol = symbol.upper()
        pip = _PIP_SIZE.get(symbol, 0.0001)

        # 1. Get raw spread
        spread_pips, source = self._get_spread_pips(symbol)

        # 2. Session multiplier
        session, multiplier = self._get_session_multiplier()

        # 3. Final buffer
        buffer_pips  = spread_pips * self.safety_margin * multiplier
        buffer_price = round(buffer_pips * pip, 6)

        result = {
            "symbol":       symbol,
            "spread_pips":  round(spread_pips, 3),
            "buffer_pips":  round(buffer_pips, 3),
            "buffer_price": buffer_price,
            "session":      session,
            "multiplier":   multiplier,
            "source":       source,
            "timestamp":    datetime.now(timezone.utc).isoformat(),
        }

        logger.debug(
            f"[SpreadAdjuster] {symbol} buffer={buffer_pips:.3f}pips "
            f"({source}, session={session}×{multiplier})"
        )
        return result

    def adjust_tp_sl(
        self,
        tp: float,
        sl: float,
        direction: str,
        symbol: str = "EURUSD",
    ) -> Tuple[float, float, Dict]:
        """
        Apply spread buffer to TP/SL levels.

        Buffer logic (direction-aware):
            BUY  → TP raised  (needs higher high to confirm)
                 → SL lowered (needs lower low to confirm)
            SELL → TP lowered (needs lower low to confirm)
                 → SL raised  (needs higher high to confirm)

        Returns:
            (adjusted_tp, adjusted_sl, buffer_info_dict)
        """
        buf = self.get_buffer(symbol)
        b   = buf["buffer_price"]

        if direction.upper() == "BUY":
            adj_tp = round(tp + b, 5)
            adj_sl = round(sl - b, 5)
        else:  # SELL
            adj_tp = round(tp - b, 5)
            adj_sl = round(sl + b, 5)

        return adj_tp, adj_sl, buf

    def analyze(self, symbol: str = "EURUSD", lookback_days: int = 14) -> Dict:
        """
        Generate a spread impact analysis report.

        Reads validation_events from Supabase to compute:
        - Average spread during validations
        - Peak spread windows
        - Impact on TP/SL detection accuracy
        - Recommended buffer

        Returns rich dict for logging / display.
        """
        report = {
            "symbol":       symbol,
            "lookback_days": lookback_days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_source":  "validation_events (Supabase)",
        }

        if not self.db:
            report["error"] = "No database connection — cannot run analysis."
            return report

        try:
            since = (
                datetime.now(timezone.utc) - timedelta(days=lookback_days)
            ).isoformat()

            rows = (
                self.db.client
                .table("validation_events")
                .select("validator_candle, is_discrepancy, check_type, created_at")
                .gte("created_at", since)
                .execute()
            ).data or []

        except Exception as e:
            report["error"] = f"DB fetch failed: {e}"
            return report

        if not rows:
            report["warning"] = "No validation events found in the lookback window."
            return report

        # Extract spread values from candle records
        spreads: List[float] = []
        for row in rows:
            candle = row.get("validator_candle") or {}
            bid    = candle.get("bid")
            ask    = candle.get("ask")
            if bid and ask:
                pip = _PIP_SIZE.get(symbol, 0.0001)
                spread_pips = round((ask - bid) / pip, 3)
                spreads.append(spread_pips)

        total     = len(rows)
        disc_rows = [r for r in rows if r.get("is_discrepancy")]
        tp_misses = [r for r in disc_rows if "TP" in (r.get("check_type") or "")]
        sl_misses = [r for r in disc_rows if "SL" in (r.get("check_type") or "")]

        disc_rate = len(disc_rows) / total * 100 if total > 0 else 0.0

        report["total_validations"] = total
        report["discrepancy_count"] = len(disc_rows)
        report["discrepancy_rate_pct"] = round(disc_rate, 2)
        report["tp_mismatches"] = len(tp_misses)
        report["sl_mismatches"] = len(sl_misses)

        if spreads:
            report["avg_spread_pips"]  = round(statistics.mean(spreads), 3)
            report["max_spread_pips"]  = round(max(spreads), 3)
            report["min_spread_pips"]  = round(min(spreads), 3)
            report["p95_spread_pips"]  = round(
                sorted(spreads)[int(len(spreads) * 0.95)], 3
            )
            recommended = report["avg_spread_pips"] * _SAFETY_MARGIN
            report["recommended_buffer_pips"] = round(recommended, 3)
            report["recommended_buffer_price"] = round(
                recommended * _PIP_SIZE.get(symbol, 0.0001), 6
            )
        else:
            report["note"] = (
                "No bid/ask data in candle records. "
                "Spread analysis requires Phase 2 MT5 feed (bid/ask populated)."
            )
            buf = self.get_buffer(symbol)
            report["recommended_buffer_pips"]  = buf["buffer_pips"]
            report["recommended_buffer_price"]  = buf["buffer_price"]

        # Recommendation logic (mirrors roadmap decision thresholds)
        if disc_rate < 5:
            report["recommendation"] = (
                "✅ Discrepancy < 5% — Current setup is accurate. "
                "Adding buffer is optional (conservative improvement only)."
            )
        elif disc_rate < 10:
            report["recommendation"] = (
                "⚠️  Discrepancy 5-10% — Apply spread buffer. "
                f"Recommended: {report.get('recommended_buffer_pips', '0.5')} pips."
            )
        else:
            report["recommendation"] = (
                "🚨 Discrepancy > 10% — Upgrade to MT5 real feed urgently. "
                "Binance proxy alone is insufficient."
            )

        return report

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_spread_pips(self, symbol: str) -> Tuple[float, str]:
        """
        Get best available spread estimate.
        Priority: live_feed → cache → historical_avg → default constant.
        """
        # A. Try live feed
        if self.feed:
            cached = self._spread_cache.get(symbol)
            if cached:
                pips, ts = cached
                age = (datetime.now(timezone.utc) - ts).total_seconds()
                if age < self._cache_ttl_seconds:
                    return pips, "live_feed (cached)"

            try:
                data = self.feed.get_price(symbol)
                if data and data.get("spread_pips"):
                    pips = float(data["spread_pips"])
                    self._spread_cache[symbol] = (pips, datetime.now(timezone.utc))
                    return pips, "live_feed"
            except Exception:
                pass

        # B. Try historical average from DB
        if self.db:
            try:
                since = (
                    datetime.now(timezone.utc) - timedelta(hours=24)
                ).isoformat()
                rows = (
                    self.db.client
                    .table("validation_events")
                    .select("validator_candle")
                    .gte("created_at", since)
                    .limit(50)
                    .execute()
                ).data or []

                pip = _PIP_SIZE.get(symbol, 0.0001)
                spreads = []
                for row in rows:
                    candle = row.get("validator_candle") or {}
                    bid, ask = candle.get("bid"), candle.get("ask")
                    if bid and ask:
                        spreads.append((ask - bid) / pip)

                if spreads:
                    return round(statistics.mean(spreads), 3), "historical_avg"
            except Exception:
                pass

        # C. Static default
        default = _DEFAULT_SPREAD_PIPS.get(symbol, 0.5)
        return default, "default"

    def _get_session_multiplier(self) -> Tuple[str, float]:
        """Return the session name and spread multiplier for the current UTC time."""
        now = datetime.now(timezone.utc)
        hour = now.hour
        weekday = now.weekday()  # 0=Mon … 4=Fri

        if hour in range(*_SPREAD_SESSIONS["london_open"]):
            return "london_open", _SESSION_MULTIPLIERS["london_open"]

        if hour in range(*_SPREAD_SESSIONS["ny_open"]):
            return "ny_open", _SESSION_MULTIPLIERS["ny_open"]

        if weekday == 4 and hour in range(*_SPREAD_SESSIONS["pre_weekend"]):
            return "pre_weekend", _SESSION_MULTIPLIERS["ny_close"]

        if hour in range(*_SPREAD_SESSIONS["ny_close"]):
            return "ny_close", _SESSION_MULTIPLIERS["ny_close"]

        return "normal", _SESSION_MULTIPLIERS["normal"]
