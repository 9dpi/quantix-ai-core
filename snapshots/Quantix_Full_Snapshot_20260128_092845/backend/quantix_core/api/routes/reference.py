"""
Quantix Public API - Market Structure Reference
Endpoint: /api/v1/public/market-reference
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta, timezone
import uuid
import pandas as pd

from quantix_core.schemas.reference import MarketStructureReference, Meta, Bias, PriceLevels, PriceZone, Metrics, Validity
from quantix_core.engine.structure_engine_v1 import StructureEngineV1
from quantix_core.ingestion.dukascopy import DukascopyFetcher, DukascopyFetcherError
from loguru import logger

router = APIRouter(prefix="/public", tags=["Public API"])

# Components
structure_engine = StructureEngineV1(sensitivity=2)
fetcher = DukascopyFetcher()

@router.get("/market-reference", response_model=MarketStructureReference)
async def get_market_reference(
    symbol: str = Query(..., description="Symbol (e.g., EURUSD)"),
    tf: str = Query("H4", description="Timeframe: H1, H4, D1")
):
    """
    **Quantix AI - Market Structure Reference API**
    
    Returns a high-confidence structural bias and key interest zones.
    This is NOT a trading signal. Disclaimer level: public_reference.
    """
    try:
        # 1. Fetch Data
        data_result = fetcher.fetch_ohlcv(symbol, timeframe=tf, period="1mo")
        df = pd.DataFrame(data_result['data'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        
        # 2. Analyze using Engine
        state = structure_engine.analyze(df, symbol=symbol, timeframe=tf, source="dukascopy")
        
        # 3. TRANSFORM LAYER (Semantic Adapter)
        # In a real scenario, these levels would come from the engine's internal zone detection
        # For V1, we derive them from recent high/lows and structural points
        last_close = df['close'].iloc[-1]
        atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]
        
        # Mocking semantic logic for V1 zones based on bias
        if state.state == "bullish":
            zone_from = last_close - (atr * 0.5)
            zone_to = last_close - (atr * 0.2)
            target = last_close + (atr * 1.5)
            invalidation = last_close - (atr * 1.2)
        else:
            zone_from = last_close + (atr * 0.2)
            zone_to = last_close + (atr * 0.5)
            target = last_close - (atr * 1.5)
            invalidation = last_close + (atr * 1.2)

        # 4. Build Meta
        meta = Meta(
            symbol=symbol,
            timeframe=tf,
            session="Global-UTC",
            generated_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
            engine_version="structure_engine_v1"
        )
        
        # 5. Build Reference Object
        reference = MarketStructureReference(
            meta=meta,
            bias=Bias(
                direction=state.state,
                confidence=round(state.confidence, 4)
            ),
            price_levels=PriceLevels(
                interest_zone=PriceZone(**{"from": round(zone_from, 5), "to": round(zone_to, 5)}),
                structure_target=round(target, 5),
                invalidation_level=round(invalidation, 5)
            ),
            metrics=Metrics(
                projected_move_pips=round(abs(target - last_close) * 10000, 1),
                structure_rr=1.4,
                volatility_context="intraday"
            ),
            validity=Validity(
                session_only=True,
                auto_invalidate_on=["target_reached", "invalidation_breached", "session_closed"]
            )
        )
        
        return reference
        
    except DukascopyFetcherError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"❌ Reference Generation Failed: {e}")
        raise HTTPException(status_code=500, detail="Intelligence engine failure")
