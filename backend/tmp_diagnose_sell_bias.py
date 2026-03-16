import pandas as pd
import numpy as np
from quantix_core.engine.structure_engine_v1 import StructureEngineV1
from quantix_core.engine.primitives.state_resolver import StructureState

# 1. Create a synthetic BEARISH (SELL) setup
# Price drop + Consolidation + Bearish FVG
dates = pd.date_range("2026-03-01", periods=100, freq="15min")
close = 1.2000 - (np.arange(100) * 0.0001) # Down trend
close[-10:] = 1.1900 + (np.random.randn(10) * 0.00005) # Consolidation

# Create Bearish FVG pattern: Candle n-2 High < Candle n Low
# Let's force it at index 90
# Candle 89: 1.1910 - 1.1915
# Candle 90: 1.1915 - 1.1900 (Big drop)
# Candle 91: 1.1900 - 1.1895
# Gap is between 89 low and 91 high. Wait, bearish FVG is Gap between High(n) and Low(n-2)? 
# Actually FVG Bearish: Low(n-2) < High(n). No, it's Low(n-2) > High(n).

data = {
    "datetime": dates,
    "open": close + 0.0001,
    "high": close + 0.0002,
    "low": close - 0.0002,
    "close": close
}
df = pd.DataFrame(data)

# Force a clear Bearish FVG
df.iloc[89, df.columns.get_loc('low')] = 1.1950  # High pivot (Low of n-2)
df.iloc[90, df.columns.get_loc('open')] = 1.1945
df.iloc[90, df.columns.get_loc('high')] = 1.1945
df.iloc[90, df.columns.get_loc('low')] = 1.1910
df.iloc[90, df.columns.get_loc('close')] = 1.1915
df.iloc[91, df.columns.get_loc('high')] = 1.1915 # Low pivot (High of n)

engine = StructureEngineV1(sensitivity=2)
result = engine.analyze(df, symbol="EURUSD", timeframe="M15")

print(f"DIRETION: SELL simulation")
print(f"STATE: {result.state}")
print(f"CONFIDENCE: {result.confidence}")
print(f"BULLISH SCORE: {result.dominance['bullish']}")
print(f"BEARISH SCORE: {result.dominance['bearish']}")
for e in result.evidence:
    print(f"EVIDENCE: {e}")
