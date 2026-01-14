from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class SignalContext(BaseModel):
    session: str
    pattern: str # e.g. "PIN_BAR", "ENGULFING"
    regime: str  # e.g. "TRENDING_UP", "RANGING"
    volatility: str # "HIGH", "NORMAL", "LOW"

class SignalOutput(BaseModel):
    id: Optional[str] = None
    asset: str
    direction: Literal["BUY", "SELL"]
    timeframe: str
    
    # Entry Zone
    entry_low: Decimal
    entry_high: Decimal
    tp: Decimal
    sl: Decimal
    reward_risk_ratio: Decimal
    
    # AI Intelligence
    confidence: float = Field(..., alias="ai_confidence")
    data_window: str = Field(default="last_500_candles")
    learning_version: str = Field(default="v1.0.0_outcome")
    
    # Structural Context
    context: Optional[SignalContext] = None
    pattern_hash: Optional[str] = None
    
    # Expiry
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    disclaimer: str = Field(default="Internal research signal. Not financial advice.")

class TradeOutcome(BaseModel):
    signal_id: str
    outcome: Literal["HIT_TP", "HIT_SL", "EXPIRED"]
    r_multiple: float
    duration_minutes: int
    resolved_at: datetime = Field(default_factory=datetime.utcnow)
