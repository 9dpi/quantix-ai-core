
import pandas as pd
from quantix_core.feeds.binance_feed import BinanceFeed
from loguru import logger

def check_volatility():
    fb = BinanceFeed()
    raw = fb.get_history(symbol="EURUSD", interval="15m", limit=30)
    if not raw:
        print("Failed to fetch data")
        return
        
    df = pd.DataFrame(raw)
    df["datetime"] = pd.to_datetime(df["datetime"])
    
    # Calculate ATR(14)
    high = df['high'].astype(float)
    low = df['low'].astype(float)
    close = df['close'].astype(float)
    
    tr = pd.concat([
        high - low, 
        (high - close.shift()).abs(), 
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    
    atr = tr.rolling(window=14).mean().iloc[-1]
    current_range = float(high.iloc[-1] - low.iloc[-1])
    
    ratio = current_range / atr
    print(f"--- Volatility Analysis ---")
    print(f"ATR(14): {atr:.5f}")
    print(f"Current Candle Range: {current_range:.5f}")
    print(f"Volatility Ratio: {ratio:.2f}x")
    
    if ratio > 2.5:
        print("⚠️ VOLATILITY SPIKE DETECTED (> 2.5x ATR)")
        print("Security Penalty: 0.6x multiplier applied.")
    else:
        print("✅ Volatility within safe limits.")

if __name__ == "__main__":
    check_volatility()
