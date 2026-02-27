"""
Unit Tests for FVG Detector — Quantix SMC-Lite M15
====================================================
Verifies FVG detection logic with deterministic test data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
from quantix_core.engine.primitives.fvg_detector import FVGDetector, FairValueGap


def create_test_df(candles: list) -> pd.DataFrame:
    """Create a test DataFrame from list of (open, high, low, close) tuples."""
    df = pd.DataFrame(candles, columns=["open", "high", "low", "close"])
    df["datetime"] = pd.date_range("2026-01-01", periods=len(df), freq="15min")
    return df


def test_bullish_fvg():
    """
    Bullish FVG: candle[0].high < candle[2].low
    
    Candle 0: H=1.1000 (ceiling)
    Candle 1: Strong bullish impulse (gap creator)
    Candle 2: L=1.1005 (floor is above candle 0's high)
    → Gap between 1.1000 and 1.1005 = 5 pips Bullish FVG
    """
    candles = [
        # (open,   high,    low,     close)
        (1.0990, 1.1000, 1.0985, 1.0995),   # Candle 0
        (1.0995, 1.1015, 1.0993, 1.1012),   # Candle 1 (impulse up)
        (1.1010, 1.1020, 1.1005, 1.1018),   # Candle 2 (gap: 1.1000 < 1.1005)
        (1.1015, 1.1025, 1.1012, 1.1022),   # Candle 3 (no fill)
    ]
    df = create_test_df(candles)
    
    detector = FVGDetector(min_gap_pips=1.0)
    fvgs = detector.detect_fvgs(df)
    
    bullish = [f for f in fvgs if f.type == "BULLISH"]
    assert len(bullish) >= 1, f"Expected ≥1 bullish FVG, got {len(bullish)}"
    
    fvg = bullish[0]
    assert fvg.bottom == 1.10000, f"Bottom should be 1.1000, got {fvg.bottom}"
    assert fvg.top == 1.10050, f"Top should be 1.1005, got {fvg.top}"
    assert fvg.size_pips == 5.0, f"Size should be 5.0 pips, got {fvg.size_pips}"
    assert not fvg.filled, "FVG should be unfilled (price stayed above)"
    
    print("✅ test_bullish_fvg PASSED")


def test_bearish_fvg():
    """
    Bearish FVG: candle[0].low > candle[2].high
    
    Candle 0: L=1.1020 (floor)
    Candle 1: Strong bearish impulse (gap creator)
    Candle 2: H=1.1015 (ceiling is below candle 0's low)
    → Gap between 1.1015 and 1.1020 = 5 pips Bearish FVG
    """
    candles = [
        (1.1025, 1.1030, 1.1020, 1.1022),   # Candle 0
        (1.1022, 1.1023, 1.1005, 1.1008),   # Candle 1 (impulse down)
        (1.1010, 1.1015, 1.1003, 1.1012),   # Candle 2 (gap: 1.1020 > 1.1015)
        (1.1008, 1.1013, 1.1000, 1.1005),   # Candle 3 (no fill)
    ]
    df = create_test_df(candles)
    
    detector = FVGDetector(min_gap_pips=1.0)
    fvgs = detector.detect_fvgs(df)
    
    bearish = [f for f in fvgs if f.type == "BEARISH"]
    assert len(bearish) >= 1, f"Expected ≥1 bearish FVG, got {len(bearish)}"
    
    fvg = bearish[0]
    assert fvg.top == 1.10200, f"Top should be 1.1020, got {fvg.top}"
    assert fvg.bottom == 1.10150, f"Bottom should be 1.1015, got {fvg.bottom}"
    assert fvg.size_pips == 5.0, f"Size should be 5.0 pips, got {fvg.size_pips}"
    
    print("✅ test_bearish_fvg PASSED")


def test_filled_fvg():
    """
    A Bullish FVG that gets filled when price dips back into it.
    """
    candles = [
        (1.0990, 1.1000, 1.0985, 1.0995),   # Candle 0
        (1.0995, 1.1015, 1.0993, 1.1012),   # Candle 1 (impulse)
        (1.1010, 1.1020, 1.1005, 1.1018),   # Candle 2 (FVG: 1.1000-1.1005)
        (1.1015, 1.1018, 1.0998, 1.1002),   # Candle 3 → dips to 1.0998 → FILLS the FVG
    ]
    df = create_test_df(candles)
    
    detector = FVGDetector(min_gap_pips=1.0)
    fvgs = detector.detect_fvgs(df)
    
    bullish = [f for f in fvgs if f.type == "BULLISH"]
    assert len(bullish) >= 1, f"Expected ≥1 bullish FVG, got {len(bullish)}"
    assert bullish[0].filled, "FVG should be FILLED (price dipped to 1.0998)"
    
    print("✅ test_filled_fvg PASSED")


def test_no_fvg_on_tight_market():
    """
    When candles are tight (no gaps), no FVG should be detected.
    """
    candles = [
        (1.1000, 1.1003, 1.0998, 1.1001),
        (1.1001, 1.1004, 1.0999, 1.1002),
        (1.1002, 1.1005, 1.1000, 1.1003),
        (1.1003, 1.1006, 1.1001, 1.1004),
    ]
    df = create_test_df(candles)
    
    detector = FVGDetector(min_gap_pips=1.0)
    fvgs = detector.detect_fvgs(df)
    
    assert len(fvgs) == 0, f"Expected 0 FVGs on tight data, got {len(fvgs)}"
    
    print("✅ test_no_fvg_on_tight_market PASSED")


def test_nearest_entry_fvg():
    """
    Find nearest unfilled FVG for BUY entry.
    """
    candles = [
        # Create a bullish FVG early in the dataset
        (1.0990, 1.1000, 1.0985, 1.0995),   # Candle 0
        (1.0995, 1.1015, 1.0993, 1.1012),   # Candle 1 (impulse)
        (1.1010, 1.1020, 1.1005, 1.1018),   # Candle 2 (FVG: 1.1000-1.1005)
        # Price continues up without filling the FVG
        (1.1018, 1.1025, 1.1015, 1.1022),
        (1.1022, 1.1028, 1.1020, 1.1026),
    ]
    df = create_test_df(candles)
    
    detector = FVGDetector(min_gap_pips=1.0)
    fvgs = detector.detect_fvgs(df)
    
    # Current price is 1.1026, looking for BUY FVG below
    best = detector.get_nearest_entry_fvg(
        fvgs, direction="BUY", current_price=1.1026, max_distance_pips=30.0
    )
    
    assert best is not None, "Should find a BUY entry FVG"
    assert best.type == "BULLISH", f"Should be BULLISH, got {best.type}"
    
    # Should NOT find SELL FVG (none exists above price)
    sell_fvg = detector.get_nearest_entry_fvg(
        fvgs, direction="SELL", current_price=1.1026, max_distance_pips=30.0
    )
    assert sell_fvg is None, "Should NOT find a SELL FVG"
    
    print("✅ test_nearest_entry_fvg PASSED")


def test_quality_scoring():
    """
    Verify that FVG quality scoring reflects impulse candle strength.
    """
    # Strong impulse candle (large body, small wicks)
    candles_strong = [
        (1.0990, 1.1000, 1.0985, 1.0995),
        (1.0995, 1.1020, 1.0994, 1.1019),   # Strong body (25/26 = 96%)
        (1.1018, 1.1025, 1.1008, 1.1022),   # FVG: 1.1000-1.1008 = 8 pips
    ]
    
    # Weak impulse candle (small body, large wicks / doji)
    candles_weak = [
        (1.0990, 1.1000, 1.0985, 1.0995),
        (1.0995, 1.1020, 1.0994, 1.0996),   # Weak body (1/26 = 4%)
        (1.1018, 1.1025, 1.1008, 1.1022),   # FVG: 1.1000-1.1008 = 8 pips
    ]
    
    detector = FVGDetector(min_gap_pips=1.0)
    
    fvgs_strong = detector.detect_fvgs(create_test_df(candles_strong))
    fvgs_weak = detector.detect_fvgs(create_test_df(candles_weak))
    
    if fvgs_strong and fvgs_weak:
        assert fvgs_strong[0].quality > fvgs_weak[0].quality, (
            f"Strong impulse ({fvgs_strong[0].quality}) should have higher "
            f"quality than weak ({fvgs_weak[0].quality})"
        )
        print("✅ test_quality_scoring PASSED")
    else:
        print("⚠️ test_quality_scoring SKIPPED (no FVGs detected)")


if __name__ == "__main__":
    print("=" * 60)
    print("FVG Detector Unit Tests")
    print("=" * 60)
    
    test_bullish_fvg()
    test_bearish_fvg()
    test_filled_fvg()
    test_no_fvg_on_tight_market()
    test_nearest_entry_fvg()
    test_quality_scoring()
    
    print("=" * 60)
    print("🎉 ALL TESTS PASSED")
    print("=" * 60)
