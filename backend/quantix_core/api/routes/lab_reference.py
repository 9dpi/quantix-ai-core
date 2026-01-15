"""
Quantix Signal Engine Lab - Market Reference (Experimental)
Endpoint: /api/v1/lab/market-reference
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta, timezone
import pandas as pd

from quantix_core.engine.structure_engine_v1 import StructureEngineV1
from quantix_core.ingestion.dukascopy import DukascopyFetcher, DukascopyFetcherError
from loguru import logger

router = APIRouter(prefix="/lab", tags=["Signal Engine Lab"])

# Components
structure_engine = StructureEngineV1(sensitivity=2)
fetcher = DukascopyFetcher()

def map_trade_bias(state: str, confidence: float):
    """Implementing the official Lab Confidence Mapping Rules"""
    if state == "bullish":
        if confidence >= 0.85: return "BUY", "strong"
        if confidence >= 0.70: return "BUY", "weak"
    elif state == "bearish":
        if confidence >= 0.85: return "SELL", "strong"
        if confidence >= 0.70: return "SELL", "weak"
    
    return "NEUTRAL", "N/A"

@router.get("/market-reference")
async def get_lab_reference(
    symbol: str = Query(..., description="Symbol (e.g., EURUSD)"),
    tf: str = Query("H4", description="Timeframe")
):
    """
    **Signal Engine Lab - Market Reference Snapshot (HOTFIX MODE)**
    
    ⚠️ TEMPORARY: Returns mock snapshot to unblock frontend.
    ⚠️ TODO: Implement proper async engine + snapshot store architecture.
    
    This endpoint should NOT run engine pipeline in HTTP request.
    Proper flow: Async worker → Snapshot store → API reads snapshot.
    """
    logger.info(f"🧪 LAB: Snapshot request for {symbol} @ {tf}")
    
    try:
        # ✅ HOTFIX: Return lightweight mock snapshot
        # This prevents infinite hanging while we build proper architecture
        
        # Mock data based on symbol pattern (deterministic for demo)
        import hashlib
        seed = int(hashlib.md5(f"{symbol}{tf}".encode()).hexdigest()[:8], 16)
        
        # Deterministic mock values
        mock_states = ["BUY", "SELL", "NEUTRAL"]
        mock_strengths = ["strong", "weak", "N/A"]
        
        state_idx = seed % 3
        trade_bias = mock_states[state_idx]
        strength = mock_strengths[state_idx] if state_idx < 2 else "N/A"
        confidence = 0.75 + (seed % 20) / 100  # 0.75 - 0.94
        
        # Mock price levels (realistic for EURUSD range)
        base_price = 1.0850 if "EUR" in symbol else 1.2500
        atr_mock = 0.0015
        
        if trade_bias == "BUY":
            entry_from = base_price - (atr_mock * 0.3)
            entry_to = base_price
            tp = base_price + (atr_mock * 1.5)
            sl = base_price - (atr_mock * 1.1)
        elif trade_bias == "SELL":
            entry_from = base_price
            entry_to = base_price + (atr_mock * 0.3)
            tp = base_price - (atr_mock * 1.5)
            sl = base_price + (atr_mock * 1.1)
        else:
            entry_from = entry_to = tp = sl = base_price
        
        return {
            "asset": f"{symbol[:3]}/{symbol[3:]}",
            "trade_bias": trade_bias,
            "bias_strength": strength,
            "confidence": round(confidence, 4),
            "timeframe": tf,
            "session": "Global → NY Overlap",
            "price_levels": {
                "entry_zone": [round(entry_from, 5), round(entry_to, 5)],
                "take_profit": round(tp, 5),
                "stop_loss": round(sl, 5)
            },
            "trade_details": {
                "target_pips": round(abs(tp - base_price) * 10000, 1),
                "risk_reward": 1.40,
                "suggested_risk_pct": [0.5, 1.0],
                "trade_type": "intraday"
            },
            "expiry": {
                "type": "session",
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat(),
                "rules": [
                    "Valid for current session only",
                    "Expires at New York close",
                    "Invalid if TP or SL is hit",
                    "Do not enter if price breaks entry zone"
                ]
            },
            "meta": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "engine": "Signal Engine Lab (MOCK MODE)",
                "derived_from": "Snapshot placeholder - async engine pending",
                "snapshot": True,
                "hotfix_mode": True
            },
            "disclaimer": "⚠️ DEMO DATA - Market reference only. Not financial advice."
        }
        
    except Exception as e:
        logger.error(f"❌ Lab snapshot failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
