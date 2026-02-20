"""
test_feeds.py — Phase 2 Feed Integration Test
==============================================
Verifies that all feed modules load correctly and the
active feed can return well-formed price data.

Usage:
    # Test default (Binance proxy — always works)
    python backend/test_feeds.py

    # Test MT5 (requires running MT5 terminal)
    python backend/test_feeds.py --feed mt5_api

    # Test cTrader connectivity (stub — will raise NotImplementedError)
    python backend/test_feeds.py --feed ctrader_api
"""

import sys
import os
import argparse

# Ensure the backend package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_feed(feed_source: str):
    print(f"\n{'='*60}")
    print(f"  PHASE 2 FEED TEST — {feed_source.upper()}")
    print(f"{'='*60}\n")

    from quantix_core.feeds import get_feed

    # 1. Instantiate feed
    print(f"[1] Loading feed: {feed_source} ...", end=" ")
    try:
        feed = get_feed(feed_source)
        print("OK")
    except Exception as e:
        print(f"FAILED\n    Error: {e}")
        return False

    # 2. Connectivity check
    print(f"[2] Connectivity check ...", end=" ")
    available = feed.is_available()
    print("CONNECTED" if available else "UNREACHABLE")

    if not available:
        print(f"\n    ⚠️  Feed '{feed_source}' is not reachable.")
        if feed_source == "mt5_api":
            print("    → Make sure MetaTrader 5 terminal is running "
                  "and Algo Trading is enabled.")
        elif feed_source == "ctrader_api":
            print("    → cTrader Open API TCP check failed. "
                  "Check internet connection.")
        return False

    # 3. Fetch price
    print(f"[3] Fetching EURUSD price ...", end=" ")
    try:
        data = feed.get_price("EURUSD")
        print("OK")
    except NotImplementedError as e:
        print(f"STUB (not yet implemented)")
        print(f"    {e}")
        return False
    except Exception as e:
        print(f"FAILED\n    Error: {e}")
        return False

    if not data:
        print("    ⚠️  get_price() returned None — feed may be rate-limited.")
        return False

    # 4. Print result
    print()
    print("  ─── Price Data ─────────────────────────────────────")
    for key, val in data.items():
        if isinstance(val, float):
            print(f"    {key:<14}: {val:.5f}")
        else:
            print(f"    {key:<14}: {val}")
    print()

    # 5. Validate required keys
    required = {"timestamp", "open", "high", "low", "close", "bid", "ask",
                "spread_pips", "source"}
    missing = required - set(data.keys())
    if missing:
        print(f"  ⚠️  Missing required keys: {missing}")
        return False

    print(f"  ✅ All required fields present.")
    print(f"  ✅ Real spread from broker: {data['spread_pips']:.2f} pips")
    print(f"\n  RESULT: PHASE 2 FEED '{feed_source}' IS OPERATIONAL\n")
    return True


def main():
    parser = argparse.ArgumentParser(description="Phase 2 Feed Integration Test")
    parser.add_argument(
        "--feed",
        choices=["binance_proxy", "mt5_api", "ctrader_api"],
        default="binance_proxy",
    )
    args = parser.parse_args()
    success = test_feed(args.feed)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
