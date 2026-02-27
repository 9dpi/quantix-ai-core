"""
Unit Test for ConfidenceRefiner (ATR Logic)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
from quantix_core.engine.confidence_refiner import ConfidenceRefiner

def create_mock_df(count=30, volatility=0.0010):
    """Create a mock dataframe with specific volatility."""
    base_price = 1.1000
    data = []
    for i in range(count):
        # Create a candle with 10 pips range
        data.append({
            'open': base_price,
            'high': base_price + volatility,
            'low': base_price,
            'close': base_price + volatility/2
        })
    return pd.DataFrame(data)

def test_volatility_factor():
    refiner = ConfidenceRefiner()
    
    # 1. Normal Volatility (current candle matches average)
    df_normal = create_mock_df()
    factor_normal = refiner.get_volatility_factor(df_normal)
    print(f"Normal Factor: {factor_normal}")
    assert factor_normal == 1.0
    
    # 2. Extreme Volatility (current candle is 5x ATR)
    df_high = create_mock_df()
    df_high.loc[29, 'high'] = df_high.loc[29, 'low'] + 0.0050 # 50 pips spike (vs 10 pips avg)
    factor_high = refiner.get_volatility_factor(df_high)
    print(f"High Vol Factor: {factor_high}")
    assert factor_high < 1.0 # Should be penalized (e.g., 0.6)
    
    # 3. Minimum Volatility (current candle is 0.1x ATR)
    df_low = create_mock_df()
    df_low.loc[29, 'high'] = df_low.loc[29, 'low'] + 0.0001 # 1 pip range (vs 10 pips avg)
    factor_low = refiner.get_volatility_factor(df_low)
    print(f"Low Vol Factor: {factor_low}")
    assert factor_low < 1.0 # Should be penalized (e.g., 0.7)

if __name__ == "__main__":
    try:
        test_volatility_factor()
        print("🎉 ConfidenceRefiner (ATR) Test PASSED")
    except Exception as e:
        print(f"❌ Test Failed: {e}")
