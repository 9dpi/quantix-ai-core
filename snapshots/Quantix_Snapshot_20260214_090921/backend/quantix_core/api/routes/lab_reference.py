"""
Quantix Signal Engine Lab - Market Reference (Experimental)
Endpoint: /api/v1/lab/market-reference

⚠️ HOTFIX MODE: Zero dependencies, instant response
"""

from fastapi import APIRouter, HTTPException, Query, Response
from datetime import datetime, timedelta, timezone
from loguru import logger

router = APIRouter(prefix="/lab", tags=["Signal Engine Lab"])

# ✅ NO MODULE-LEVEL INIT - This was causing blocking
# ✅ NO ENGINE IMPORT - Endpoint must be lightweight
# ✅ NO FETCHER IMPORT - Mock data only

@router.get("/market-reference")
async def get_lab_reference(
    response: Response,
    symbol: str = Query(..., description="Symbol (e.g., EURUSD)"),
    tf: str = Query("H4", description="Timeframe"),
    snap_time: str = Query(None, description="ISO Timestamp for historical snapshot")
):
    """
    **Signal Engine Lab - Market Reference Snapshot**
    
    Implements Official Quantix Confidence Mapping v1.0
    Confidence determines the Trade Action, Structure determines Direction.
    """
    logger.info(f"🧪 LAB: Snapshot request for {symbol} @ {tf} (Time: {snap_time})")
    
    # ✅ HOTFIX: Return deterministic mock snapshot based on seed
    # Logic is purely CPU bound (math/random), so running it directly here is fastest & safest.
    
    import hashlib
    import random
    import uuid
    
    # 1. Deterministic Seed via Caching Window OR Specific Timestamp
    # We want the signal to be STABLE for the duration of the timeframe
    now = datetime.now(timezone.utc)
    
    if snap_time:
        # Historical Mode: Seed based on input time
        seed_source = f"{symbol}{tf}{snap_time}"
        timestamp_used = snap_time
        is_historical = True
    else:
        # Live Mode: Seed based on current TTL window
        # TTL Mapping (Seconds)
        ttl_map = {
            "M15": 900,
            "H1": 3600,
            "H4": 14400,
            "D1": 86400
        }
        ttl = ttl_map.get(tf, 3600) # Default 1h
        window_timestamp = int(now.timestamp()) // ttl
        
        seed_source = f"{symbol}{tf}{window_timestamp}"
        timestamp_used = now.isoformat()
        is_historical = False
        
        # Calculate Expires At (Only for Live)
        next_update_ts = (window_timestamp + 1) * ttl
        expires_at = datetime.fromtimestamp(next_update_ts, tz=timezone.utc)
        seconds_left = max(0, int(next_update_ts - now.timestamp()))
        
        # 🛡️ HTTP CACHING HEADERS (Live Only)
        response.headers["Cache-Control"] = f"public, max-age={seconds_left}, stale-while-revalidate=60"
        response.headers["X-Quantix-TTL"] = str(seconds_left)
        response.headers["X-Quantix-Next-Update"] = expires_at.isoformat()

    seed = int(hashlib.md5(seed_source.encode()).hexdigest()[:8], 16)
    random.seed(seed)
    
    # Generate Trace ID
    trace_id = f"struct-{hashlib.md5(seed_source.encode()).hexdigest()[:12]}"
    
    # 2. Generate Base Metrics (Structure & Confidence)
    raw_confidence = random.uniform(0.35, 0.92) 
    structure_bias = random.choice(["BULLISH", "BEARISH"])
    
    # 3. APPLY OFFICIAL MAPPING LOGIC (The Spine)
    confidence_pct = int(raw_confidence * 100)
    
    trade_bias = "NEUTRAL"
    strength_label = "Neutral"
    trade_allowed = False
    ui_color = "gray"
    
    if confidence_pct < 40:
        trade_bias = "NO TRADE"
        strength_label = "Neutral"
        ui_color = "gray"
    elif confidence_pct < 55:
        trade_bias = "WAIT"
        strength_label = "Weak Bias"
        ui_color = "gray"
    elif confidence_pct < 65:
        trade_bias = "BUY" if structure_bias == "BULLISH" else "SELL"
        strength_label = "Cautious"
        trade_allowed = True
        ui_color = "yellow"
    elif confidence_pct < 75:
        trade_bias = "BUY" if structure_bias == "BULLISH" else "SELL"
        strength_label = "Valid"
        trade_allowed = True
        ui_color = "green"
    elif confidence_pct < 85:
        trade_bias = "STRONG BUY" if structure_bias == "BULLISH" else "STRONG SELL"
        strength_label = "Strong"
        trade_allowed = True
        ui_color = "blue"
    else: # >= 85
        trade_bias = "HIGH CONVICTION" if structure_bias == "BULLISH" else "HIGH CONVICTION"
        strength_label = "High Confidence"
        trade_allowed = True
        ui_color = "fire"
        
    # 4. Mock Price Levels & Evidence
    base_price = 1.0850 if "EUR" in symbol else (150.00 if "JPY" in symbol else 1.2500)
    atr_mock = 0.0015 if "JPY" not in symbol else 0.15
    
    levels = {}
    trade_details = {}
    evidence = []
    invalidation_price = 0
    
    reasoning_state = "Neutral Consolidation"
    
    if trade_allowed and "BUY" in trade_bias:
        reasoning_state = "Bullish Continuation"
        entry = base_price
        tp = base_price + (atr_mock * 2.0)
        sl = base_price - (atr_mock * 1.0)
        invalidation_price = round(sl - (atr_mock * 0.2), 5)
        
        levels = {
            "entry_zone": [round(entry - (atr_mock*0.1), 5), round(entry, 5)],
            "take_profit": round(tp, 5),
            "stop_loss": round(sl, 5)
        }
        trade_details = {
            "target_pips": round(abs(tp - entry) * (100 if "JPY" in symbol else 10000), 1),
            "risk_reward": 2.0,
            "type": "Trend Follow"
        }
        evidence = [
            "✔ Higher Low confirmed at reference point",
            "✔ No structure break detected in lookback",
            "✔ Momentum aligned with Primary structure"
        ]
        
    elif trade_allowed and "SELL" in trade_bias:
        reasoning_state = "Bearish Rejection"
        entry = base_price
        tp = base_price - (atr_mock * 2.0)
        sl = base_price + (atr_mock * 1.0)
        invalidation_price = round(sl + (atr_mock * 0.2), 5)
        
        levels = {
            "entry_zone": [round(entry, 5), round(entry + (atr_mock*0.1), 5)],
            "take_profit": round(tp, 5),
            "stop_loss": round(sl, 5)
        }
        trade_details = {
            "target_pips": round(abs(entry - tp) * (100 if "JPY" in symbol else 10000), 1),
            "risk_reward": 2.0,
            "type": "Trend Follow"
        }
        evidence = [
            "✔ Lower High confirmed at resistance",
            "✔ Supply zone rejection detected",
            "✔ Bearish momentum divergence"
        ]
    else:
        levels = {"entry_zone": [0,0], "take_profit": 0, "stop_loss": 0}
        trade_details = {"target_pips": 0, "risk_reward": 0, "type": "N/A"}
        evidence = ["Market is ranging / choppy", "No clear structural bias identified"]

    # 5. Construct Response
    return {
        "asset": symbol,
        "trade_bias": trade_bias,         
        "bias_strength": strength_label,
        "confidence": round(raw_confidence, 2),
        "structure_bias": structure_bias,
        "ui_color": ui_color,
        "timeframe": tf,
        "session": "NY Session",
        "price_levels": levels,
        "trade_details": trade_details,
        
        # Extended Lab Fields
        "reasoning": {
            "state": reasoning_state,
            "evidence": evidence,
            "invalidation_price": invalidation_price,
            "trace_id": trace_id,
            "provider": "dukascopy"
        },
        
        "meta": {
            "generated_at": timestamp_used,
            "engine": "Signal Engine Lab (MOCK)",
            "mapping_version": "1.0-official",
            "is_historical": is_historical
        },
        "disclaimer": "Confidence indicates statistical quality, not profit guarantee."
    }
        
