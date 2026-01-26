"""
Quantix AI Core - Signal Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from loguru import logger

from quantix_core.config.settings import settings
from quantix_core.schemas.signal import SignalOutput
from quantix_core.database.connection import db

from quantix_core.learning.pattern_engine import PatternEngine
from quantix_core.learning.explainability import ExplainabilityEngine

router = APIRouter()
pattern_engine = PatternEngine()
explain_engine = ExplainabilityEngine()

@router.post("/generate", response_model=SignalOutput)
async def generate_signal(asset: str, timeframe: str = "M15"):
    """
    Core Sniper Signal Generation with Dynamic Explainability & Confidence
    """
    # 1. API Guard Check
    if settings.QUANTIX_MODE != "INTERNAL":
        raise HTTPException(status_code=403, detail="Public signal generation restricted to Internal Alpha Engine.")

    # 2. Context Analysis (Simulation for Phase 3.1)
    # In real pipeline, this comes from quantix_core.Ingestion Engine
    context = {
        "session": "LONDON_NY_OVERLAP", 
        "pattern": "PIN_BAR", 
        "regime": "TRENDING_UP", 
        "volatility": "EXPANDING",
        "is_rollover": False
    }
    
    # 3. Fetch Pattern Memory (Mocked for demo until we have real data)
    mock_stats = {
        "win_rate": 0.72,
        "total_signals": 1240,
        "expectancy": 0.45
    }
    
    # 4. Generate Explainability Trace & Dynamic Confidence
    # The Engine now CALCULATES confidence, it doesn't just read it
    trace_result = explain_engine.generate_trace(context, mock_stats)
    final_confidence = trace_result["final_confidence"]
    
    # 5. Signal Construction
    signal_data = {
        "asset": asset,
        "direction": "BUY",
        "timeframe": timeframe,
        "entry_low": 1.08500,
        "entry_high": 1.08520,
        "tp": 1.08750,
        "sl": 1.08400,
        "reward_risk_ratio": 2.5,
        
        # Intelligence Fields
        "ai_confidence": final_confidence,
        "data_window": "last_500_candles",
        "learning_version": "v3.1_explainable",
        
        # Explainability Object (Matches improved schema)
        "explainability": {
            "summary": trace_result["summary"],
            "driving_factors": trace_result["driving_factors"],   # Legacy support
            "risk_factors": trace_result["risk_factors"],         # Legacy support
            "statistical_basis": mock_stats                       # Audit trail
        },
        
        "disclaimer": "Internal research signal. Not financial advice."
    }

    # Task C: Structured Logging for AI Audit
    logger.bind(signal_log=True).info(f"QUANTIX_INTELLIGENCE: {signal_data}")
    
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

@router.get("/latest-lab", response_model=List[SignalOutput])
async def get_latest_lab_signals():
    """
    Fetch the 3 most recent signals (candidates or locked) for the Laboratory
    """
    try:
        # Fetching top 3 regardless of status to show 'latest' activity
        query = "SELECT * FROM fx_signals ORDER BY generated_at DESC LIMIT 3"
        results = await db.fetch(query)
        return results
    except Exception as e:
        logger.error(f"Failed to fetch lab signals: {e}")
        return []
