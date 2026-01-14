"""
Quantix Lab API - Isolated Decision Support
Namespace: /api/v1/lab
"""

from fastapi import APIRouter, HTTPException, Query
from config.settings import settings
from engine.structure_engine_v1 import StructureEngineV1
from learning_lab.advisor import LabAdvisor
from ingestion.yahoo_fetcher import YahooFinanceFetcher
from loguru import logger
import pandas as pd
import uuid

router = APIRouter()

# Components (Isolated from main routes)
structure_engine = StructureEngineV1(sensitivity=2)
fetcher = YahooFinanceFetcher()
lab_advisor = LabAdvisor()

@router.get("/signal-candidate")
async def get_signal_candidate(
    symbol: str = Query(..., description="Symbol (e.g., EURUSD)"),
    tf: str = Query("H4", description="Timeframe: H1, H4, D1")
):
    """
    **LAB ONLY** - Get Buy/Sell candidates based on structural evidence.
    
    This endpoint is subject to the Kill Switch: LAB_SIGNALS_ENABLED.
    """
    if not settings.ENABLE_LAB_SIGNALS:
        raise HTTPException(
            status_code=403,
            detail="Learning Lab signals are currently disabled (Kill Switch active)."
        )

    trace_id = f"lab-{uuid.uuid4().hex[:8]}"
    
    try:
        logger.info(f"[{trace_id}] 🧪 Lab analysis request: {symbol} @ {tf}")
        
        # 1. Fetch Data (Internal utility)
        data_result = fetcher.fetch_ohlcv(symbol, timeframe=tf, period="3mo")
        df = pd.DataFrame(data_result['data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # 2. Run Structure Engine (Read-only)
        state = structure_engine.analyze(df, symbol=symbol, timeframe=tf, source="yahoo_finance")
        
        # 3. Create a snapshot mock from state for the advisor
        # (In prod this would pull from analytics_snapshots_v1)
        snapshot = {
            "snapshot_id": f"lab-snap-{trace_id}",
            "asset": symbol,
            "timeframe": tf,
            "structure_state": state.state,
            "confidence": state.confidence,
            "dominance": state.dominance_ratio,
            "persistence": 2, # Mocked
            "evidence": {
                "fake_breakout": False # Mocked
            }
        }
        
        # 4. Map to Decision using LabAdvisor
        decision = lab_advisor.advise(snapshot)
        
        # 5. Clean Output for API
        return {
            "decision": decision["classification"],
            "confidence": decision["confidence"],
            "valid_for": decision["expires_in"],
            "lab_only": True,
            "explain": [
                f"Market structure is {state.state.upper()}",
                f"Confidence level: {state.confidence * 100:.1f}%",
                f"Dominance ratio: {state.dominance_ratio:.2f}"
            ] + list(state.evidence),
            "disclaimer": "Not a trading signal. Research output only."
        }
        
    except Exception as e:
        logger.error(f"[{trace_id}] ❌ Lab analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
