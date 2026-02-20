"""
Pepperstone Validation Layer - Independent Observer
===================================================
Runs in parallel with the main system to validate signals
against a pluggable market data feed.

Phase 1 (default) : Binance proxy     → feed_source="binance_proxy"
Phase 2A          : MetaTrader 5 API  → feed_source="mt5_api"
Phase 2B          : cTrader Open API  → feed_source="ctrader_api"

Architecture:
    - Passive observer (reads DB, writes validation_events table)
    - Runs in a separate process / screen session
    - Can be stopped at any time without affecting the main system
    - Feed source is hot-swappable via CLI arg or environment variable

Usage:
    # Phase 1 (default Binance proxy)
    python backend/run_pepperstone_validator.py

    # Phase 2A (MT5 / Pepperstone real feed)
    python backend/run_pepperstone_validator.py --feed mt5_api

    # Phase 2B (cTrader — stub, not yet fully operational)
    python backend/run_pepperstone_validator.py --feed ctrader_api

Environment variables:
    VALIDATOR_FEED      – Override feed source (binance_proxy | mt5_api | ctrader_api)
    SPREAD_BUFFER_PIPS  – Override spread buffer (default: 0.3 pips = 0.00003)
    MT5_LOGIN / MT5_PASSWORD / MT5_SERVER   – MT5 credentials
    CTRADER_CLIENT_ID / CTRADER_ACCESS_TOKEN / CTRADER_ACCOUNT_ID – cTrader creds
"""

import argparse
import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List

from loguru import logger

from quantix_core.database.connection import SupabaseConnection
from quantix_core.config.settings import settings
from quantix_core.feeds import get_feed, BaseFeed

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
IS_RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") is not None

if IS_RAILWAY:
    logger.add(
        lambda msg: print(msg, end=""),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
    )
else:
    VALIDATION_LOG = Path(__file__).parent / "validation_audit.jsonl"
    logger.add(
        str(VALIDATION_LOG),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
        rotation="10 MB",
        retention="30 days",
    )


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

