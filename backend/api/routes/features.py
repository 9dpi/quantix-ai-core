"""
Quantix AI Core - Internal Feature State API
For internal use by decision engine and learning loop
"""

from fastapi import APIRouter, HTTPException, Query
import pandas as pd
from datetime import datetime, timezone
import uuid

from schemas.feature_state import FeatureStateObject, TrendFeatureState, MomentumFeatureState, VolatilityFeatureState
from learning.primitives.structure import StructurePrimitive
from ingestion.yahoo_fetcher import YahooFinanceFetcher
from loguru import logger

router = APIRouter()
fetcher = YahooFinanceFetcher()
structure_calc = StructurePrimitive()


@router.get("/internal/feature-state", response_model=FeatureStateObject)
async def get_feature_state(
    symbol: str = Query(..., description="Asset symbol (e.g., EURUSD)"),
    tf: str = Query("H4", description="Timeframe: H1, H4, D1"),
    period: str = Query("3mo", description="Data period for calculation")
):
    """
    **INTERNAL API** - Get complete feature state for reasoning engine.
    
    Returns state-based features with evidence (NOT raw indicators).
    
    This endpoint is used by:
    - Decision Graph
    - Regime Detector
    - Explainability Engine
    
    Example response:
    ```json
    {
      "trend": {
        "state": "bullish",
        "confidence": 0.84,
        "evidence": ["HH-HL pattern", "EMA slope aligned"]
      },
      "structure": {
        "state": "intact",
        "confidence": 0.81,
        "evidence": ["No close beyond range high", "Strong body acceptance"]
      },
      ...
    }
    ```
    """
    try:
        # Generate trace ID
        trace_id = f"fs-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"[{trace_id}] Calculating feature state for {symbol} {tf}")
        
        # Fetch data
        data_result = fetcher.fetch_daily_ohlcv(symbol, period=period)
        
        if not data_result:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to fetch data for {symbol}"
            )
        
        # Convert to DataFrame
        df = pd.DataFrame(data_result['data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(
                status_code=500,
                detail="Data missing required OHLC columns"
            )
        
        # Calculate STRUCTURE state (most important - done first)
        structure = structure_calc.calculate(df)
        logger.info(f"[{trace_id}] Structure: {structure.state} (conf: {structure.confidence:.2f})")
        
        # TODO: Calculate other states (Sprint 1 continuation)
        # For now, using placeholders with basic logic
        
        # Placeholder TREND (will be replaced with proper primitive)
        trend = TrendFeatureState(
            state="bullish" if df['close'].iloc[-1] > df['close'].iloc[-20] else "bearish",
            confidence=0.7,
            evidence=["Placeholder - awaiting trend primitive implementation"]
        )
        
        # Placeholder MOMENTUM (will be replaced with proper primitive)
        momentum = MomentumFeatureState(
            state="expanding",
            confidence=0.6,
            evidence=["Placeholder - awaiting momentum primitive implementation"]
        )
        
        # Placeholder VOLATILITY (will be replaced with proper primitive)
        volatility = VolatilityFeatureState(
            state="contracting",
            confidence=0.65,
            evidence=["Placeholder - awaiting volatility primitive implementation"]
        )
        
        # Construct complete feature state object
        feature_state = FeatureStateObject(
            trend=trend,
            momentum=momentum,
            volatility=volatility,
            structure=structure,
            timestamp=datetime.now(timezone.utc).isoformat(),
            timeframe=tf,
            symbol=symbol,
            trace_id=trace_id
        )
        
        logger.info(f"[{trace_id}] ✅ Feature state calculated successfully")
        
        return feature_state
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Feature state calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/internal/feature-state/health")
async def internal_health():
    """Health check for internal feature state API"""
    return {
        "status": "ok",
        "service": "feature_state_engine_internal",
        "version": "1.0.0",
        "primitives_implemented": [
            "structure"
        ],
        "primitives_pending": [
            "trend",
            "momentum", 
            "volatility"
        ]
    }
