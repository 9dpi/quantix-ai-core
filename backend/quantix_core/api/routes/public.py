"""
Quantix Public API - Market State Intelligence
Endpoint: /api/v1/public/market-state
"""

from fastapi import APIRouter, HTTPException, Query, Header, Depends
from quantix_core.config.settings import settings
from quantix_core.engine.structure_engine_v1 import StructureEngineV1
from quantix_core.ingestion.yahoo_fetcher import YahooFinanceFetcher
from loguru import logger
import pandas as pd
import uuid
from datetime import datetime

router = APIRouter(prefix="/public", tags=["Public API"])

# Components
structure_engine = StructureEngineV1(sensitivity=2)
fetcher = YahooFinanceFetcher()

async def verify_api_key(authorization: str = Header(..., alias="Authorization")):
    """Verify the public API key using Bearer token"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format. Use 'Bearer YOUR_KEY'")
    
    auth_token = authorization.split(" ")[1]
    if auth_token != settings.QUANTIX_PUBLIC_API_KEY:
        logger.warning(f"Invalid API Key attempt: {auth_token}")
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return auth_token

@router.get("/market-state")
async def get_market_state(
    asset: str = Query(..., description="Asset symbol (e.g., EURUSD)"),
    timeframe: str = Query("H4", description="Timeframe: H1, H4, D1"),
    api_key: str = Depends(verify_api_key)
):
    """
    **Quantix Market State Reasoning API**
    
    Provides deterministic structural analysis, confidence, and evidence.
    This API does NOT provide trading signals or financial advice.
    """
    trace_id = f"pub-{uuid.uuid4().hex[:8]}"
    
    try:
        logger.info(f"[{trace_id}] 🌐 Public state request: {asset} @ {timeframe}")
        
        # 1. Fetch data
        data_result = fetcher.fetch_ohlcv(asset, timeframe=timeframe, period="3mo")
        df = pd.DataFrame(data_result['data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # 2. Analyze structure
        state = structure_engine.analyze(df, symbol=asset, timeframe=timeframe, source="yahoo_finance")
        
        # 3. Formulate response (aligned with Public Positioning)
        return {
            "asset": asset,
            "timeframe": timeframe,
            "state": state.state,
            "confidence": round(state.confidence, 4),
            "dominance": {
                "bullish": round(state.stats.get('bullish_dominance', 0), 2),
                "bearish": round(state.stats.get('bearish_dominance', 0), 2)
            },
            "evidence": list(state.evidence),
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "trace_id": state.trace_id,
            "disclaimer": "Quantix AI provides market structure analysis and research insights only. Not financial advice."
        }
        
    except Exception as e:
        logger.error(f"[{trace_id}] ❌ Public API failed: {e}")
        raise HTTPException(status_code=500, detail="Internal analysis engine error")
