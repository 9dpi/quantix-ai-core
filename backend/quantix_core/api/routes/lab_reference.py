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
    tf: str = Query("H4", description="Timeframe")
):
    """
    **Signal Engine Lab - Market Reference Snapshot**
    
    Implements Official Quantix Confidence Mapping v1.0
    Confidence determines the Trade Action, Structure determines Direction.
    """
    logger.info(f"🧪 LAB: Snapshot request for {symbol} @ {tf}")
    
    # ✅ HOTFIX: Return deterministic mock snapshot based on seed
    # Logic is purely CPU bound (math/random), so running it directly here is fastest & safest.
    # No asyncio wrappers needed.
    
    import hashlib
    import random
    
    # 1. Deterministic Seed via Caching Window
    # We want the signal to be STABLE for the duration of the timeframe
    now = datetime.now(timezone.utc)
    
    # TTL Mapping (Seconds)
    ttl_map = {
        "M15": 900,
        "H1": 3600,
        "H4": 14400,
        "D1": 86400
    }
    ttl = ttl_map.get(tf, 3600) # Default 1h
    
    # Calculate current window start
    window_timestamp = int(now.timestamp()) // ttl
    
    seed_str = f"{symbol}{tf}{window_timestamp}" 
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    random.seed(seed)
    
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
        
    # 4. Mock Price Levels (Only if trade allowed)
    base_price = 1.0850 if "EUR" in symbol else (150.00 if "JPY" in symbol else 1.2500)
    atr_mock = 0.0015 if "JPY" not in symbol else 0.15
    
    levels = {}
    trade_details = {}
    
    if trade_allowed and "BUY" in trade_bias:
        entry = base_price
        tp = base_price + (atr_mock * 2.0)
        sl = base_price - (atr_mock * 1.0)
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
    elif trade_allowed and "SELL" in trade_bias:
        entry = base_price
        tp = base_price - (atr_mock * 2.0)
        sl = base_price + (atr_mock * 1.0)
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
    else:
        levels = {"entry_zone": [0,0], "take_profit": 0, "stop_loss": 0}
        trade_details = {"target_pips": 0, "risk_reward": 0, "type": "N/A"}

    # Calculate Expires At
    next_update_ts = (window_timestamp + 1) * ttl
    expires_at = datetime.fromtimestamp(next_update_ts, tz=timezone.utc)
    
    # 🛡️ HTTP CACHING HEADERS (Crucial for cost control)
    # CDN/Browser will cache this until the next window
    # Max-age is remaining time in current window
    seconds_left = max(0, int(next_update_ts - now.timestamp()))
    response.headers["Cache-Control"] = f"public, max-age={seconds_left}, stale-while-revalidate=60"
    response.headers["X-Quantix-TTL"] = str(seconds_left)
    response.headers["X-Quantix-Next-Update"] = expires_at.isoformat()

    # 5. Construct Response
    return {
        "asset": symbol,
        "trade_bias": trade_bias,         # "STRONG BUY", "WAIT"
        "bias_strength": strength_label,  # "Strong", "Weak Bias"
        "confidence": round(raw_confidence, 2),
        "structure_bias": structure_bias, # "BULLISH", "BEARISH"
        "ui_color": ui_color,
        "timeframe": tf,
        "session": "NY Session",
        "price_levels": levels,
        "trade_details": trade_details,
        "expiry": {
            "expires_at": expires_at.isoformat(),
            "ttl_seconds": seconds_left
        },
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "engine": "Signal Engine Lab (MOCK)",
            "mapping_version": "1.0-official",
            "cache_status": "optimized"
        },
        "disclaimer": "Confidence indicates statistical quality, not profit guarantee."
    }
        
