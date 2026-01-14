"""
Quantix AI Core - Feature State Calculator v1
Converts raw OHLCV data into interpretable market states

This is NOT indicator calculation - this is STATE REASONING.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timezone

from schemas.feature_state import (
    MarketStateSnapshot,
    TrendState, TrendFeature,
    MomentumState, MomentumFeature,
    VolatilityState, VolatilityFeature,
    StructureState, StructureFeature
)


class FeatureStateCalculator:
    """
    Calculates market feature states from OHLCV data.
    
    Philosophy:
    - States are INTERPRETATIONS, not raw numbers
    - Confidence reflects clarity of the state
    - No magic numbers - all thresholds are explainable
    """
    
    def __init__(self):
        # Configurable thresholds (explainable, not magic)
        self.trend_ema_fast = 20
        self.trend_ema_slow = 50
        self.momentum_lookback = 14
        self.volatility_atr_period = 14
        self.structure_swing_threshold = 0.002  # 0.2% for structure breaks
    
    def calculate_state(
        self, 
        df: pd.DataFrame, 
        symbol: str, 
        timeframe: str
    ) -> MarketStateSnapshot:
        """
        Calculate complete market state from OHLCV dataframe.
        
        Args:
            df: DataFrame with OHLC data (must have: open, high, low, close)
            symbol: Asset symbol
            timeframe: Timeframe identifier
            
        Returns:
            MarketStateSnapshot with all feature states
        """
        
        # Ensure we have enough data
        if len(df) < max(self.trend_ema_slow, self.momentum_lookback, self.volatility_atr_period):
            raise ValueError(f"Insufficient data: need at least {self.trend_ema_slow} candles")
        
        # Calculate each feature state
        trend = self._calculate_trend_state(df)
        momentum = self._calculate_momentum_state(df)
        volatility = self._calculate_volatility_state(df)
        structure = self._calculate_structure_state(df)
        
        # Data quality assessment
        data_quality = self._assess_data_quality(df)
        
        return MarketStateSnapshot(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.now(timezone.utc).isoformat(),
            trend=trend,
            momentum=momentum,
            volatility=volatility,
            structure=structure,
            data_quality=data_quality
        )
    
    def _calculate_trend_state(self, df: pd.DataFrame) -> TrendFeature:
        """
        Determine trend state using EMA crossover + price position.
        
        Logic:
        - BULLISH: Fast EMA > Slow EMA AND price > both EMAs
        - BEARISH: Fast EMA < Slow EMA AND price < both EMAs
        - RANGE: Mixed signals
        
        Confidence: Based on EMA separation and price distance
        """
        close = df['close'].values
        
        # Calculate EMAs
        ema_fast = pd.Series(close).ewm(span=self.trend_ema_fast, adjust=False).mean()
        ema_slow = pd.Series(close).ewm(span=self.trend_ema_slow, adjust=False).mean()
        
        current_price = close[-1]
        current_ema_fast = ema_fast.iloc[-1]
        current_ema_slow = ema_slow.iloc[-1]
        
        # Determine state
        if current_ema_fast > current_ema_slow and current_price > current_ema_fast:
            state = TrendState.BULLISH
            # Confidence based on EMA separation
            separation = (current_ema_fast - current_ema_slow) / current_ema_slow
            confidence = min(1.0, separation * 100)  # Normalize
        elif current_ema_fast < current_ema_slow and current_price < current_ema_fast:
            state = TrendState.BEARISH
            separation = (current_ema_slow - current_ema_fast) / current_ema_slow
            confidence = min(1.0, separation * 100)
        else:
            state = TrendState.RANGE
            # Low confidence in range
            confidence = 0.5
        
        return TrendFeature(state=state, confidence=confidence)
    
    def _calculate_momentum_state(self, df: pd.DataFrame) -> MomentumFeature:
        """
        Determine momentum state using ROC (Rate of Change).
        
        Logic:
        - EXPANDING: ROC increasing over lookback period
        - WEAKENING: ROC decreasing over lookback period
        - NEUTRAL: Flat ROC
        
        Confidence: Based on consistency of ROC direction
        """
        close = df['close'].values
        
        # Calculate Rate of Change
        roc = pd.Series(close).pct_change(self.momentum_lookback) * 100
        
        # Look at recent ROC trend
        recent_roc = roc.tail(5).values
        
        # Determine if ROC is increasing or decreasing
        roc_slope = np.polyfit(range(len(recent_roc)), recent_roc, 1)[0]
        
        if roc_slope > 0.1:
            state = MomentumState.EXPANDING
            confidence = min(1.0, abs(roc_slope) * 10)
        elif roc_slope < -0.1:
            state = MomentumState.WEAKENING
            confidence = min(1.0, abs(roc_slope) * 10)
        else:
            state = MomentumState.NEUTRAL
            confidence = 0.6
        
        return MomentumFeature(state=state, confidence=confidence)
    
    def _calculate_volatility_state(self, df: pd.DataFrame) -> VolatilityFeature:
        """
        Determine volatility state using ATR (Average True Range).
        
        Logic:
        - EXPANDING: ATR increasing
        - CONTRACTING: ATR decreasing
        - ABNORMAL: ATR spike (> 2x average)
        
        Confidence: Based on ATR consistency
        """
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        # Calculate True Range
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        
        # Calculate ATR
        atr = pd.Series(tr).rolling(window=self.volatility_atr_period).mean()
        
        current_atr = atr.iloc[-1]
        avg_atr = atr.tail(20).mean()
        
        # Check for abnormal spike
        if current_atr > avg_atr * 2:
            state = VolatilityState.ABNORMAL
            confidence = 0.9
        else:
            # Check if ATR is expanding or contracting
            atr_slope = (atr.iloc[-1] - atr.iloc[-5]) / atr.iloc[-5]
            
            if atr_slope > 0.1:
                state = VolatilityState.EXPANDING
                confidence = min(1.0, abs(atr_slope) * 5)
            elif atr_slope < -0.1:
                state = VolatilityState.CONTRACTING
                confidence = min(1.0, abs(atr_slope) * 5)
            else:
                state = VolatilityState.CONTRACTING  # Default to contracting
                confidence = 0.5
        
        return VolatilityFeature(state=state, confidence=confidence)
    
    def _calculate_structure_state(self, df: pd.DataFrame) -> StructureFeature:
        """
        Determine market structure state using swing highs/lows.
        
        Logic:
        - BREAKOUT: Price breaks recent swing high/low cleanly
        - FAKEOUT: Price breaks but immediately reverses
        - INTACT: Structure holding
        
        Confidence: Based on break magnitude and follow-through
        """
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        # Find recent swing high and low (last 20 candles)
        recent_high = np.max(high[-20:])
        recent_low = np.min(low[-20:])
        current_close = close[-1]
        
        # Check for breakout
        break_threshold = self.structure_swing_threshold
        
        if current_close > recent_high * (1 + break_threshold):
            # Bullish breakout
            # Check for follow-through (not immediate reversal)
            if close[-2] > recent_high:
                state = StructureState.BREAKOUT
                confidence = 0.85
            else:
                state = StructureState.FAKEOUT
                confidence = 0.7
        elif current_close < recent_low * (1 - break_threshold):
            # Bearish breakout
            if close[-2] < recent_low:
                state = StructureState.BREAKOUT
                confidence = 0.85
            else:
                state = StructureState.FAKEOUT
                confidence = 0.7
        else:
            # Structure intact
            state = StructureState.INTACT
            confidence = 0.8
        
        return StructureFeature(state=state, confidence=confidence)
    
    def _assess_data_quality(self, df: pd.DataFrame) -> float:
        """
        Assess quality of input data.
        
        Factors:
        - Missing values
        - Data consistency
        - Outliers
        
        Returns: Quality score 0.0 to 1.0
        """
        quality = 1.0
        
        # Check for missing values
        missing_ratio = df[['open', 'high', 'low', 'close']].isna().sum().sum() / (len(df) * 4)
        quality -= missing_ratio * 0.5
        
        # Check for zero/negative prices (data error)
        invalid_prices = ((df['close'] <= 0) | (df['high'] <= 0)).sum()
        if invalid_prices > 0:
            quality -= 0.3
        
        # Check for extreme outliers (>5% single candle move - suspicious)
        returns = df['close'].pct_change().abs()
        extreme_moves = (returns > 0.05).sum()
        if extreme_moves > len(df) * 0.01:  # More than 1% of candles
            quality -= 0.2
        
        return max(0.0, min(1.0, quality))
