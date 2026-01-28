from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class PriceZone(BaseModel):
    from_price: float = Field(..., alias="from")
    to_price: float = Field(..., alias="to")

    class Config:
        populate_by_name = True

class PriceLevels(BaseModel):
    interest_zone: PriceZone
    structure_target: float
    invalidation_level: float

class Bias(BaseModel):
    direction: str  # bullish, bearish, ranging
    confidence: float

class Meta(BaseModel):
    symbol: str
    timeframe: str
    session: str
    generated_at: datetime
    expires_at: datetime
    engine_version: str

class Metrics(BaseModel):
    projected_move_pips: float
    structure_rr: float
    volatility_context: str

class Validity(BaseModel):
    session_only: bool
    auto_invalidate_on: List[str]

class MarketStructureReference(BaseModel):
    """
    Official Quantix Market Structure Reference Schema.
    Strictly educational/analytical. No BUY/SELL keywords.
    """
    meta: Meta
    bias: Bias
    price_levels: PriceLevels
    metrics: Metrics
    validity: Validity
    disclaimer_level: str = "public_reference"
