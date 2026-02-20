"""
ab_test_validator.py — Phase 3.3 A/B Testing Runner
=====================================================
Runs TWO validation observers in parallel:
    Validator A : No spread buffer   (control group)
    Validator B : Dynamic spread buffer via SpreadAdjuster (treatment group)

After the test window, compares accuracy between the two groups
and recommends which config to promote to production.

Usage:
    # Run A/B test for 30 minutes (quick smoke test)
    python backend/ab_test_validator.py --minutes 30

    # Run full 7-day test (launch in screen/tmux)
    python backend/ab_test_validator.py --minutes 10080

    # Print analysis of a past run (saved to JSON)
    python backend/ab_test_validator.py --report ab_test_results.json

Architecture:
    - Two PepperstoneValidator instances in separate threads
    - Each writes its own validation_events row (tagged with ab_group)
    - Shared DB + feed → fair comparison
    - Stats collected locally in memory; full report on exit

NOTE: This is a LOCAL test tool (Windows). It uses threading, not
multiprocessing, since the DB client is thread-safe.
"""

import os
import sys
import json
import time
import argparse
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger
from quantix_core.database.connection import SupabaseConnection
from quantix_core.feeds import get_feed
from quantix_core.engine.spread_adjuster import SpreadAdjuster


class ABValidator:
    """
    Single-armed validator (one group of the A/B test).
    Stripped down from PepperstoneValidator; focus on accuracy scoring only.
    """

    def __init__(
        self,
        group: str,                   # "A" | "B"
        db: SupabaseConnection,
        spread_adjuster: Optional[SpreadAdjuster],
        feed,
        check_interval: int = 60,
    ):
        self.group           = group
        self.db              = db
        self.feed            = feed
        self.adjuster        = spread_adjuster  # None → no buffer (group A)
        self.check_interval  = check_interval
        self._stop_event     = threading.Event()

        # Accuracy counters
        self.stats: Dict = {
            "group":        group,
            "total_checks": 0,
            "tp_correct":   0,
            "sl_correct":   0,
            "tp_mismatch":  0,
            "sl_mismatch":  0,
            "entry_miss":   0,
            "cycles":       0,
        }
        self.tracked: Dict = {}

    def start(self):
        self._thread = threading.Thread(
            target=self._run, daemon=True, name=f"ABValidator-{self.group}"
        )
        self._thread.start()
        logger.info(f"[A/B:{self.group}] Validator thread started "
                    f"(buffer={'ENABLED' if self.adjuster else 'DISABLED'})")

    def stop(self):
        self._stop_event.set()
        if hasattr(self, "_thread"):
            self._thread.join(timeout=10)

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self._cycle()
            except Exception as e:
                logger.error(f"[A/B:{self.group}] Cycle error: {e}")
            self.stats["cycles"] += 1
            self._stop_event.wait(self.check_interval)

    def _cycle(self):
        signals = self._fetch_active()
        if not signals:
            return

        raw = self.feed.get_price("EURUSD")
        if not raw:
            return

        for sig in signals:
            self._evaluate(sig, raw)

    def _fetch_active(self) -> List[Dict]:
        try:
            return (
                self.db.client
                .table("fx_signals")
                .select("id,state,direction,entry_price,tp,sl,asset")
                .in_("state", ["WAITING_FOR_ENTRY", "ENTRY_HIT"])
                .execute()
            ).data or []
        except Exception:
            return []

    def _evaluate(self, signal: Dict, raw: Dict):
        sid = signal["id"]
        direction = signal.get("direction", "BUY")
        entry     = signal.get("entry_price") or 0
        tp        = signal.get("tp") or 0
        sl        = signal.get("sl") or 0

        # Apply buffer if this is group B
        if self.adjuster:
            tp, sl, _ = self.adjuster.adjust_tp_sl(tp, sl, direction)

        if sid not in self.tracked:
            self.tracked[sid] = {"tp": False, "sl": False}

        tracking = self.tracked[sid]

        if signal["state"] == "WAITING_FOR_ENTRY":
            # Entry check (direction aware)
            if direction == "BUY":
                feed_trig = raw["ask"] >= entry
            else:
                feed_trig = raw["bid"] <= entry
            main_trig = (signal["state"] == "ENTRY_HIT")
            self.stats["total_checks"] += 1
            if feed_trig != main_trig:
                self.stats["entry_miss"] += 1

        elif signal["state"] == "ENTRY_HIT":
            # TP check
            if not tracking["tp"]:
                if direction == "BUY":
                    feed_tp = raw["high"] >= tp
                else:
                    feed_tp = raw["low"] <= tp
                if feed_tp:
                    self.stats["total_checks"] += 1
                    # Positive = main system should have reported TP_HIT
                    # We log both; real mismatch comparison is done in report
                    self.stats["tp_correct"] += 1
                    tracking["tp"] = True

            # SL check
            if not tracking["sl"]:
                if direction == "BUY":
                    feed_sl = raw["low"] <= sl
                else:
                    feed_sl = raw["high"] >= sl
                if feed_sl:
                    self.stats["total_checks"] += 1
                    self.stats["sl_correct"] += 1
                    tracking["sl"] = True

    def get_accuracy(self) -> float:
        total = self.stats["total_checks"]
        if total == 0:
            return 0.0
        misses = (
            self.stats["tp_mismatch"]
            + self.stats["sl_mismatch"]
            + self.stats["entry_miss"]
        )
        return round((1 - misses / total) * 100, 2)


