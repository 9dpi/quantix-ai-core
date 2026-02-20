"""
analyze_spread_impact.py — Phase 3.1 Spread Impact Report
==========================================================
Reads validation_events from Supabase and generates a detailed
spread analysis report. Run this after 2 weeks of data collection
to decide the optimal buffer for Phase 3.2.

Usage:
    python backend/analyze_spread_impact.py
    python backend/analyze_spread_impact.py --days 7 --symbol EURUSD
    python backend/analyze_spread_impact.py --json           # machine-readable
"""

import sys
import os
import argparse
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_section(title: str):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


def run_report(symbol: str, days: int, as_json: bool):
    from quantix_core.database.connection import SupabaseConnection
    from quantix_core.feeds import get_feed
    from quantix_core.engine.spread_adjuster import SpreadAdjuster

    db   = SupabaseConnection()
    feed = get_feed(os.getenv("VALIDATOR_FEED", "binance_proxy"))
    adj  = SpreadAdjuster(db=db, feed=feed)

    # Run full analysis
    report = adj.analyze(symbol=symbol, lookback_days=days)

    if as_json:
        print(json.dumps(report, indent=2))
        return

    # ── Pretty print ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PEPPERSTONE VALIDATION — SPREAD IMPACT ANALYSIS")
    print("=" * 60)
    print(f"  Symbol       : {report['symbol']}")
    print(f"  Lookback     : {report['lookback_days']} days")
    print(f"  Generated    : {report['generated_at']}")
    print(f"  Data source  : {report['data_source']}")

    if report.get("error"):
        print(f"\n  ❌ ERROR: {report['error']}")
        return

    if report.get("warning"):
        print(f"\n  ⚠️  {report['warning']}")

    print_section("Validation Summary")
    print(f"  Total checks       : {report.get('total_validations', 0)}")
    print(f"  Discrepancies      : {report.get('discrepancy_count', 0)}")
    print(f"  Discrepancy rate   : {report.get('discrepancy_rate_pct', 0.0):.2f}%")
    print(f"  TP mismatches      : {report.get('tp_mismatches', 0)}")
    print(f"  SL mismatches      : {report.get('sl_mismatches', 0)}")

    if report.get("avg_spread_pips"):
        print_section("Spread Statistics")
        print(f"  Average spread     : {report['avg_spread_pips']:.3f} pips")
        print(f"  Max spread         : {report['max_spread_pips']:.3f} pips")
        print(f"  Min spread         : {report['min_spread_pips']:.3f} pips")
        print(f"  95th pct spread    : {report['p95_spread_pips']:.3f} pips")
    elif report.get("note"):
        print_section("Spread Statistics")
        print(f"  {report['note']}")

    print_section("Recommended Buffer")
    print(f"  Buffer (pips)      : {report.get('recommended_buffer_pips', 'n/a')} pips")
    print(f"  Buffer (price)     : {report.get('recommended_buffer_price', 'n/a')}")

    print_section("Recommendation")
    print(f"  {report.get('recommendation', 'No recommendation available.')}")

    # Live buffer right now
    print_section("Live Buffer (Current Moment)")
    buf = adj.get_buffer(symbol)
    print(f"  Spread now         : {buf['spread_pips']:.3f} pips  [{buf['source']}]")
    print(f"  Session            : {buf['session']}  (×{buf['multiplier']})")
    print(f"  Buffer applied     : {buf['buffer_pips']:.3f} pips → {buf['buffer_price']} price units")

    # Example adjustment
    print_section("Example TP/SL Adjustment")
    test_tp, test_sl = 1.08500, 1.08200
    adj_tp, adj_sl, b = adj.adjust_tp_sl(test_tp, test_sl, "BUY", symbol)
    print(f"  Original  TP={test_tp:.5f}  SL={test_sl:.5f}  (BUY)")
    print(f"  Adjusted  TP={adj_tp:.5f}  SL={adj_sl:.5f}  (buffer={b['buffer_price']})")

    print("\n" + "=" * 60 + "\n")


def main():
    p = argparse.ArgumentParser(description="Phase 3.1 Spread Impact Report")
    p.add_argument("--symbol", default="EURUSD", help="Trading pair (default EURUSD)")
    p.add_argument("--days",   type=int, default=14, help="Lookback window in days")
    p.add_argument("--json",   action="store_true",  help="Output raw JSON")
    args = p.parse_args()

    run_report(symbol=args.symbol, days=args.days, as_json=args.json)


if __name__ == "__main__":
    main()
