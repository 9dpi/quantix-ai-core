"""
Quantix Lab API - Isolated Decision Support
Namespace: /api/v1/lab
"""

from fastapi import APIRouter, HTTPException, Query, Body
from quantix_core.config.settings import settings
from quantix_core.engine.structure_engine_v1 import StructureEngineV1
from quantix_core.learning_lab.advisor import LabAdvisor
# DISABLED: YahooFinanceFetcher module does not exist - Quantix uses Dukascopy
# from quantix_core.ingestion.yahoo_fetcher import YahooFinanceFetcher
from loguru import logger
import pandas as pd
import uuid
import random
from datetime import datetime, timedelta

router = APIRouter()

# Components (Isolated from main routes)
structure_engine = StructureEngineV1(sensitivity=2)
# DISABLED: YahooFinanceFetcher not available - Quantix uses Dukascopy
# fetcher = YahooFinanceFetcher()
lab_advisor = LabAdvisor()

# DISABLED: These endpoints require YahooFinanceFetcher which is not available
# TODO: Reimplement with Dukascopy fetcher
"""
@router.post("/signal-engine/evaluate")
async def evaluate_user_rules(payload: dict = Body(...)):
    # ENDPOINT DISABLED - REQUIRES YAHOO FINANCE FETCHER
    pass

@router.get("/signal-candidate")
async def get_signal_candidate(
    symbol: str = Query(..., description="Symbol (e.g., EURUSD)"),
    tf: str = Query("H4", description="Timeframe: H1, H4, D1")
):
    # ENDPOINT DISABLED - REQUIRES YAHOO FINANCE FETCHER
    pass
"""
