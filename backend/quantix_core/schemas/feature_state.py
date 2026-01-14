"""
Quantix AI Core - Feature State Schema v1 (FROZEN)
Market State Reasoning Engine - State > Value

This schema is FROZEN for v1. Do not modify without version bump.
"""

from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime


# ============================================================================
# STATE ENUMS - FROZEN v1
# ============================================================================

# Trend States
TrendState = Literal["bullish", "bearish", "range"]

# Momentum States  
MomentumState = Literal["expanding", "weakening", "neutral"]

# Volatility States
VolatilityState = Literal["expanding", "contracting", "abnormal"]

# Structure States (MOST IMPORTANT)
StructureState = Literal["breakout", "fakeout", "intact"]


# ============================================================================
# FEATURE STATE MODELS (WITH EVIDENCE)
# ============================================================================

class FeatureState(BaseModel):
    """
    Base feature state with MANDATORY evidence array.
    Evidence is the foundation of explainability.
    """
    state: str = Field(..., description="The current state")
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence = consistency of evidence (NOT probability)"
    )
    evidence: List[str] = Field(
        ...,
        min_items=1,
        description="Evidence supporting this state (MANDATORY for explainability)"
    )


class TrendFeatureState(FeatureState):
    """Trend state with evidence"""
    state: TrendState


class MomentumFeatureState(FeatureState):
    """Momentum state with evidence"""
    state: MomentumState


class VolatilityFeatureState(FeatureState):
    """Volatility state with evidence"""
    state: VolatilityState


class StructureFeatureState(FeatureState):
    """Structure state with evidence (MOST IMPORTANT)"""
    state: StructureState


# ============================================================================
# COMPLETE FEATURE STATE OBJECT (v1 FROZEN)
# ============================================================================

class FeatureStateObject(BaseModel):
    """
    Complete feature state representation.
    This is what Quantix AI uses for reasoning.
    
    FROZEN v1 - Do not modify without version bump.
    """
    
    # Core states (all mandatory)
    trend: TrendFeatureState
    momentum: MomentumFeatureState
    volatility: VolatilityFeatureState
    structure: StructureFeatureState
    
    # Metadata
    timestamp: str = Field(..., description="State snapshot timestamp (ISO 8601)")
    timeframe: str = Field(..., description="Timeframe (H1, H4, D1)")
    symbol: str = Field(..., description="Asset symbol")
    trace_id: str = Field(..., description="Trace ID for debugging/logging")
    
    class Config:
        schema_extra = {
            "example": {
                "trend": {
                    "state": "bullish",
                    "confidence": 0.84,
                    "evidence": ["HH-HL pattern", "EMA slope aligned", "D1 confirms"]
                },
                "momentum": {
                    "state": "expanding",
                    "confidence": 0.76,
                    "evidence": ["ROC acceleration", "Strong body candles"]
                },
                "volatility": {
                    "state": "contracting",
                    "confidence": 0.68,
                    "evidence": ["ATR percentile < 30"]
                },
                "structure": {
                    "state": "intact",
                    "confidence": 0.81,
                    "evidence": ["No close beyond range high"]
                },
                "timestamp": "2026-01-14T00:00:00Z",
                "timeframe": "H4",
                "symbol": "EURUSD",
                "trace_id": "fs-92ad"
            }
        }


# ============================================================================
# PRIMITIVE SIGNAL RESULT (Internal Use)
# ============================================================================

class PrimitiveSignal(BaseModel):
    """
    Result from a primitive signal calculation.
    Used internally by state aggregator.
    """
    name: str = Field(..., description="Signal name (e.g., 'HH-HL pattern')")
    value: float = Field(..., description="Signal value (normalized 0-1 or -1 to 1)")
    weight: float = Field(default=1.0, description="Signal weight in aggregation")
    evidence: str = Field(..., description="Human-readable evidence string")
