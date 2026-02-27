"""
Unit Tests for Liquidity Filter — Quantix SMC-Lite M15
=====================================================
Verifies stop-hunt detection logic with deterministic test data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from quantix_core.engine.primitives.liquidity_filter import LiquidityFilter
from quantix_core.engine.primitives.swing_detector import SwingPoint

def test_bearish_sweep():
    """
    Bearish Sweep: Price goes above swing high but closes below.
    """
    # Swing High at 1.1020 at index 2
    swings = [SwingPoint(index=2, price=1.1020, type="HIGH", strength=3)]
    
    # Current candles at index 9, 10
    data = {
        'open':  [1.1010, 1.1015],
        'high':  [1.1025, 1.1025], # Pierced 1.1020
        'low':   [1.1008, 1.1008],
        'close': [1.1018, 1.1018]  # Closed below 1.1020
    }
    # Create 11 rows to make index 10 valid and far from swing 2
    indices = list(range(11))
    full_data = {
        'open':  [1.1000] * 11,
        'high':  [1.1000] * 11,
        'low':   [1.1000] * 11,
        'close': [1.1000] * 11
    }
    df = pd.DataFrame(full_data, index=indices)
    df.loc[10, 'open'] = 1.1015
    df.loc[10, 'high'] = 1.1025
    df.loc[10, 'low'] = 1.1008
    df.loc[10, 'close'] = 1.1018
    
    filter_svc = LiquidityFilter()
    sweeps = filter_svc.detect_sweeps(df, swings)
    
    assert len(sweeps) == 1
    assert sweeps[0].type == "BEARISH_SWEEP"
    assert sweeps[0].swept_level == 1.1020
    assert sweeps[0].wick_size_pips > 0
    
    print("✅ test_bearish_sweep PASSED")

def test_bullish_sweep():
    """
    Bullish Sweep: Price goes below swing low but closes above.
    """
    # Swing Low at 1.1000 at index 2
    swings = [SwingPoint(index=2, price=1.1000, type="LOW", strength=3)]
    
    # Create 11 rows
    indices = list(range(11))
    full_data = {
        'open':  [1.1010] * 11,
        'high':  [1.1020] * 11,
        'low':   [1.1010] * 11,
        'close': [1.1015] * 11
    }
    df = pd.DataFrame(full_data, index=indices)
    df.loc[10, 'open'] = 1.1005
    df.loc[10, 'high'] = 1.1015
    df.loc[10, 'low'] = 1.0995  # Pierced 1.1000
    df.loc[10, 'close'] = 1.1002 # Closed above 1.1000
    
    filter_svc = LiquidityFilter()
    sweeps = filter_svc.detect_sweeps(df, swings)
    
    assert len(sweeps) == 1
    assert sweeps[0].type == "BULLISH_SWEEP"
    assert sweeps[0].swept_level == 1.1000
    
    print("✅ test_bullish_sweep PASSED")

def test_no_sweep_on_clean_break():
    """
    A full body close above a swing high is a BOS, NOT a sweep.
    """
    # Swing High at 1.1020 at index 2
    swings = [SwingPoint(index=2, price=1.1020, type="HIGH", strength=3)]
    
    # Create 11 rows
    indices = list(range(11))
    full_data = {
        'open':  [1.1010] * 11,
        'high':  [1.1020] * 11,
        'low':   [1.1010] * 11,
        'close': [1.1015] * 11
    }
    df = pd.DataFrame(full_data, index=indices)
    df.loc[10, 'open'] = 1.1021
    df.loc[10, 'high'] = 1.1030
    df.loc[10, 'low'] = 1.1020
    df.loc[10, 'close'] = 1.1028 # Closed ABOVE 1.1020
    
    filter_svc = LiquidityFilter()
    sweeps = filter_svc.detect_sweeps(df, swings)
    
    assert len(sweeps) == 0
    print("✅ test_no_sweep_on_clean_break PASSED")

if __name__ == "__main__":
    test_bearish_sweep()
    test_bullish_sweep()
    test_no_sweep_on_clean_break()
    print("🎉 ALL LIQUIDITY FILTER TESTS PASSED")
