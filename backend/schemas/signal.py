from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

class SignalOutput(BaseModel):
    asset: str
    direction: Literal["BUY", "SELL"]
    timeframe: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    disclaimer: str = Field(default="Internal research signal. Not financial advice.")
