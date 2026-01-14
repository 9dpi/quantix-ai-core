"""
Quantix AI Core - Signal Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from loguru import logger

from config.settings import settings
from schemas.signal import SignalOutput
from database.connection import db

router = APIRouter()

@router.post("/generate", response_model=SignalOutput)
async def generate_signal(asset: str, timeframe: str = "M15"):
    """
    Core Sniper Signal Generation with API Guard
    """
    # 1. API Guard Check
    if settings.QUANTIX_MODE != "INTERNAL":
        logger.warning(f"Blocked signal generation attempt for {asset} - Mode: {settings.QUANTIX_MODE}")
        raise HTTPException(status_code=403, detail="Public signal generation restricted to Internal Alpha Engine.")

    # 2. Logic (Mocked for now, will be replaced by AI Engine in Phase 2)
    logger.info(f"🎯 Generating Internal Sniper Signal for {asset} {timeframe}")
    
    # Internal research signal with mandatory disclaimer
    return SignalOutput(
        asset=asset,
        direction="BUY",
        timeframe=timeframe,
        disclaimer="Internal research signal. Not financial advice."
    )

@router.get("/active", response_model=List[SignalOutput])
async def get_active_signals():
    """
    Fetch all currently active internal signals from Supabase
    """
    try:
        query = "SELECT * FROM fx_signals WHERE status = 'ACTIVE' ORDER BY generated_at DESC"
        results = await db.fetch(query)
        return results
    except Exception as e:
        logger.error(f"Failed to fetch signals: {e}")
        return []
