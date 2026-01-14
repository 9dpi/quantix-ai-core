"""
Candle Aggregator - Converts lower timeframe candles to higher timeframes
Example: 4x H1 candles → 1x H4 candle
"""

import pandas as pd
from typing import List, Dict


class CandleAggregator:
    """
    Aggregates lower timeframe candles into higher timeframes.
    
    Principle: CORRECT aggregation, not shortcuts.
    - Open = first candle's open
    - High = max of all highs
    - Low = min of all lows
    - Close = last candle's close
    - Volume = sum of all volumes
    """
    
    @staticmethod
    def aggregate(df: pd.DataFrame, factor: int) -> pd.DataFrame:
        """
        Aggregate candles by factor.
        
        Args:
            df: DataFrame with OHLCV data (indexed by timestamp)
            factor: Aggregation factor (e.g., 4 for H1→H4)
            
        Returns:
            Aggregated DataFrame
        """
        if len(df) < factor:
            raise ValueError(f"Insufficient data: need at least {factor} candles for aggregation")
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Resample using proper OHLC aggregation
        aggregated = df.resample(f'{factor}H').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        return aggregated
    
    @staticmethod
    def aggregate_manual(candles: List[Dict], factor: int) -> List[Dict]:
        """
        Manual aggregation for list of candle dicts.
        Used when DataFrame is not available.
        
        Args:
            candles: List of candle dicts with OHLCV
            factor: Aggregation factor
            
        Returns:
            List of aggregated candles
        """
        if len(candles) < factor:
            raise ValueError(f"Insufficient candles: need at least {factor}")
        
        aggregated = []
        
        for i in range(0, len(candles), factor):
            chunk = candles[i:i+factor]
            
            if len(chunk) < factor:
                # Skip incomplete chunks at the end
                break
            
            agg_candle = {
                'timestamp': chunk[0]['timestamp'],
                'open': chunk[0]['open'],
                'high': max(c['high'] for c in chunk),
                'low': min(c['low'] for c in chunk),
                'close': chunk[-1]['close'],
                'volume': sum(c.get('volume', 0) for c in chunk)
            }
            
            aggregated.append(agg_candle)
        
        return aggregated
