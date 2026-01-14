"""
Quantix AI Core - Structure State Primitive
THE MOST IMPORTANT FEATURE - Foundation of all decisions

Structure = Market's acceptance/rejection of price levels
"""

import pandas as pd
import numpy as np
from typing import List, Tuple

from quantix_core.schemas.feature_state import PrimitiveSignal, StructureFeatureState


class StructurePrimitive:
    """
    Calculates market structure state using swing analysis.
    
    Philosophy:
    - Structure is about ACCEPTANCE vs REJECTION
    - Close matters more than wicks
    - Follow-through confirms validity
    """
    
    def __init__(self):
        # Configurable thresholds (explainable)
        self.swing_lookback = 20  # Candles to look back for swings
        self.break_threshold = 0.002  # 0.2% for clean break
        self.followthrough_candles = 2  # Candles needed for confirmation
    
    def calculate(self, df: pd.DataFrame) -> StructureFeatureState:
        """
        Calculate structure state from OHLCV data.
        
        Returns:
            StructureFeatureState with state, confidence, and evidence
        """
        
        # Calculate primitive signals
        swing_break = self._detect_swing_break(df)
        acceptance = self._check_acceptance(df)
        fakeout = self._detect_fakeout(df)
        
        # Aggregate signals into state
        state, confidence, evidence = self._aggregate_structure_state(
            swing_break, acceptance, fakeout
        )
        
        return StructureFeatureState(
            state=state,
            confidence=confidence,
            evidence=evidence
        )
    
    def _detect_swing_break(self, df: pd.DataFrame) -> PrimitiveSignal:
        """
        Detect if price has broken recent swing high/low.
        
        Returns:
            PrimitiveSignal with value:
            +1.0 = bullish break
            -1.0 = bearish break
             0.0 = no break
        """
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        # Find swing high and low
        recent_high = np.max(high[-self.swing_lookback:-1])  # Exclude current candle
        recent_low = np.min(low[-self.swing_lookback:-1])
        
        current_close = close[-1]
        
        # Check for break
        if current_close > recent_high * (1 + self.break_threshold):
            value = 1.0
            evidence = f"Close above swing high ({recent_high:.5f})"
        elif current_close < recent_low * (1 - self.break_threshold):
            value = -1.0
            evidence = f"Close below swing low ({recent_low:.5f})"
        else:
            value = 0.0
            evidence = f"Price within range [{recent_low:.5f}, {recent_high:.5f}]"
        
        return PrimitiveSignal(
            name="swing_break",
            value=value,
            weight=1.0,
            evidence=evidence
        )
    
    def _check_acceptance(self, df: pd.DataFrame) -> PrimitiveSignal:
        """
        Check if price is ACCEPTED (close) vs REJECTED (wick) at levels.
        
        Close acceptance = strong signal
        Wick rejection = weak signal
        
        Returns:
            PrimitiveSignal with value 0.0 to 1.0 (acceptance strength)
        """
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        open_price = df['open'].values
        
        # Last candle analysis
        candle_range = high[-1] - low[-1]
        if candle_range == 0:
            return PrimitiveSignal(
                name="acceptance",
                value=0.5,
                weight=0.8,
                evidence="Doji candle - neutral acceptance"
            )
        
        # Calculate body vs wick ratio
        body = abs(close[-1] - open_price[-1])
        upper_wick = high[-1] - max(close[-1], open_price[-1])
        lower_wick = min(close[-1], open_price[-1]) - low[-1]
        
        body_ratio = body / candle_range
        
        # Strong body = acceptance, long wicks = rejection
        if body_ratio > 0.6:
            value = 0.9
            evidence = f"Strong body ({body_ratio:.1%}) - price accepted"
        elif body_ratio > 0.4:
            value = 0.6
            evidence = f"Moderate body ({body_ratio:.1%})"
        else:
            value = 0.3
            evidence = f"Weak body ({body_ratio:.1%}) - rejection likely"
        
        return PrimitiveSignal(
            name="acceptance",
            value=value,
            weight=0.8,
            evidence=evidence
        )
    
    def _detect_fakeout(self, df: pd.DataFrame) -> PrimitiveSignal:
        """
        Detect fake breakouts (break then immediate reversal).
        
        Fakeout pattern:
        1. Break level
        2. Close back inside range within 1-2 candles
        
        Returns:
            PrimitiveSignal with value 0.0 (clean) to 1.0 (fakeout)
        """
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        if len(df) < self.followthrough_candles + 2:
            return PrimitiveSignal(
                name="fakeout",
                value=0.0,
                weight=1.2,  # High weight - fakeouts are critical
                evidence="Insufficient data for fakeout detection"
            )
        
        # Check if previous candle broke level but current closed back
        recent_high = np.max(high[-self.swing_lookback:-self.followthrough_candles])
        recent_low = np.min(low[-self.swing_lookback:-self.followthrough_candles])
        
        # Did we break high but close back below?
        broke_high = high[-self.followthrough_candles] > recent_high
        closed_back_below = close[-1] < recent_high
        
        # Did we break low but close back above?
        broke_low = low[-self.followthrough_candles] < recent_low
        closed_back_above = close[-1] > recent_low
        
        if (broke_high and closed_back_below) or (broke_low and closed_back_above):
            value = 0.9
            evidence = "Fakeout detected - break reversed"
        else:
            value = 0.0
            evidence = "No fakeout pattern"
        
        return PrimitiveSignal(
            name="fakeout",
            value=value,
            weight=1.2,
            evidence=evidence
        )
    
    def _aggregate_structure_state(
        self,
        swing_break: PrimitiveSignal,
        acceptance: PrimitiveSignal,
        fakeout: PrimitiveSignal
    ) -> Tuple[str, float, List[str]]:
        """
        Aggregate primitive signals into final structure state.
        
        Logic:
        - BREAKOUT: Swing break + acceptance + no fakeout
        - FAKEOUT: Swing break + low acceptance OR fakeout detected
        - INTACT: No swing break
        
        Returns:
            (state, confidence, evidence_list)
        """
        evidence = []
        
        # Collect all evidence
        evidence.append(swing_break.evidence)
        evidence.append(acceptance.evidence)
        if fakeout.value > 0:
            evidence.append(fakeout.evidence)
        
        # Determine state
        if fakeout.value > 0.5:
            # Fakeout detected
            state = "fakeout"
            confidence = fakeout.value * 0.9  # High confidence in fakeout
            
        elif abs(swing_break.value) > 0.5:
            # Swing broken
            if acceptance.value > 0.6:
                # Clean breakout with acceptance
                state = "breakout"
                # Confidence = weighted average of signals
                confidence = (
                    swing_break.weight * abs(swing_break.value) +
                    acceptance.weight * acceptance.value
                ) / (swing_break.weight + acceptance.weight)
            else:
                # Break but poor acceptance = potential fakeout
                state = "fakeout"
                confidence = 0.7
                evidence.append("Break without strong acceptance")
        else:
            # No break = structure intact
            state = "intact"
            confidence = 0.8
        
        return state, min(1.0, confidence), evidence
