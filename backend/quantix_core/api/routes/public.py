"""
Quantix Public API - Market State Intelligence
Endpoint: /api/v1/public/market-state
"""

from fastapi import APIRouter, HTTPException, Query, Header, Depends
from quantix_core.config.settings import settings
from quantix_core.engine.structure_engine_v1 import StructureEngineV1
# DISABLED: YahooFinanceFetcher module does not exist - Quantix uses Dukascopy
# from quantix_core.ingestion.yahoo_fetcher import YahooFinanceFetcher
from loguru import logger
import pandas as pd
import uuid
from datetime import datetime

router = APIRouter(prefix="/public", tags=["Public API"])

# Components
structure_engine = StructureEngineV1(sensitivity=2)
# DISABLED: YahooFinanceFetcher not available - Quantix uses Dukascopy
# fetcher = YahooFinanceFetcher()

async def verify_api_key(authorization: str = Header(..., alias="Authorization")):
    """Verify the public API key using Bearer token"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format. Use 'Bearer YOUR_KEY'")
    
    auth_token = authorization.split(" ")[1]
    if auth_token != settings.QUANTIX_PUBLIC_API_KEY:
        logger.warning(f"Invalid API Key attempt: {auth_token}")
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return auth_token

# DISABLED: This endpoint requires YahooFinanceFetcher which is not available
# TODO: Reimplement with Dukascopy fetcher
"""
@router.get("/market-state")
async def get_market_state(
    asset: str = Query(..., description="Asset symbol (e.g., EURUSD)"),
    timeframe: str = Query("H4", description="Timeframe: H1, H4, D1"),
    api_key: str = Depends(verify_api_key)
):
    # ENDPOINT DISABLED - REQUIRES YAHOO FINANCE FETCHER
    pass
"""