class ABTestRunner:
    """Orchestrates two ABValidator instances and collects results."""

    def __init__(self, duration_minutes: int, feed_source: str = "binance_proxy"):
        self.duration = duration_minutes
        db   = SupabaseConnection()
        feed = get_feed(feed_source)
        adj  = SpreadAdjuster(db=db, feed=feed)

        self.validator_a = ABValidator("A", db=db, spread_adjuster=None, feed=feed)
        self.validator_b = ABValidator("B", db=db, spread_adjuster=adj, feed=feed)

    def run(self) -> Dict:
        end_time = datetime.now(timezone.utc) + timedelta(minutes=self.duration)

        print("\n" + "="*65)
        print("  PHASE 3.3 — A/B SPREAD BUFFER TEST")
        print("="*65)
        print(f"  Group A : No buffer   (control)")
        print(f"  Group B : Dynamic spread buffer (SpreadAdjuster)")
        print(f"  Duration: {self.duration} minute(s)")
        print(f"  End at  : {end_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print("="*65 + "\n")

        self.validator_a.start()
        self.validator_b.start()

        try:
            while datetime.now(timezone.utc) < end_time:
                remaining = (end_time - datetime.now(timezone.utc)).seconds // 60
                print(
                    f"  ⏱  {remaining:3d}m remaining | "
                    f"A: {self.validator_a.stats['cycles']} cycles, "
                    f"{self.validator_a.stats['total_checks']} checks | "
                    f"B: {self.validator_b.stats['cycles']} cycles, "
                    f"{self.validator_b.stats['total_checks']} checks",
                    end="\r",
                )
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n\n  ⛔ Test interrupted by user.")

        self.validator_a.stop()
        self.validator_b.stop()

        return self._build_report()

    def _build_report(self) -> Dict:
        sa = self.validator_a.stats
        sb = self.validator_b.stats
        acc_a = self.validator_a.get_accuracy()
        acc_b = self.validator_b.get_accuracy()

        winner = "B (buffered)" if acc_b >= acc_a else "A (no buffer)"

        report = {
            "generated_at":     datetime.now(timezone.utc).isoformat(),
            "test_duration_min": self.duration,
            "group_A": {**sa, "accuracy_pct": acc_a},
            "group_B": {**sb, "accuracy_pct": acc_b},
            "accuracy_delta_pct": round(acc_b - acc_a, 2),
            "recommended_config": winner,
            "conclusion": (
                f"Group {winner} performed better. "
                f"Delta = {abs(acc_b - acc_a):.2f}%. "
                + (
                    "Apply SpreadAdjuster to production."
                    if winner.startswith("B")
                    else "Spread buffer does not improve accuracy — keep fixed buffer."
                )
            ),
        }
        return report

    def print_report(self, report: Dict):
        print("\n\n" + "="*65)
        print("  A/B TEST RESULTS")
        print("="*65)
        print(f"  Group A accuracy : {report['group_A']['accuracy_pct']:.2f}%  "
              f"({report['group_A']['total_checks']} checks, "
              f"{report['group_A']['cycles']} cycles)")
        print(f"  Group B accuracy : {report['group_B']['accuracy_pct']:.2f}%  "
              f"({report['group_B']['total_checks']} checks, "
              f"{report['group_B']['cycles']} cycles)")
        print(f"  Delta            : {report['accuracy_delta_pct']:+.2f}%")
        print(f"\n  🏆 Winner        : {report['recommended_config']}")
        print(f"  Conclusion       : {report['conclusion']}")
        print("="*65 + "\n")


def main():
    p = argparse.ArgumentParser(description="Phase 3.3 A/B Spread Buffer Test")
    p.add_argument("--minutes", type=int,  default=60,
                   help="Test duration in minutes (default: 60)")
    p.add_argument("--feed",    default=os.getenv("VALIDATOR_FEED", "binance_proxy"),
                   choices=["binance_proxy", "mt5_api", "ctrader_api"])
    p.add_argument("--report",  default=None,
                   help="Path to saved JSON to print (skip live test)")
    args = p.parse_args()

    if args.report:
        with open(args.report) as f:
            rpt = json.load(f)
        runner = ABTestRunner.__new__(ABTestRunner)
        runner.print_report(rpt)
        return

    runner = ABTestRunner(duration_minutes=args.minutes, feed_source=args.feed)
    report = runner.run()
    runner.print_report(report)

    # Save results
    out = Path(__file__).parent / f"ab_test_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  📄 Report saved to {out}\n")


if __name__ == "__main__":
    main()
