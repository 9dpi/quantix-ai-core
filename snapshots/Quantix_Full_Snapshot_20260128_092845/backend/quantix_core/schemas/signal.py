from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class SignalContext(BaseModel):
    session: str
    pattern: str # e.g. "PIN_BAR", "ENGULFING"
    regime: str  # e.g. "TRENDING_UP", "RANGING"
    volatility: str # "HIGH", "NORMAL", "LOW"

class ExplainabilityTrace(BaseModel):
    summary: str # Human readable summary e.g. "High confidence breakout in London Session"
    driving_factors: List[str] # ["Winrate > 70%", "Session Overlap", "Pattern Match"]
    statistical_basis: Dict[str, Any] # {"historical_winrate": 0.71, "sample_size": 183}
    risk_factors: List[str] # ["Near Resistance", "Low Volatility"]

class SignalOutput(BaseModel):
    id: Optional[str] = None
    asset: str
    direction: str
    timeframe: str
    
    # Entry Zone
    entry_low: float
    entry_high: float
    tp: float
    sl: float
    reward_risk_ratio: Optional[float] = 2.0
    
    # AI Intelligence
    confidence: float = Field(..., alias="ai_confidence")
    strategy: Optional[str] = Field(default="Quantix Alpha", alias="learning_version")
    status: Optional[str] = "CANDIDATE"
    
    # Expiry
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    disclaimer: str = Field(default="Internal research signal. Not financial advice.")

    class Config:
        populate_by_name = True
        extra = "ignore"

class TradeOutcome(BaseModel):
    signal_id: str
    outcome: Literal["HIT_TP", "HIT_SL", "EXPIRED"]
    r_multiple: float
    duration_minutes: int
    resolved_at: datetime = Field(default_factory=datetime.utcnow)
