"""
Quantix AI Core - Signal Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from loguru import logger

from config.settings import settings
from schemas.signal import SignalOutput
from database.connection import db

from learning.pattern_engine import PatternEngine

router = APIRouter()
pattern_engine = PatternEngine()

@router.post("/generate", response_model=SignalOutput)
async def generate_signal(asset: str, timeframe: str = "M15"):
    """
    Core Sniper Signal Generation with Bayesian Outcome Feedback
    """
    # 1. API Guard Check
    if settings.QUANTIX_MODE != "INTERNAL":
        logger.warning(f"Blocked signal generation attempt for {asset} - Mode: {settings.QUANTIX_MODE}")
        raise HTTPException(status_code=403, detail="Public signal generation restricted to Internal Alpha Engine.")

    # 2. Pattern Analysis (Logic will be expanded in ML Phase)
    context = {
        "session": "LONDON", 
        "pattern": "PIN_BAR", 
        "regime": "TRENDING_UP", 
        "volatility": "NORMAL"
    }
    p_hash = pattern_engine.generate_hash(context)
    
    # 3. Generate Bayesian Confidence
    confidence = await pattern_engine.generate_confidence(p_hash)
    
    # 4. Signal Construction
    signal_data = {
        "asset": asset,
        "direction": "BUY",
        "timeframe": timeframe,
        "entry_low": 1.08500,
        "entry_high": 1.08520,
        "tp": 1.08750,
        "sl": 1.08400,
        "reward_risk_ratio": 2.5,
        "ai_confidence": confidence,
        "pattern_hash": p_hash,
        "data_window": "last_500_candles",
        "learning_version": "v1.5_loop",
        "disclaimer": "Internal research signal. Not financial advice."
    }

    # Task C: Structured Logging for AI Explainability & Memory
    logger.bind(signal_log=True).info(f"QUANTIX_SIGNAL_REGISTRY: {signal_data}")
    
    return SignalOutput(**signal_data)

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
