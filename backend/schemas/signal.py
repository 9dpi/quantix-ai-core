from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

class SignalOutput(BaseModel):
    asset: str
    direction: Literal["BUY", "SELL"]
    timeframe: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(..., alias="ai_confidence")
    data_window: str = Field(default="last_500_candles")
    learning_version: str = Field(default="v0.1.0")
    disclaimer: str = Field(default="Internal research signal. Not financial advice.")
