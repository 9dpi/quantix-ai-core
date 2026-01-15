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
    **Signal Engine Lab - Market Reference Snapshot**
    Deterministic, rule-based reference derived from Structure Engine V1.
    """
    try:
        # 1. Fetch & Analyze
        data_result = fetcher.fetch_ohlcv(symbol, timeframe=tf, period="1mo")
        df = pd.DataFrame(data_result['data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        state = structure_engine.analyze(df, symbol=symbol, timeframe=tf)
        
        # 2. Apply Lab Logic
        trade_bias, strength = map_trade_bias(state.state, state.confidence)
        
        # 3. Derive Price Levels (Rule-based)
        last_close = df['close'].iloc[-1]
        atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]
        
        # Calculation for TP/SL (Reward/Risk focus: 1.4)
        if trade_bias == "BUY":
            entry_from = last_close - (atr * 0.3)
            entry_to = last_close
            tp = last_close + (atr * 1.5)
            sl = last_close - (atr * 1.1)
        elif trade_bias == "SELL":
            entry_from = last_close
            entry_to = last_close + (atr * 0.3)
            tp = last_close - (atr * 1.5)
            sl = last_close + (atr * 1.1)
        else:
            entry_from = entry_to = tp = sl = 0.0

        # 4. Construct Response (Final Schema)
        return {
            "asset": f"{symbol[:3]}/{symbol[3:]}",
            "trade_bias": trade_bias,
            "bias_strength": strength,
            "confidence": round(state.confidence, 4),
            "timeframe": tf,
            "session": "Global → NY Overlap",
            "price_levels": {
                "entry_zone": [round(entry_from, 5), round(entry_to, 5)],
                "take_profit": round(tp, 5),
                "stop_loss": round(sl, 5)
            },
            "trade_details": {
                "target_pips": round(abs(tp - last_close) * 10000, 1) if tp else 0,
                "risk_reward": 1.40 if tp else 0,
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
                "engine": "Signal Engine Lab",
                "derived_from": "Structure Engine v1",
                "snapshot": True
            },
            "disclaimer": "Market reference only — not financial advice."
        }
        
    except Exception as e:
        logger.error(f"❌ Lab Generation Failed: {e}")
        raise HTTPException(status_code=500, detail="Lab engine failure")
