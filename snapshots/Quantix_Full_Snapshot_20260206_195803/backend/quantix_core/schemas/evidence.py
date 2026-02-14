"""
Evidence Schema - Structured evidence for explainability
Frontend can render these without understanding the logic
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class EvidenceItem(BaseModel):
    """
    Structured evidence item that frontend can render.
    
    Principle: Evidence is DATA, not just text.
    Frontend renders based on type, not hardcoded strings.
    """
    type: str = Field(..., description="Evidence type (e.g., 'swing_high_break')")
    description: str = Field(..., description="Human-readable description")
    
    # Optional structured data for rich rendering
    direction: Optional[Literal["up", "down"]] = None
    level: Optional[float] = None
    strength: Optional[Literal["strong", "moderate", "weak"]] = None
    candle_index: Optional[int] = None
    value: Optional[float] = None
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "type": "swing_high_break",
                    "description": "Swing High broken at 1.0942",
                    "direction": "up",
                    "level": 1.0942,
                    "strength": "strong"
                },
                {
                    "type": "acceptance",
                    "description": "Strong body (82%) - price accepted",
                    "candle_index": -1,
                    "value": 0.82
                }
            ]
        }