class PepperstoneValidator:
    """
    Pluggable validation layer.

    Phase 2 change: feed_source drives which BaseFeed implementation
    is used. All validation logic stays identical — only the price
    data source changes.
    """

    def __init__(self, feed_source: str = "binance_proxy", **feed_kwargs):
        self.db = SupabaseConnection()
        self.feed_source = feed_source

        # Spread buffer: default 0.3 pips, overridable via env
        raw_buffer = float(os.getenv("SPREAD_BUFFER_PIPS", "0.3"))
        self.spread_buffer = raw_buffer * 0.0001   # Convert pips → price

        # Instantiate the selected feed
        self.feed: BaseFeed = get_feed(feed_source, **feed_kwargs)

        self.check_interval = 60        # seconds between validation cycles
        self.tracked_signals: Dict = {} # {signal_id: tracking_state}
        self.cycle_count = 0

        logger.info(
            f"🔍 PepperstoneValidator ready "
            f"[feed={feed_source}, spread_buffer={self.spread_buffer:.5f}]"
        )

        # Connectivity check at startup
        if not self.feed.is_available():
            logger.warning(
                f"⚠️  Feed '{feed_source}' is not currently reachable. "
                "Validator will retry each cycle."
            )
        else:
            logger.success(f"✅ Feed '{feed_source}' connected successfully.")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        """Blocking main loop — runs until KeyboardInterrupt."""
        logger.info("🚀 Validation Layer started [Independent Observer Mode]")

        while True:
            try:
                self.validation_cycle()
            except KeyboardInterrupt:
                logger.info("🛑 Validation Layer stopped by user.")
                break
            except Exception as e:
                logger.error(f"Validation cycle error: {e}")

            self.cycle_count += 1

            # Heartbeat every 5 cycles (~5 minutes)
            if self.cycle_count % 5 == 0:
                self._log_heartbeat()

            time.sleep(self.check_interval)

    # ------------------------------------------------------------------
    # Validation cycle
    # ------------------------------------------------------------------

    def validation_cycle(self):
        """Single pass: fetch active signals → get price → validate each."""
        signals = self._fetch_active_signals()

        if not signals:
            logger.debug("No active signals to validate.")
            return

        logger.info(f"Validating {len(signals)} active signal(s) via {self.feed_source}")

        market_data = self.feed.get_price("EURUSD")

        if not market_data:
            logger.warning(
                f"⚠️  Could not fetch price from '{self.feed_source}'. "
                "Skipping this cycle."
            )
            return

        logger.debug(
            f"📊 Market: bid={market_data['bid']} ask={market_data['ask']} "
            f"spread={market_data['spread_pips']}pips  [{market_data['source']}]"
        )

        for signal in signals:
            self._validate_signal(signal, market_data)

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    def _fetch_active_signals(self) -> List[Dict]:
        try:
            res = (
                self.db.client
                .table("fx_signals")
                .select("*")
                .in_("state", ["WAITING_FOR_ENTRY", "ENTRY_HIT"])
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching signals from DB: {e}")
            return []

    # ------------------------------------------------------------------
    # Signal validation logic
    # ------------------------------------------------------------------

    def _validate_signal(self, signal: Dict, market_data: Dict):
        """Route signal to entry or TP/SL validation based on its state."""
        signal_id = signal.get("id")
        state = signal.get("state")

        if signal_id not in self.tracked_signals:
            self.tracked_signals[signal_id] = {
                "first_seen":      datetime.now(timezone.utc).isoformat(),
                "entry_validated": False,
                "tp_validated":    False,
                "sl_validated":    False,
                "discrepancies":   [],
            }

        tracking = self.tracked_signals[signal_id]

        if state == "WAITING_FOR_ENTRY":
            self._validate_entry(signal, market_data, tracking)
        elif state == "ENTRY_HIT":
            self._validate_tp_sl(signal, market_data, tracking)

    def _validate_entry(self, signal: Dict, market_data: Dict, tracking: Dict):
        if tracking["entry_validated"]:
            return

        entry_price = signal.get("entry_price")
        direction   = signal.get("direction", "BUY")

        # Use bid for SELL entry, ask for BUY entry (realistic broker fill)
        if direction == "BUY":
            feed_triggered = market_data["ask"] >= entry_price
        else:
            feed_triggered = market_data["bid"] <= entry_price

        main_triggered = (signal.get("state") == "ENTRY_HIT")

        if feed_triggered != main_triggered:
            disc = self._build_discrepancy(
                disc_type="ENTRY_MISMATCH",
                signal=signal,
                market_data=market_data,
                feed_says="TRIGGERED" if feed_triggered else "NOT_TRIGGERED",
                main_says="TRIGGERED" if main_triggered else "NOT_TRIGGERED",
                details={
                    "entry_price": entry_price,
                    "market_high": market_data["high"],
                    "market_low":  market_data["low"],
                    "bid":        market_data["bid"],
                    "ask":        market_data["ask"],
                },
            )
            tracking["discrepancies"].append(disc)
            self._log_discrepancy(disc, market_data)

        elif feed_triggered and main_triggered:
            self._log_checkpoint(signal, "ENTRY", market_data)
            tracking["entry_validated"] = True

    def _validate_tp_sl(self, signal: Dict, market_data: Dict, tracking: Dict):
        direction = signal.get("direction", "BUY")
        tp = signal.get("tp")
        sl = signal.get("sl")

        buf = self.spread_buffer

        if direction == "BUY":
            feed_tp_hit = market_data["high"] >= (tp + buf)
            feed_sl_hit = market_data["low"]  <= (sl - buf)
        else:
            feed_tp_hit = market_data["low"]  <= (tp - buf)
            feed_sl_hit = market_data["high"] >= (sl + buf)

        # If both hit in the same candle → assume SL (conservative)
        if feed_tp_hit and feed_sl_hit:
            logger.warning(
                f"⚠️  Signal {signal['id']}: TP and SL both triggered in same candle. "
                "Prioritising SL (conservative safety rule)."
            )
            feed_tp_hit = False

        main_state = signal.get("state")

        # TP check
        if feed_tp_hit and not tracking["tp_validated"]:
            if main_state != "TP_HIT":
                disc = self._build_discrepancy(
                    "TP_MISMATCH", signal, market_data,
                    "TP_HIT", main_state,
                    {"tp": tp, "high": market_data["high"], "ask": market_data["ask"]},
                )
                tracking["discrepancies"].append(disc)
                self._log_discrepancy(disc, market_data)
            else:
                self._log_checkpoint(signal, "TP", market_data)
            tracking["tp_validated"] = True

        # SL check
        if feed_sl_hit and not tracking["sl_validated"]:
            if main_state != "SL_HIT":
                disc = self._build_discrepancy(
                    "SL_MISMATCH", signal, market_data,
                    "SL_HIT", main_state,
                    {"sl": sl, "low": market_data["low"], "bid": market_data["bid"]},
                )
                tracking["discrepancies"].append(disc)
                self._log_discrepancy(disc, market_data)
            else:
                self._log_checkpoint(signal, "SL", market_data)
            tracking["sl_validated"] = True

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    def _build_discrepancy(
        self,
        disc_type: str,
        signal: Dict,
        market_data: Dict,
        feed_says: str,
        main_says: str,
        details: Dict,
    ) -> Dict:
        return {
            "type":          disc_type,
            "signal_id":     signal.get("id"),
            "asset":         signal.get("asset", "EURUSD"),
            "feed_source":   self.feed_source,
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "feed_says":     feed_says,
            "main_sys_says": main_says,
            "market_price":  market_data["close"],
            "bid":           market_data["bid"],
            "ask":           market_data["ask"],
            "spread_pips":   market_data["spread_pips"],
            "details":       details,
        }

    def _log_discrepancy(self, disc: Dict, candle: Dict):
        logger.warning(
            f"⚠️  DISCREPANCY [{disc['type']}] signal={disc['signal_id']} "
            f"feed={disc['feed_says']} main={disc['main_sys_says']}"
        )

        # Write to local file (when not on Railway)
        if not IS_RAILWAY:
            disc_file = Path(__file__).parent / "validation_discrepancies.jsonl"
            with open(disc_file, "a") as f:
                f.write(json.dumps(disc) + "\n")
        else:
            logger.info(f"DISCREPANCY_DATA: {json.dumps(disc)}")

        # Save to Supabase for self-learning
        try:
            self.db.client.table("validation_events").insert({
                "signal_id":        disc.get("signal_id"),
                "asset":            disc.get("asset", "EURUSD"),
                "feed_source":      disc.get("feed_source", self.feed_source),
                "validator_price":  candle.get("close", 0),
                "validator_candle": candle,
                "check_type":       disc.get("type", "UNKNOWN"),
                "main_system_state":disc.get("main_sys_says", "UNKNOWN"),
                "is_discrepancy":   True,
                "discrepancy_type": disc.get("type"),
                "meta_data":        disc.get("details", {}),
            }).execute()
            logger.success(
                f"💾 Discrepancy saved to DB [signal={disc['signal_id']}]"
            )
        except Exception as e:
            logger.error(f"❌ Failed to save discrepancy to DB: {e}")

    def _log_checkpoint(self, signal: Dict, check_type: str, candle: Dict):
        """Log a positive validation match (passed checkpoint)."""
        logger.info(
            f"✅ VALIDATED [{check_type}] signal={signal.get('id')} "
            f"price={candle.get('close')} source={candle.get('source')}"
        )
        try:
            self.db.client.table("validation_events").insert({
                "signal_id":         signal.get("id"),
                "asset":             signal.get("asset", "EURUSD"),
                "feed_source":       self.feed_source,
                "validator_price":   candle.get("close", 0),
                "validator_candle":  candle,
                "check_type":        check_type,
                "main_system_state": signal.get("state"),
                "is_discrepancy":    False,
                "meta_data":         {"confidence": "HIGH", "match": True},
            }).execute()
        except Exception:
            pass  # Silent fail for positive checks

    def _log_heartbeat(self):
        """Emit a heartbeat entry to the analysis log table every 5 cycles."""
        try:
            self.db.client.table(settings.TABLE_ANALYSIS_LOG).insert({
                "timestamp":  datetime.now(timezone.utc).isoformat(),
                "asset":      "VALIDATOR",
                "price":      0,
                "direction":  "HEARTBEAT",
                "confidence": 1.0,
                "status":     "ONLINE",
                "strength":   1.0,
                "refinement": (
                    f"Validation Layer alive. "
                    f"Feed={self.feed_source}. "
                    f"Monitoring {len(self.tracked_signals)} signal(s). "
                    f"Cycle #{self.cycle_count}."
                ),
            }).execute()
        except Exception:
            pass  # Heartbeat is best-effort


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Pepperstone Validation Layer — Independent Observer"
    )
    parser.add_argument(
        "--feed",
        choices=["binance_proxy", "mt5_api", "ctrader_api"],
        default=os.getenv("VALIDATOR_FEED", "binance_proxy"),
        help="Market data feed source (default: binance_proxy)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 80)
    print("  PEPPERSTONE VALIDATION LAYER — INDEPENDENT OBSERVER  (Phase 2)")
    print("=" * 80)
    print()
    print(f"  Feed source        : {args.feed}")
    print(f"  Spread buffer      : {float(os.getenv('SPREAD_BUFFER_PIPS', '0.3'))} pips")
    print(f"  Running on Railway : {IS_RAILWAY}")
    print()
    print("  This layer is a PASSIVE OBSERVER.")
    print("  It does NOT interfere with the main production system.")
    print()

    validator = PepperstoneValidator(feed_source=args.feed)
    validator.run()


if __name__ == "__main__":
    main()
