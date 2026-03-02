
import pandas as pd
import sys
import os
from datetime import datetime, timezone
from loguru import logger

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)

from quantix_core.engine.continuous_analyzer import ContinuousAnalyzer
from quantix_core.engine.confidence_refiner import ConfidenceRefiner
from quantix_core.config.settings import settings

def debug_analyzer_v36():
    analyzer = ContinuousAnalyzer()
    refiner = ConfidenceRefiner()
    
    print(f"--- Quantix v3.6 - Market Intelligence Debug ---")
    print(f"Current UTC: {datetime.now(timezone.utc)}")
    print(f"Threshold (MIN_CONFIDENCE): {settings.MIN_CONFIDENCE}")
    
    # 1. Fetch Data
    print("\n[1] Fetching Market Data...")
    try:
        raw_data = analyzer.td_client.get_time_series(symbol="EUR/USD", interval="15min", outputsize=100)
        df = analyzer.convert_to_df(raw_data)
        if df.empty:
            print("❌ Initial data fetch failed. Trying fallback...")
            raw_data = analyzer.binance.get_history(symbol="EURUSD", interval="15m", limit=100)
            df = analyzer.convert_to_df(raw_data)
    except Exception as e:
        print(f"❌ Data fetch error: {e}")
        return

    if df.empty:
        print("❌ CRITICAL: Market data is empty after both sources.")
        return

    price = float(df.iloc[-1]['close'])
    print(f"✅ Market Data Ready: EURUSD @ {price:.5f}")

    # 2. Structure Analysis
    print("\n[2] Performing Context Analysis...")
    state = analyzer.engine.analyze(df, symbol="EURUSD", timeframe="M15")
    print(f"   Structure State: {state.state}")
    print(f"   Raw Confidence: {state.confidence:.2f}")
    print(f"   Strength: {state.strength:.2f}")
    
    # Check direction mapping
    direction_map = {"bullish": "BUY", "bearish": "SELL"}
    direction = direction_map.get(state.state)
    if direction is None:
        print(f"⏸️ Analysis says Market is '{state.state}' (neutral/ranging). Blocking signal.")
    else:
        print(f"✅ Potential Direction: {direction}")

    # 3. Confidence Gating
    print("\n[3] Calculating Confidence Gating Factors...")
    now = datetime.now(timezone.utc)
    s_weight = refiner.get_session_weight(now)
    v_factor = refiner.get_volatility_factor(df)
    sp_factor = refiner.get_spread_factor("EURUSD")
    
    release_score = state.confidence * s_weight * v_factor * sp_factor
    print(f"   - Session Weight: {s_weight:.2f}")
    print(f"   - Volatility Factor: {v_factor:.2f}")
    print(f"   - Spread Factor: {sp_factor:.2f}")
    print(f"   - Final Release Score: {release_score:.4f}")
    
    if release_score >= settings.MIN_CONFIDENCE:
        print(f"🚀 THRESHOLD PASSED! Signal should be released.")
    else:
        print(f"🚫 THRESHOLD BLOCKED. Needs {settings.MIN_CONFIDENCE} but got {release_score:.4f}")

    # 4. Release Gate Check (Anti-Burst)
    if release_score >= settings.MIN_CONFIDENCE:
        print("\n[4] Performing Release Gate Check (Anti-Burst)...")
        is_allowed, gate_reason = analyzer.check_release_gate("EURUSD", "M15")
        if is_allowed:
            print(f"✅ GATES OPEN. System is clear to fire.")
        else:
            print(f"❌ GATES CLOSED. Reason: {gate_reason}")

if __name__ == "__main__":
    debug_analyzer_v36()
