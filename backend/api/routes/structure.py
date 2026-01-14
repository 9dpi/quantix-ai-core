"""
Structure Feature State API - Market State Reasoning Endpoint
Exposes Structure Engine v1 reasoning capabilities

This is NOT indicator spam - this is STATE REASONING
"""

from fastapi import APIRouter, HTTPException, Query
import pandas as pd
from datetime import datetime
import uuid

from learning.structure_engine_v1 import StructureEngineV1
from ingestion.yahoo_fetcher import YahooFinanceFetcher
from ingestion.data_validator import DataValidator, DataNotSufficientError
from loguru import logger

router = APIRouter()

# Initialize components
structure_engine = StructureEngineV1(sensitivity=2)  # H4 optimal
fetcher = YahooFinanceFetcher()
validator = DataValidator


@router.get("/internal/feature-state/structure")
async def get_structure_state(
    symbol: str = Query(..., description="Symbol (e.g., EURUSD)"),
    tf: str = Query("H4", description="Timeframe: H1, H4, D1"),
    period: str = Query("3mo", description="Data period for analysis")
):
    """
    **INTERNAL API** - Get market structure state with reasoning.
    
    This endpoint returns INTERPRETED STATE, not raw indicators.
    
    Response format:
    ```json
    {
      "feature": "structure",
      "state": "bullish",
      "confidence": 0.78,
      "dominance": {
        "bullish": 1.42,
        "bearish": 0.31
      },
      "evidence": [
        "Bullish BOS confirmed (body 82%, close accepted)",
        "No fakeout after swing break"
      ],
      "trace_id": "struct-9e21c",
      "source": "yahoo_finance",
      "timeframe": "H4"
    }
    ```
    
    Frontend displays:
    - Market is in X state
    - Because of Y evidence
    - With Z confidence
    
    NOT "Buy/Sell" - this is STATE REASONING.
    """
    trace_id = f"api-{uuid.uuid4().hex[:8]}"
    
    try:
        logger.info(f"[{trace_id}] 📊 Structure analysis request: {symbol} @ {tf}")
        
        # Fetch data
        try:
            data_result = fetcher.fetch_ohlcv(symbol, timeframe=tf, period=period)
        except Exception as fetch_error:
            if hasattr(fetch_error, 'error_code'):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": fetch_error.error_code,
                        "symbol": symbol,
                        "timeframe": tf,
                        "details": fetch_error.details,
                        "trace_id": trace_id
                    }
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Data fetch failed: {str(fetch_error)}"
                )
        
        # Convert to DataFrame
        df = pd.DataFrame(data_result['data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # Validate data sufficiency
        try:
            validator.validate_candle_count(len(df), tf, symbol)
            logger.info(f"[{trace_id}] ✅ Data validation passed: {len(df)} candles")
        except DataNotSufficientError as e:
            logger.warning(f"[{trace_id}] ⚠️ Insufficient data: {e}")
            raise HTTPException(
                status_code=400,
                detail={
                    **e.to_dict(),
                    "trace_id": trace_id,
                    "data_status": {
                        "provider": "Yahoo Finance",
                        "raw_candles": len(data_result['data']),
                        "aggregated_candles": len(df),
                        "status": "insufficient"
                    }
                }
            )
        
        # Ensure required columns
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(
                status_code=500,
                detail="Data missing required OHLC columns"
            )
        
        # Run Structure Engine v1
        logger.info(f"[{trace_id}] 🏗️ Running Structure Engine v1...")
        
        state = structure_engine.analyze(
            df=df,
            symbol=symbol,
            timeframe=tf,
            source="yahoo_finance"
        )
        
        # Convert to API format
        response = structure_engine.to_api_response(state)
        
        logger.info(
            f"[{trace_id}] ✅ Structure analysis complete: "
            f"{state.state} (confidence: {state.confidence:.2f})"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{trace_id}] ❌ Structure analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ANALYSIS_FAILED",
                "message": str(e),
                "trace_id": trace_id
            }
        )


@router.get("/internal/feature-state/structure/health")
async def structure_health():
    """
    Health check for Structure Engine v1.
    """
    return {
        "status": "ok",
        "engine": "structure_v1",
        "version": "1.0.0",
        "capabilities": [
            "swing_detection",
            "bos_choch_detection",
            "fake_breakout_filtering",
            "evidence_scoring",
            "state_resolution"
        ],
        "reasoning_type": "deterministic",
        "ml_used": False
    }
